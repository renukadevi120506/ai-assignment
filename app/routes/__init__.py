from app.routes.assessment import assessment_bp
from app.routes.auth import auth_bp
from app.routes.documents import document_bp
from app.routes.evaluation import evaluation_bp
from app.routes.learning import learning_bp
from app.routes.rubric import rubric_bp
from app.routes.student import student_bp
from app.routes.teacher import teacher_bp

__all__ = [
    "assessment_bp",
    "auth_bp",
    "document_bp",
    "evaluation_bp",
    "learning_bp",
    "rubric_bp",
    "student_bp",
    "teacher_bp"
]
