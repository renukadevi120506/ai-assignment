import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'teacher' or 'student'
    full_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_assessments = db.relationship("Assessment", back_populates="teacher", cascade="all, delete-orphan", foreign_keys="Assessment.teacher_id")
    assigned_assessments = db.relationship("AssessmentAssignment", back_populates="student", cascade="all, delete-orphan", foreign_keys="AssessmentAssignment.student_id")
    submissions = db.relationship("StudentAnswer", back_populates="student", cascade="all, delete-orphan", foreign_keys="StudentAnswer.student_id")
    documents = db.relationship("Document", back_populates="teacher", cascade="all, delete-orphan", foreign_keys="Document.teacher_id")
    learning_gaps = db.relationship("LearningGap", back_populates="student", cascade="all, delete-orphan", foreign_keys="LearningGap.student_id")
    practice_questions = db.relationship("PracticeQuestion", back_populates="student", cascade="all, delete-orphan", foreign_keys="PracticeQuestion.student_id")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_teacher(self) -> bool:
        return self.role == "teacher"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
