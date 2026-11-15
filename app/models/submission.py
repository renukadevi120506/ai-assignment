import uuid
from datetime import datetime

from app.database import db


class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.String(36), db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default="submitted")  # submitted, evaluating, evaluated, approved, rejected

    # Relationships
    assessment = db.relationship("Assessment", back_populates="submissions")
    question = db.relationship("Question", back_populates="answers")
    student = db.relationship("User", back_populates="submissions")
    evaluation = db.relationship("Evaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else "",
            "answer_text": self.answer_text,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "status": self.status,
            "has_evaluation": self.evaluation is not None
        }

class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, txt
    file_size = db.Column(db.Integer, nullable=False, default=0)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    collection_name = db.Column(db.String(100), nullable=False, default="educational_documents")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teacher = db.relationship("User", back_populates="documents")

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
