from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.database import db
from app.models.assessment import Assessment
from app.models.evaluation import LearningGap, PracticeQuestion
from app.models.submission import StudentAnswer
from app.services.assessment_service import AssessmentService
from app.utils.helpers import student_required

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    stats = AssessmentService.get_student_dashboard_stats(current_user.id)
    return render_template("student/dashboard.html", stats=stats)

@student_bp.route("/assessments")
@login_required
@student_required
def assessments():
    active_assessments = Assessment.query.filter_by(status="active").order_by(Assessment.created_at.desc()).all()
    # Check submissions by current user
    student_submissions = {s.assessment_id: s for s in StudentAnswer.query.filter_by(student_id=current_user.id).all()}
    return render_template("student/assessments.html", assessments=active_assessments, submissions=student_submissions)

@student_bp.route("/assessments/<string:id>", methods=["GET", "POST"])
@login_required
@student_required
def view_assessment(id):
    assessment = Assessment.query.filter_by(id=id, status="active").first_or_404()
    question = assessment.questions[0] if assessment.questions else None
    
    # Check if student already submitted
    existing_sub = StudentAnswer.query.filter_by(assessment_id=id, student_id=current_user.id).first()
    if existing_sub:
        flash("You have already submitted an answer for this assessment.", "info")
        return redirect(url_for("student.report_view", submission_id=existing_sub.id))

    if request.method == "POST":
        answer_text = request.form.get("answer_text", "").strip()
        if not answer_text:
            flash("Answer cannot be empty.", "warning")
            return render_template("student/submit_answer.html", assessment=assessment, question=question)

        sub = StudentAnswer(
            assessment_id=assessment.id,
            question_id=question.id if question else None,
            student_id=current_user.id,
            answer_text=answer_text,
            status="submitted"
        )
        db.session.add(sub)
        db.session.commit()
        flash("Your answer has been submitted successfully! Waiting for evaluation.", "success")
        return redirect(url_for("student.submissions_list"))

    return render_template("student/submit_answer.html", assessment=assessment, question=question)

@student_bp.route("/submissions")
@login_required
@student_required
def submissions_list():
    subs = StudentAnswer.query.filter_by(student_id=current_user.id).order_by(StudentAnswer.submitted_at.desc()).all()
    return render_template("student/submissions.html", submissions=subs)

@student_bp.route("/reports/<string:submission_id>")
@login_required
def report_view(submission_id):
    submission = StudentAnswer.query.get_or_404(submission_id)
    # Access control: student can only view their own approved report; teacher can view if owner
    if current_user.is_student:
        if submission.student_id != current_user.id:
            flash("Unauthorized access to report.", "danger")
            return redirect(url_for("student.dashboard"))
        if not submission.evaluation or submission.evaluation.status != "approved":
            flash("This evaluation report is still being reviewed by the teacher.", "info")
            return redirect(url_for("student.submissions_list"))
    elif current_user.is_teacher:
        if submission.assessment.teacher_id != current_user.id:
            flash("Unauthorized access.", "danger")
            return redirect(url_for("teacher.dashboard"))

    return render_template("student/report.html", submission=submission, evaluation=submission.evaluation)

@student_bp.route("/gaps")
@login_required
@student_required
def learning_gaps():
    gaps = LearningGap.query.filter_by(student_id=current_user.id).order_by(LearningGap.created_at.desc()).all()
    return render_template("student/learning_gaps.html", gaps=gaps)

@student_bp.route("/practice")
@login_required
@student_required
def practice_questions():
    questions = PracticeQuestion.query.filter_by(student_id=current_user.id).order_by(PracticeQuestion.is_completed.asc(), PracticeQuestion.created_at.desc()).all()
    return render_template("student/practice.html", questions=questions)

@student_bp.route("/practice/<string:question_id>/submit", methods=["POST"])
@login_required
@student_required
def submit_practice(question_id):
    pq = PracticeQuestion.query.filter_by(id=question_id, student_id=current_user.id).first_or_404()
    ans = request.form.get("student_practice_answer", "").strip()
    pq.student_practice_answer = ans
    pq.is_completed = True
    db.session.commit()
    flash("Practice answer submitted! Review the model answer below.", "success")
    return redirect(url_for("student.practice_questions"))
