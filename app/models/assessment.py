import uuid
from datetime import datetime

from app.database import db


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(150), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")  # 'draft', 'active', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = db.relationship("User", back_populates="created_assessments", foreign_keys=[teacher_id])
    questions = db.relationship("Question", back_populates="assessment", cascade="all, delete-orphan", lazy="joined")
    assignments = db.relationship("AssessmentAssignment", back_populates="assessment", cascade="all, delete-orphan")
    submissions = db.relationship("StudentAnswer", back_populates="assessment", cascade="all, delete-orphan")

    @property
    def total_max_marks(self):
        return sum(q.maximum_marks for q in self.questions) if self.questions else 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "title": self.title,
            "subject": self.subject,
            "topic": self.topic,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "questions_count": len(self.questions) if self.questions else 0,
            "total_marks": self.total_max_marks
        }

class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    maximum_marks = db.Column(db.Float, nullable=False, default=10.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assessment = db.relationship("Assessment", back_populates="questions")
    rubric = db.relationship("Rubric", back_populates="question", uselist=False, cascade="all, delete-orphan")
    answers = db.relationship("StudentAnswer", back_populates="question", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "question_text": self.question_text,
            "maximum_marks": self.maximum_marks,
            "has_rubric": self.rubric is not None
        }

class AssessmentAssignment(db.Model):
    __tablename__ = "assessment_assignments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assessment = db.relationship("Assessment", back_populates="assignments")
    student = db.relationship("User", back_populates="assigned_assessments")

    __table_args__ = (
        db.UniqueConstraint("assessment_id", "student_id", name="uq_assessment_student"),
    )
