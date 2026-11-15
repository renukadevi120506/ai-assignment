from datetime import datetime
from typing import Any

from app.database import db
from app.models.assessment import Assessment, Question
from app.models.evaluation import Evaluation
from app.models.submission import StudentAnswer
from app.models.user import User


class AssessmentService:
    @staticmethod
    def create_assessment(
        teacher_id: str,
        title: str,
        subject: str,
        topic: str,
        question_text: str,
        maximum_marks: float,
        due_date: datetime | None = None
    ) -> Assessment:
        assessment = Assessment(
            teacher_id=teacher_id,
            title=title,
            subject=subject,
            topic=topic,
            due_date=due_date,
            status="active"
        )
        db.session.add(assessment)
        db.session.flush()

        question = Question(
            assessment_id=assessment.id,
            question_text=question_text,
            maximum_marks=float(maximum_marks)
        )
        db.session.add(question)
        db.session.commit()
        return assessment

    @staticmethod
    def get_teacher_dashboard_stats(teacher_id: str) -> dict[str, Any]:
        assessments = Assessment.query.filter_by(teacher_id=teacher_id).all()
        assessment_ids = [a.id for a in assessments]

        total_assessments = len(assessments)
        total_students = User.query.filter_by(role="student").count()

        submissions = StudentAnswer.query.filter(StudentAnswer.assessment_id.in_(assessment_ids)).all() if assessment_ids else []
        total_submissions = len(submissions)

        pending_evaluations = sum(1 for s in submissions if s.status in ["submitted", "evaluating", "evaluated"])
        completed_evaluations = sum(1 for s in submissions if s.status == "approved")

        # Average student scores for approved evaluations
        approved_evals = (
            Evaluation.query.join(StudentAnswer)
            .filter(StudentAnswer.assessment_id.in_(assessment_ids), Evaluation.status == "approved")
            .all()
        ) if assessment_ids else []

        avg_score = round(sum(e.percentage for e in approved_evals) / len(approved_evals), 1) if approved_evals else 0.0

        # Recent submissions
        recent_submissions = (
            StudentAnswer.query.filter(StudentAnswer.assessment_id.in_(assessment_ids))
            .order_by(StudentAnswer.submitted_at.desc())
            .limit(5)
            .all()
        ) if assessment_ids else []

        # Chart.js analytics: distribution (<50%, 50-70%, 70-85%, >85%)
        dist = {"< 50%": 0, "50-70%": 0, "70-85%": 0, "85-100%": 0}
        for e in approved_evals:
            p = e.percentage
            if p < 50:
                dist["< 50%"] += 1
            elif p < 70:
                dist["50-70%"] += 1
            elif p < 85:
                dist["70-85%"] += 1
            else:
                dist["85-100%"] += 1

        return {
            "total_assessments": total_assessments,
            "total_students": total_students,
            "total_submissions": total_submissions,
            "pending_evaluations": pending_evaluations,
            "completed_evaluations": completed_evaluations,
            "average_score": avg_score,
            "recent_submissions": recent_submissions,
            "score_distribution": dist
        }

    @staticmethod
    def get_student_dashboard_stats(student_id: str) -> dict[str, Any]:
        all_active_assessments = Assessment.query.filter_by(status="active").all()
        student_submissions = StudentAnswer.query.filter_by(student_id=student_id).all()
        submitted_assessment_ids = {s.assessment_id for s in student_submissions}

        pending_tasks = [a for a in all_active_assessments if a.id not in submitted_assessment_ids]
        
        approved_evals = (
            Evaluation.query.join(StudentAnswer)
            .filter(StudentAnswer.student_id == student_id, Evaluation.status == "approved")
            .all()
        )

        avg_score = round(sum(e.percentage for e in approved_evals) / len(approved_evals), 1) if approved_evals else 0.0

        return {
            "assigned_count": len(all_active_assessments),
            "submitted_count": len(student_submissions),
            "pending_count": len(pending_tasks),
            "approved_evaluations": approved_evals,
            "average_score": avg_score,
            "pending_assessments": pending_tasks[:5]
        }
