import os
import re
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.ai.embedding_service import EmbeddingService


class RAGService:
    def __init__(self, collection_name: str = "educational_documents"):
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService()
        self._client = None
        self.vector_dim = 384  # Default for BGE-small / fallback

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            qdrant_url = os.environ.get("QDRANT_URL", "")
            qdrant_api_key = os.environ.get("QDRANT_API_KEY", None)

            if qdrant_url:
                self._client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            else:
                # Local in-memory or filesystem storage
                storage_path = os.environ.get("QDRANT_STORAGE_PATH", ":memory:")
                self._client = QdrantClient(location=storage_path)

            self._ensure_collection()
        return self._client

    def _ensure_collection(self):
        try:
            collections = self._client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"[RAGService] Notice during collection check: {e}")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> list[str]:
        """Split text into coherent paragraph-aware chunks."""
        if not text or not text.strip():
            return []
        
        paragraphs = [p.strip() for p in re.split(r"\n+", text.strip()) if p.strip()]
        chunks = []
        current = ""

        for p in paragraphs:
            if len(current) + len(p) + 1 <= chunk_size:
                current = f"{current}\n{p}" if current else p
            else:
                if current:
                    chunks.append(current)
                # If paragraph itself is longer than chunk_size, split by sentences
                if len(p) > chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', p)
                    sub = ""
                    for s in sentences:
                        if len(sub) + len(s) + 1 <= chunk_size:
                            sub = f"{sub} {s}" if sub else s
                        else:
                            if sub:
                                chunks.append(sub)
                            sub = s
                    if sub:
                        current = sub
                    else:
                        current = ""
                else:
                    current = p

        if current:
            chunks.append(current)
        return chunks

    def index_document(self, teacher_id: str, document_id: str, filename: str, text: str) -> int:
        """Splits document text, computes embeddings, and stores in Qdrant with teacher isolation metadata."""
        chunks = self.chunk_text(text)
        if not chunks:
            return 0

        client = self._get_client()
        embeddings = self.embedding_service.embed_texts(chunks)

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{i}"))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "teacher_id": teacher_id,
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": i,
                        "text": chunk
                    }
                )
            )

        client.upsert(collection_name=self.collection_name, points=points)
        return len(chunks)

    def search_relevant_passages(
        self,
        query: str,
        teacher_id: str | None = None,
        document_id: str | None = None,
        top_k: int = 3
    ) -> list[dict[str, Any]]:
        """Retrieve relevant context chunks with metadata filtering for authorization."""
        if not query or not query.strip():
            return []

        try:
            client = self._get_client()
            query_vector = self.embedding_service.embed_query(query)

            # Metadata filter construction
            must_filters = []
            if teacher_id:
                must_filters.append(
                    qmodels.FieldCondition(key="teacher_id", match=qmodels.MatchValue(value=teacher_id))
                )
            if document_id:
                must_filters.append(
                    qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))
                )

            query_filter = qmodels.Filter(must=must_filters) if must_filters else None

            # Support both qdrant-client search and query_points
            if hasattr(client, "query_points"):
                response = client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
                points = response.points
            else:
                points = client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )

            results = []
            for hit in points:
                payload = hit.payload or {}
                results.append({
                    "id": hit.id,
                    "score": round(float(hit.score), 4) if hasattr(hit, "score") and hit.score is not None else 0.0,
                    "text": payload.get("text", ""),
                    "filename": payload.get("filename", ""),
                    "document_id": payload.get("document_id", "")
                })
            return results
        except Exception as e:
            print(f"[RAGService] Search error: {e}")
            return []

    def delete_document_points(self, document_id: str):
        """Remove indexed points for a deleted document."""
        try:
            client = self._get_client()
            client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))]
                    )
                )
            )
        except Exception as e:
            print(f"[RAGService] Delete points error: {e}")
