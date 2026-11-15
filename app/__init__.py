import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

from app.config import Config, config_by_name
from app.database import db, migrate

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    
    env_config = config_by_name.get(config_name, Config)
    app.config.from_object(env_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Register blueprints
    from app.routes.assessment import assessment_bp
    from app.routes.auth import auth_bp
    from app.routes.documents import document_bp
    from app.routes.evaluation import evaluation_bp
    from app.routes.learning import learning_bp
    from app.routes.rubric import rubric_bp
    from app.routes.student import student_bp
    from app.routes.teacher import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(rubric_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(learning_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.is_teacher:
                return redirect(url_for("teacher.dashboard"))
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    # Ensure database tables exist automatically and populate initial starter assessments
    with app.app_context():
        try:
            db.create_all()
            from app.database.seed import seed_database_if_empty
            seed_database_if_empty()
        except Exception as e:
            app.logger.warning(f"Database table check/seed: {e}")

    # Jinja2 template filters
    @app.template_filter("status_badge")
    def status_badge_filter(status: str) -> str:
        mapping = {
            "approved": "success",
            "evaluated": "info",
            "evaluating": "warning",
            "pending_review": "warning",
            "submitted": "secondary",
            "rejected": "danger",
            "active": "primary",
            "resolved": "success",
            "correct": "success",
            "partial": "warning",
            "missing": "danger",
            "incorrect": "danger"
        }
        return mapping.get(str(status).lower(), "secondary")

    return app
