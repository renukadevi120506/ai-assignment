from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models.assessment import Assessment
from app.models.evaluation import Evaluation
from app.models.submission import StudentAnswer
from app.services.assessment_service import AssessmentService
from app.utils.helpers import teacher_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

@teacher_bp.route("/dashboard")
@login_required
@teacher_required
def dashboard():
    stats = AssessmentService.get_teacher_dashboard_stats(current_user.id)
    return render_template("teacher/dashboard.html", stats=stats)

@teacher_bp.route("/submissions")
@login_required
@teacher_required
def submissions():
    assessments = Assessment.query.filter_by(teacher_id=current_user.id).all()
    assessment_ids = [a.id for a in assessments]
    submissions = (
        StudentAnswer.query.filter(StudentAnswer.assessment_id.in_(assessment_ids))
        .order_by(StudentAnswer.submitted_at.desc())
        .all()
    ) if assessment_ids else []
    return render_template("teacher/submissions.html", submissions=submissions)

@teacher_bp.route("/evaluations")
@login_required
@teacher_required
def evaluations():
    assessments = Assessment.query.filter_by(teacher_id=current_user.id).all()
    assessment_ids = [a.id for a in assessments]
    evals = (
        Evaluation.query.join(StudentAnswer)
        .filter(StudentAnswer.assessment_id.in_(assessment_ids))
        .order_by(Evaluation.evaluated_at.desc())
        .all()
    ) if assessment_ids else []
    return render_template("teacher/evaluations_list.html", evaluations=evals)

@teacher_bp.route("/analytics")
@login_required
@teacher_required
def analytics():
    stats = AssessmentService.get_teacher_dashboard_stats(current_user.id)
    assessments = Assessment.query.filter_by(teacher_id=current_user.id).all()
    return render_template("teacher/analytics.html", stats=stats, assessments=assessments)
