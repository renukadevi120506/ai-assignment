import pytest
from app.database import db
from app.models.user import User
from app.models.assessment import Assessment, Question
from app.models.rubric import Rubric, RubricCriterion
from app.models.submission import StudentAnswer
from app.services.rubric_service import RubricService
from app.services.assessment_service import AssessmentService

def test_assessment_and_rubric_sum_validation(app):
    with app.app_context():
        teacher = User(username="prof_jones", email="jones@edu.com", full_name="Prof Jones", role="teacher")
        teacher.set_password("Pass1234")
        db.session.add(teacher)
        db.session.commit()

        # Create assessment with 10 max marks
        assessment = AssessmentService.create_assessment(
            teacher_id=teacher.id,
            title="Introduction to Machine Learning",
            subject="Computer Science",
            topic="Supervised vs Unsupervised",
            question_text="Explain the key differences between Supervised and Unsupervised Learning.",
            maximum_marks=10.0
        )
        assert assessment.id is not None
        assert len(assessment.questions) == 1
        q = assessment.questions[0]
        assert q.maximum_marks == 10.0

        # Attempt to save invalid rubric sum (e.g. 8.0 instead of 10.0)
        invalid_criteria = [
            {"criterion_name": "Definition", "maximum_marks": 3.0},
            {"criterion_name": "Examples", "maximum_marks": 5.0}
        ]
        with pytest.raises(ValueError) as exc:
            RubricService.create_or_update_rubric(
                teacher_id=teacher.id,
                question_id=q.id,
                title="ML Rubric",
                criteria_data=invalid_criteria
            )
        assert "must equal the question's maximum marks" in str(exc.value)

        # Valid criteria sum (3.0 + 4.0 + 3.0 = 10.0)
        valid_criteria = [
            {"criterion_name": "Supervised Concept", "maximum_marks": 3.0},
            {"criterion_name": "Unsupervised Concept", "maximum_marks": 4.0},
            {"criterion_name": "Real-World Examples", "maximum_marks": 3.0}
        ]
        rubric = RubricService.create_or_update_rubric(
            teacher_id=teacher.id,
            question_id=q.id,
            title="ML Rubric",
            criteria_data=valid_criteria
        )
        assert rubric.id is not None
        assert len(rubric.criteria) == 3
        assert rubric.criteria_sum == 10.0

def test_student_submission_flow(app):
    with app.app_context():
        teacher = User(username="prof_t", email="t@edu.com", full_name="Teacher T", role="teacher")
        teacher.set_password("Pass1234")
        student = User(username="stud_s", email="s@edu.com", full_name="Student S", role="student")
        student.set_password("Pass1234")
        db.session.add_all([teacher, student])
        db.session.commit()

        assessment = AssessmentService.create_assessment(
            teacher_id=teacher.id,
            title="RAG Systems",
            subject="AI",
            topic="RAG",
            question_text="What is Retrieval-Augmented Generation?",
            maximum_marks=10.0
        )

        sub = StudentAnswer(
            assessment_id=assessment.id,
            question_id=assessment.questions[0].id,
            student_id=student.id,
            answer_text="RAG is an AI pattern that retrieves external domain knowledge and passes it to an LLM for factual generation."
        )
        db.session.add(sub)
        db.session.commit()

        assert sub.id is not None
        assert sub.status == "submitted"
        assert sub.student.full_name == "Student S"
