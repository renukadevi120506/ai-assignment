import json
import uuid
from datetime import datetime

from app.database import db


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("student_answers.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    total_suggested_marks = db.Column(db.Float, nullable=False, default=0.0)
    total_approved_marks = db.Column(db.Float, nullable=True)
    max_marks = db.Column(db.Float, nullable=False, default=10.0)
    percentage = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), nullable=False, default="pending_review")  # pending_review, approved, rejected
    overall_feedback = db.Column(db.Text, nullable=True)
    teacher_notes = db.Column(db.Text, nullable=True)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    submission = db.relationship("StudentAnswer", back_populates="evaluation")
    criterion_scores = db.relationship("CriterionScore", back_populates="evaluation", cascade="all, delete-orphan", lazy="joined")
    learning_gaps = db.relationship("LearningGap", back_populates="evaluation", cascade="all, delete-orphan", lazy="joined")
    feedbacks = db.relationship("TeacherFeedback", back_populates="evaluation", cascade="all, delete-orphan", order_by="TeacherFeedback.created_at.desc()")

    @property
    def final_score(self):
        if self.status == "approved" and self.total_approved_marks is not None:
            return self.total_approved_marks
        return self.total_suggested_marks

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "total_suggested_marks": self.total_suggested_marks,
            "total_approved_marks": self.total_approved_marks,
            "max_marks": self.max_marks,
            "percentage": self.percentage,
            "status": self.status,
            "overall_feedback": self.overall_feedback,
            "teacher_notes": self.teacher_notes,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "criterion_scores": [c.to_dict() for c in self.criterion_scores],
            "learning_gaps": [g.to_dict() for g in self.learning_gaps]
        }

class CriterionScore(db.Model):
    __tablename__ = "criterion_scores"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = db.Column(db.String(36), db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = db.Column(db.String(36), db.ForeignKey("rubric_criteria.id", ondelete="SET NULL"), nullable=True)
    criterion_name = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=1.0)
    suggested_marks = db.Column(db.Float, nullable=False, default=0.0)
    approved_marks = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="correct")  # correct, partial, missing, incorrect
    explanation = db.Column(db.Text, nullable=True)
    supporting_evidence_json = db.Column(db.Text, nullable=True)  # JSON string list
    missing_concepts_json = db.Column(db.Text, nullable=True)     # JSON string list

    # Relationships
    evaluation = db.relationship("Evaluation", back_populates="criterion_scores")
    criterion = db.relationship("RubricCriterion", back_populates="scores")

    @property
    def supporting_evidence(self):
        if not self.supporting_evidence_json:
            return []
        try:
            return json.loads(self.supporting_evidence_json)
        except Exception:
            return [self.supporting_evidence_json]

    @supporting_evidence.setter
    def supporting_evidence(self, val):
        self.supporting_evidence_json = json.dumps(val if isinstance(val, list) else [val])

    @property
    def missing_concepts(self):
        if not self.missing_concepts_json:
            return []
        try:
            return json.loads(self.missing_concepts_json)
        except Exception:
            return [self.missing_concepts_json]

    @missing_concepts.setter
    def missing_concepts(self, val):
        self.missing_concepts_json = json.dumps(val if isinstance(val, list) else [val])

    def to_dict(self):
        return {
            "id": self.id,
            "criterion_id": self.criterion_id,
            "criterion_name": self.criterion_name,
            "max_marks": self.max_marks,
            "suggested_marks": self.suggested_marks,
            "approved_marks": self.approved_marks,
            "status": self.status,
            "explanation": self.explanation,
            "supporting_evidence": self.supporting_evidence,
            "missing_concepts": self.missing_concepts
        }

class LearningGap(db.Model):
    __tablename__ = "learning_gaps"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = db.Column(db.String(36), db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text, nullable=True)
    recommended_material = db.Column(db.Text, nullable=True)
    difficulty_level = db.Column(db.String(30), nullable=False, default="Intermediate")  # Beginner, Intermediate, Advanced
    status = db.Column(db.String(20), nullable=False, default="active")  # active, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    evaluation = db.relationship("Evaluation", back_populates="learning_gaps")
    student = db.relationship("User", back_populates="learning_gaps")
    practice_questions = db.relationship("PracticeQuestion", back_populates="learning_gap", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "evaluation_id": self.evaluation_id,
            "student_id": self.student_id,
            "concept_name": self.concept_name,
            "description": self.description,
            "evidence": self.evidence,
            "recommended_material": self.recommended_material,
            "difficulty_level": self.difficulty_level,
            "status": self.status,
            "practice_questions": [q.to_dict() for q in self.practice_questions]
        }

class PracticeQuestion(db.Model):
    __tablename__ = "practice_questions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learning_gap_id = db.Column(db.String(36), db.ForeignKey("learning_gaps.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    sample_answer = db.Column(db.Text, nullable=True)
    difficulty_level = db.Column(db.String(30), nullable=False, default="Intermediate")  # Beginner, Intermediate, Advanced
    student_practice_answer = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    learning_gap = db.relationship("LearningGap", back_populates="practice_questions")
    student = db.relationship("User", back_populates="practice_questions")

    def to_dict(self):
        return {
            "id": self.id,
            "learning_gap_id": self.learning_gap_id,
            "student_id": self.student_id,
            "question_text": self.question_text,
            "sample_answer": self.sample_answer,
            "difficulty_level": self.difficulty_level,
            "student_practice_answer": self.student_practice_answer,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class TeacherFeedback(db.Model):
    __tablename__ = "teacher_feedback"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = db.Column(db.String(36), db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comments = db.Column(db.Text, nullable=True)
    action = db.Column(db.String(20), nullable=False, default="approve")  # approve, reject, edit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    evaluation = db.relationship("Evaluation", back_populates="feedbacks")
    teacher = db.relationship("User", foreign_keys=[teacher_id])
