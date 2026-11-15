from typing import Any

from app.database import db
from app.models.evaluation import LearningGap


class LearningGapService:
    @staticmethod
    def save_learning_gaps(
        evaluation_id: str,
        student_id: str,
        gaps_data: list[dict[str, Any]]
    ) -> list[LearningGap]:
        saved_gaps = []
        for g in gaps_data:
            concept = g.get("concept_name", "").strip()
            if not concept:
                continue

            gap = LearningGap(
                evaluation_id=evaluation_id,
                student_id=student_id,
                concept_name=concept,
                description=g.get("description", "").strip(),
                evidence=g.get("evidence", "").strip(),
                recommended_material=g.get("recommended_material", "").strip(),
                difficulty_level=g.get("difficulty_level", "Intermediate")
            )
            db.session.add(gap)
            saved_gaps.append(gap)

        db.session.flush()
        return saved_gaps

    @staticmethod
    def get_student_active_gaps(student_id: str) -> list[LearningGap]:
        return LearningGap.query.filter_by(student_id=student_id, status="active").order_by(LearningGap.created_at.desc()).all()

    @staticmethod
    def resolve_gap(gap_id: str, student_id: str) -> bool:
        gap = LearningGap.query.filter_by(id=gap_id, student_id=student_id).first()
        if not gap:
            return False
        gap.status = "resolved"
        db.session.commit()
        return True
