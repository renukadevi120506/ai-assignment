from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.assessment import Assessment, Question
from app.models.rubric import Rubric
from app.services.rubric_service import RubricService
from app.utils.helpers import teacher_required

rubric_bp = Blueprint("rubric", __name__, url_prefix="/teacher/rubrics")

@rubric_bp.route("/")
@login_required
@teacher_required
def list_rubrics():
    assessments = Assessment.query.filter_by(teacher_id=current_user.id).all()
    questions = []
    for a in assessments:
        questions.extend(a.questions)
    return render_template("teacher/rubrics.html", questions=questions)

@rubric_bp.route("/manage/<string:question_id>", methods=["GET", "POST"])
@login_required
@teacher_required
def manage_rubric(question_id):
    question = Question.query.get_or_404(question_id)
    if question.assessment.teacher_id != current_user.id:
        flash("Unauthorized access to this rubric.", "danger")
        return redirect(url_for("rubric.list_rubrics"))

    rubric = Rubric.query.filter_by(question_id=question_id).first()

    if request.method == "POST":
        title = request.form.get("title", f"Rubric for {question.assessment.title}")
        crit_names = request.form.getlist("criterion_name[]")
        crit_maxes = request.form.getlist("maximum_marks[]")
        crit_descs = request.form.getlist("criterion_description[]")
        crit_concepts = request.form.getlist("expected_concepts[]")
        crit_keywords = request.form.getlist("important_keywords[]")
        crit_guidelines = request.form.getlist("evaluation_guidelines[]")

        criteria_data = []
        for i in range(len(crit_names)):
            if crit_names[i].strip():
                criteria_data.append({
                    "criterion_name": crit_names[i].strip(),
                    "maximum_marks": float(crit_maxes[i] if i < len(crit_maxes) and crit_maxes[i] else 1.0),
                    "criterion_description": crit_descs[i].strip() if i < len(crit_descs) else "",
                    "expected_concepts": crit_concepts[i].strip() if i < len(crit_concepts) else "",
                    "important_keywords": crit_keywords[i].strip() if i < len(crit_keywords) else "",
                    "evaluation_guidelines": crit_guidelines[i].strip() if i < len(crit_guidelines) else ""
                })

        try:
            RubricService.create_or_update_rubric(
                teacher_id=current_user.id,
                question_id=question_id,
                title=title,
                criteria_data=criteria_data
            )
            flash("Rubric saved successfully!", "success")
            return redirect(url_for("rubric.list_rubrics"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("teacher/manage_rubric.html", question=question, rubric=rubric)

@rubric_bp.route("/ai-generate", methods=["POST"])
@login_required
@teacher_required
def ai_generate():
    data = request.get_json() or {}
    question_text = data.get("question_text", "")
    total_marks = float(data.get("total_marks", 10.0))

    if not question_text:
        return jsonify({"success": False, "error": "Question text is required."}), 400

    try:
        generated = RubricService.generate_ai_rubric(question_text, total_marks)
        return jsonify({"success": True, "rubric": generated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
