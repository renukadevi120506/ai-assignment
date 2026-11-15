import uuid
from datetime import datetime

from app.database import db


class Rubric(db.Model):
    __tablename__ = "rubrics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = db.Column(db.String(36), db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.String(36), db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    title = db.Column(db.String(200), nullable=False)
    total_marks = db.Column(db.Float, nullable=False, default=10.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    question = db.relationship("Question", back_populates="rubric")
    criteria = db.relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan", lazy="joined", order_by="RubricCriterion.created_at")

    @property
    def criteria_sum(self):
        return sum(c.maximum_marks for c in self.criteria) if self.criteria else 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "title": self.title,
            "total_marks": self.total_marks,
            "criteria": [c.to_dict() for c in self.criteria]
        }

class RubricCriterion(db.Model):
    __tablename__ = "rubric_criteria"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rubric_id = db.Column(db.String(36), db.ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_name = db.Column(db.String(150), nullable=False)
    criterion_description = db.Column(db.Text, nullable=True)
    maximum_marks = db.Column(db.Float, nullable=False, default=1.0)
    expected_concepts = db.Column(db.Text, nullable=True)     # comma-separated or text
    important_keywords = db.Column(db.Text, nullable=True)    # comma-separated or text
    evaluation_guidelines = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rubric = db.relationship("Rubric", back_populates="criteria")
    scores = db.relationship("CriterionScore", back_populates="criterion", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "rubric_id": self.rubric_id,
            "criterion_name": self.criterion_name,
            "criterion_description": self.criterion_description,
            "maximum_marks": self.maximum_marks,
            "expected_concepts": self.expected_concepts,
            "important_keywords": self.important_keywords,
            "evaluation_guidelines": self.evaluation_guidelines
        }
