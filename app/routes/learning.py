from flask import Blueprint, flash, redirect, url_for
from flask_login import current_user, login_required

from app.services.learning_gap_service import LearningGapService
from app.utils.helpers import student_required

learning_bp = Blueprint("learning", __name__, url_prefix="/learning")

@learning_bp.route("/gaps")
@login_required
@student_required
def gaps():
    return redirect(url_for("student.learning_gaps"))

@learning_bp.route("/practice")
@login_required
@student_required
def practice():
    return redirect(url_for("student.practice_questions"))

@learning_bp.route("/gap/<string:gap_id>/resolve", methods=["POST"])
@login_required
@student_required
def resolve_gap(gap_id):
    success = LearningGapService.resolve_gap(gap_id, current_user.id)
    if success:
        flash("Learning gap marked as resolved!", "success")
    else:
        flash("Could not resolve learning gap.", "danger")
    return redirect(url_for("student.learning_gaps"))
