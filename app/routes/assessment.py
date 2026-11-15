from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.database import db
from app.models.assessment import Assessment
from app.services.assessment_service import AssessmentService
from app.utils.helpers import teacher_required

assessment_bp = Blueprint("assessment", __name__, url_prefix="/teacher/assessments")

@assessment_bp.route("/")
@login_required
@teacher_required
def list_assessments():
    assessments = Assessment.query.filter_by(teacher_id=current_user.id).order_by(Assessment.created_at.desc()).all()
    return render_template("teacher/assessments.html", assessments=assessments)

@assessment_bp.route("/create", methods=["GET", "POST"])
@login_required
@teacher_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        question_text = request.form.get("question_text", "").strip()
        max_marks = float(request.form.get("maximum_marks", 10.0))
        due_date_str = request.form.get("due_date", "")

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                pass

        if not title or not subject or not topic or not question_text:
            flash("All fields are required.", "danger")
            return render_template("teacher/create_assessment.html")

        assessment = AssessmentService.create_assessment(
            teacher_id=current_user.id,
            title=title,
            subject=subject,
            topic=topic,
            question_text=question_text,
            maximum_marks=max_marks,
            due_date=due_date
        )

        flash("Assessment created successfully! Now set up its marking rubric.", "success")
        question = assessment.questions[0] if assessment.questions else None
        if question:
            return redirect(url_for("rubric.manage_rubric", question_id=question.id))
        return redirect(url_for("assessment.list_assessments"))

    return render_template("teacher/create_assessment.html")

@assessment_bp.route("/<string:id>/edit", methods=["GET", "POST"])
@login_required
@teacher_required
def edit(id):
    assessment = Assessment.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    question = assessment.questions[0] if assessment.questions else None

    if request.method == "POST":
        assessment.title = request.form.get("title", "").strip()
        assessment.subject = request.form.get("subject", "").strip()
        assessment.topic = request.form.get("topic", "").strip()
        assessment.status = request.form.get("status", "active")
        
        due_date_str = request.form.get("due_date", "")
        if due_date_str:
            try:
                assessment.due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                pass
        else:
            assessment.due_date = None

        if question:
            question.question_text = request.form.get("question_text", "").strip()
            question.maximum_marks = float(request.form.get("maximum_marks", question.maximum_marks))

        db.session.commit()
        flash("Assessment updated successfully.", "success")
        return redirect(url_for("assessment.list_assessments"))

    return render_template("teacher/edit_assessment.html", assessment=assessment, question=question)

@assessment_bp.route("/<string:id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete(id):
    assessment = Assessment.query.filter_by(id=id, teacher_id=current_user.id).first_or_404()
    db.session.delete(assessment)
    db.session.commit()
    flash("Assessment deleted.", "info")
    return redirect(url_for("assessment.list_assessments"))
