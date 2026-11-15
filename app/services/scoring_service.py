from typing import Any


class ScoringService:
    """
    Deterministic scoring engine.
    Ensures mathematical rigor and rubric compliance:
    - Marks are strictly non-negative
    - Marks do not exceed the criterion maximum
    - Total marks and percentages are calculated strictly programmatically
    - Overrides any hallucinated or inconsistent arithmetic from the LLM
    """

    @staticmethod
    def clamp_mark(mark: float, max_mark: float) -> float:
        """Clamp mark between 0.0 and max_mark with 2 decimal precision."""
        if mark is None:
            return 0.0
        try:
            val = float(mark)
        except (ValueError, TypeError):
            return 0.0
        
        clamped = max(0.0, min(val, float(max_mark)))
        return round(clamped, 2)

    @classmethod
    def process_criterion_scores(
        cls,
        rubric_criteria: list[Any],
        suggested_results: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], float, float, float]:
        """
        Match suggested criterion evaluations with authoritative database rubric criteria.
        Returns:
            - processed_criteria: list of validated criteria scores
            - total_suggested: programmatically summed marks
            - total_max: sum of criterion maximums
            - percentage: score percentage
        """
        # Map criteria by name (lowercase for resilient matching)
        suggested_map = {}
        for item in suggested_results:
            name_key = str(item.get("criterion_name", "")).strip().lower()
            suggested_map[name_key] = item

        processed = []
        total_suggested = 0.0
        total_max = 0.0

        for crit in rubric_criteria:
            crit_name = crit.criterion_name if hasattr(crit, "criterion_name") else crit.get("criterion_name", "")
            crit_max = float(crit.maximum_marks if hasattr(crit, "maximum_marks") else crit.get("maximum_marks", 1.0))
            crit_id = crit.id if hasattr(crit, "id") else crit.get("id", None)

            # Match from suggestions
            match = suggested_map.get(crit_name.lower())
            if not match:
                # Partial match attempt
                for key, val in suggested_map.items():
                    if key in crit_name.lower() or crit_name.lower() in key:
                        match = val
                        break

            raw_suggested = match.get("suggested_marks", 0.0) if match else 0.0
            clamped_score = cls.clamp_mark(raw_suggested, crit_max)

            status = match.get("status", "partial") if match else "missing"
            if status not in {"correct", "partial", "missing", "incorrect"}:
                status = "correct" if clamped_score == crit_max else ("missing" if clamped_score == 0 else "partial")

            explanation = match.get("explanation", "Evaluated based on rubric criteria.") if match else "No specific answer provided for this criterion."
            evidence = match.get("supporting_evidence", []) if match else []
            missing = match.get("missing_concepts", []) if match else []

            processed.append({
                "criterion_id": crit_id,
                "criterion_name": crit_name,
                "max_marks": crit_max,
                "suggested_marks": clamped_score,
                "approved_marks": clamped_score, # default to suggested until teacher edits
                "status": status,
                "explanation": explanation,
                "supporting_evidence": evidence,
                "missing_concepts": missing
            })

            total_suggested += clamped_score
            total_max += crit_max

        percentage = round((total_suggested / total_max * 100.0), 2) if total_max > 0 else 0.0
        total_suggested = round(total_suggested, 2)
        total_max = round(total_max, 2)

        return processed, total_suggested, total_max, percentage

    @classmethod
    def recalculate_total_from_approved(
        cls,
        criterion_scores: list[Any],
        max_marks: float
    ) -> tuple[float, float]:
        """
        Recalculate total score and percentage after teacher edits individual criterion marks.
        """
        total = 0.0
        for cs in criterion_scores:
            score = cs.approved_marks if (hasattr(cs, "approved_marks") and cs.approved_marks is not None) else (
                cs.suggested_marks if hasattr(cs, "suggested_marks") else 0.0
            )
            total += float(score)

        total = round(max(0.0, min(total, max_marks)), 2)
        percentage = round((total / max_marks * 100.0), 2) if max_marks > 0 else 0.0
        return total, percentage
