import os
import re

import docx
try:
    import pymupdf as fitz
except ImportError:
    import fitz
from werkzeug.utils import secure_filename

from app.ai.rag_service import RAGService
from app.database import db
from app.models.submission import Document


class DocumentService:
    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize whitespace, remove non-printable characters, clean text."""
        if not text:
            return ""
        # Replace non-breaking spaces and unusual whitespace
        text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
        # Remove repeated empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def extract_text_from_file(cls, file_path: str, file_type: str) -> str:
        file_type = file_type.lower()
        extracted = ""
        
        if file_type == "pdf":
            doc = fitz.open(file_path)
            pages = []
            for page in doc:
                pages.append(page.get_text())
            doc.close()
            extracted = "\n".join(pages)

        elif file_type == "docx":
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            extracted = "\n".join(paragraphs)

        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted = f.read()

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return cls.clean_text(extracted)

    @classmethod
    def process_and_save_document(
        cls,
        teacher_id: str,
        uploaded_file,
        upload_folder: str
    ) -> Document:
        filename = secure_filename(uploaded_file.filename)
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        
        os.makedirs(upload_folder, exist_ok=True)
        unique_filename = f"{teacher_id}_{os.urandom(4).hex()}_{filename}"
        save_path = os.path.join(upload_folder, unique_filename)
        uploaded_file.save(save_path)

        file_size = os.path.getsize(save_path)
        extracted_text = cls.extract_text_from_file(save_path, file_ext)

        # Create database record
        doc_record = Document(
            teacher_id=teacher_id,
            filename=unique_filename,
            original_filename=filename,
            file_type=file_ext,
            file_size=file_size,
            chunk_count=0
        )
        db.session.add(doc_record)
        db.session.flush()

        # Index chunks in RAG knowledge base
        rag = RAGService()
        chunk_count = rag.index_document(
            teacher_id=teacher_id,
            document_id=doc_record.id,
            filename=filename,
            text=extracted_text
        )
        doc_record.chunk_count = chunk_count
        db.session.commit()

        return doc_record

    @staticmethod
    def delete_document(document_id: str, teacher_id: str, upload_folder: str) -> bool:
        doc = Document.query.filter_by(id=document_id, teacher_id=teacher_id).first()
        if not doc:
            return False

        # Remove vector points
        rag = RAGService()
        rag.delete_document_points(doc.id)

        # Remove physical file
        file_path = os.path.join(upload_folder, doc.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        db.session.delete(doc)
        db.session.commit()
        return True
