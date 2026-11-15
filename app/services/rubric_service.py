from pathlib import Path
from typing import Any, Tuple

from app.ai.gemini_provider import GeminiProvider
from app.ai.llm_provider import RubricResponseSchema
from app.database import db
from app.models.assessment import Question
from app.models.rubric import Rubric, RubricCriterion

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"

class RubricService:
    @staticmethod
    def validate_rubric_sum(criteria_list: list[dict[str, Any]], expected_total: float) -> Tuple[bool, float]:
        total = sum(float(c.get("maximum_marks", 0)) for c in criteria_list)
        # Check within 0.01 precision for floating point numbers
        is_valid = abs(total - expected_total) < 0.01
        return is_valid, round(total, 2)

    @staticmethod
    def create_or_update_rubric(
        teacher_id: str,
        question_id: str,
        title: str,
        criteria_data: list[dict[str, Any]]
    ) -> Rubric:
        question = Question.query.get_or_404(question_id)
        
        # Validate sum
        sum_marks = sum(float(c.get("maximum_marks", 0)) for c in criteria_data)
        if abs(sum_marks - question.maximum_marks) > 0.01:
            raise ValueError(
                f"Criteria marks sum ({sum_marks}) must equal the question's maximum marks ({question.maximum_marks})."
            )

        rubric = Rubric.query.filter_by(question_id=question_id).first()
        if not rubric:
            rubric = Rubric(
                teacher_id=teacher_id,
                assessment_id=question.assessment_id,
                question_id=question_id,
                title=title,
                total_marks=question.maximum_marks
            )
            db.session.add(rubric)
            db.session.flush()
        else:
            rubric.title = title
            rubric.total_marks = question.maximum_marks
            # Clear existing criteria
            RubricCriterion.query.filter_by(rubric_id=rubric.id).delete()
            db.session.flush()

        for c in criteria_data:
            criterion = RubricCriterion(
                rubric_id=rubric.id,
                criterion_name=c.get("criterion_name", "").strip(),
                criterion_description=c.get("criterion_description", "").strip(),
                maximum_marks=float(c.get("maximum_marks", 1.0)),
                expected_concepts=c.get("expected_concepts", "").strip(),
                important_keywords=c.get("important_keywords", "").strip(),
                evaluation_guidelines=c.get("evaluation_guidelines", "").strip()
            )
            db.session.add(criterion)

        db.session.commit()
        return rubric

    @staticmethod
    def generate_ai_rubric(question_text: str, total_marks: float) -> dict[str, Any]:
        """Generate structured rubric recommendation using AI prompt."""
        prompt_file = PROMPTS_DIR / "rubric.txt"
        with open(prompt_file, "r") as f:
            template = f.read()

        prompt = template.format(question=question_text, total_marks=total_marks)
        provider = GeminiProvider()
        return provider.generate_json(prompt, RubricResponseSchema)
