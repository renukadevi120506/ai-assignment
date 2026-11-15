from pathlib import Path

from app.ai.gemini_provider import GeminiProvider
from app.ai.llm_provider import PracticeResponseSchema
from app.database import db
from app.models.evaluation import LearningGap, PracticeQuestion

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"

class PracticeService:
    @classmethod
    def generate_practice_for_gaps(cls, learning_gaps: list[LearningGap]) -> list[PracticeQuestion]:
        if not learning_gaps:
            return []

        gaps_payload = [
            {
                "concept_name": g.concept_name,
                "description": g.description,
                "difficulty_level": g.difficulty_level
            }
            for g in learning_gaps
        ]

        prompt_file = PROMPTS_DIR / "practice.txt"
        with open(prompt_file, "r") as f:
            template = f.read()

        import json
        prompt = template.format(learning_gaps_json=json.dumps(gaps_payload, indent=2))

        provider = GeminiProvider()
        result = provider.generate_json(prompt, PracticeResponseSchema)

        created_questions = []
        # Map gaps by concept name
        gap_map = {g.concept_name.lower(): g for g in learning_gaps}

        for item in result.get("practice_items", []):
            concept = item.get("concept_name", "").lower()
            target_gap = gap_map.get(concept)
            if not target_gap and learning_gaps:
                target_gap = learning_gaps[0]

            for q in item.get("questions", []):
                pq = PracticeQuestion(
                    learning_gap_id=target_gap.id if target_gap else learning_gaps[0].id,
                    student_id=target_gap.student_id if target_gap else learning_gaps[0].student_id,
                    question_text=q.get("question_text", ""),
                    sample_answer=q.get("sample_answer", ""),
                    difficulty_level=q.get("difficulty_level", "Intermediate"),
                    is_completed=False
                )
                db.session.add(pq)
                created_questions.append(pq)

        db.session.commit()
        return created_questions

    @staticmethod
    def submit_practice_response(question_id: str, student_id: str, student_answer: str) -> PracticeQuestion:
        pq = PracticeQuestion.query.filter_by(id=question_id, student_id=student_id).first_or_404()
        pq.student_practice_answer = student_answer.strip()
        pq.is_completed = True
        db.session.commit()
        return pq
