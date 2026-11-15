from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.evaluation import Evaluation
from app.models.submission import StudentAnswer
from app.services.evaluation_service import EvaluationService
from app.utils.helpers import teacher_required

evaluation_bp = Blueprint("evaluation", __name__, url_prefix="/evaluations")

@evaluation_bp.route("/<string:submission_id>/run", methods=["POST"])
@login_required
@teacher_required
def run_evaluation(submission_id):
    submission = StudentAnswer.query.get_or_404(submission_id)
    if submission.assessment.teacher_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("teacher.submissions"))

    provider_name = request.form.get("provider", "gemini")
    include_rag = bool(request.form.get("include_rag", True))

    try:
        eval_record = EvaluationService.run_evaluation(
            submission_id=submission_id,
            provider_name=provider_name,
            include_rag=include_rag
        )
        flash("AI Evaluation generated successfully! Please review and approve marks below.", "success")
        return redirect(url_for("evaluation.review", evaluation_id=eval_record.id))
    except Exception as e:
        submission.status = "submitted" # reset
        from app.database import db
        db.session.commit()
        flash(f"Error during AI evaluation: {e!s}", "danger")
        return redirect(url_for("teacher.submissions"))

@evaluation_bp.route("/<string:evaluation_id>/review", methods=["GET"])
@login_required
@teacher_required
def review(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if evaluation.submission.assessment.teacher_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("teacher.evaluations"))

    return render_template("teacher/evaluation_review.html", evaluation=evaluation)

@evaluation_bp.route("/<string:evaluation_id>/approve", methods=["POST"])
@login_required
@teacher_required
def approve(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if evaluation.submission.assessment.teacher_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("teacher.evaluations"))

    # Extract teacher modified marks for each criterion
    approved_marks = {}
    for cs in evaluation.criterion_scores:
        field_name = f"criterion_marks_{cs.id}"
        if field_name in request.form:
            try:
                approved_marks[cs.id] = float(request.form.get(field_name))
            except ValueError:
                pass

    teacher_notes = request.form.get("teacher_notes", "").strip()

    try:
        EvaluationService.teacher_approve_evaluation(
            evaluation_id=evaluation_id,
            teacher_id=current_user.id,
            approved_criterion_marks=approved_marks,
            teacher_notes=teacher_notes
        )
        flash("Evaluation approved and finalized! The student can now view the official report.", "success")
        return redirect(url_for("teacher.evaluations"))
    except Exception as e:
        flash(f"Error approving evaluation: {e!s}", "danger")
        return redirect(url_for("evaluation.review", evaluation_id=evaluation_id))

@evaluation_bp.route("/<string:evaluation_id>/reject", methods=["POST"])
@login_required
@teacher_required
def reject(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if evaluation.submission.assessment.teacher_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("teacher.evaluations"))

    reason = request.form.get("reject_reason", "Rejected by teacher.").strip()
    EvaluationService.teacher_reject_evaluation(
        evaluation_id=evaluation_id,
        teacher_id=current_user.id,
        reason=reason
    )
    flash("Evaluation rejected.", "warning")
    return redirect(url_for("teacher.evaluations"))
