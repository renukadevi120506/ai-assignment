import os

import numpy as np


class EmbeddingService:
    def __init__(self):
        self._model = None
        self._fastembed_available = None

    def _init_model(self):
        if self._fastembed_available is False:
            return
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                self._fastembed_available = True
            except Exception:
                self._fastembed_available = False

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        self._init_model()
        if self._fastembed_available and self._model:
            try:
                embeddings = list(self._model.embed(texts))
                return [emb.tolist() for emb in embeddings]
            except Exception:
                pass

        # Fallback to Gemini Embeddings if available
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                res = []
                for t in texts:
                    emb_resp = client.models.embed_content(
                        model="text-embedding-004",
                        contents=t
                    )
                    res.append(list(emb_resp.embedding.values))
                return res
            except Exception:
                pass

        # Final resilient local fallback (frequency / hash embedding, 384 dimensions)
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * 384

    def _fallback_embed(self, text: str, dim: int = 384) -> list[float]:
        """Deterministic hash-based pseudo-embedding for zero-dependency offline environments."""
        vec = np.zeros(dim, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            return vec.tolist()
        for token in tokens:
            idx = abs(hash(token)) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
