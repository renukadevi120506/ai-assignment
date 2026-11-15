from app.services.scoring_service import ScoringService


def test_clamp_mark():
    # Regular within bounds
    assert ScoringService.clamp_mark(2.5, 3.0) == 2.5
    # Exceeding max mark
    assert ScoringService.clamp_mark(4.5, 3.0) == 3.0
    # Negative mark
    assert ScoringService.clamp_mark(-1.0, 3.0) == 0.0
    # None or invalid
    assert ScoringService.clamp_mark(None, 3.0) == 0.0
    assert ScoringService.clamp_mark("invalid", 3.0) == 0.0

def test_process_criterion_scores():
    class DummyCriterion:
        def __init__(self, id, name, max_marks):
            self.id = id
            self.criterion_name = name
            self.maximum_marks = max_marks

    rubric = [
        DummyCriterion("c1", "Definition", 2.0),
        DummyCriterion("c2", "Retrieval Process", 3.0),
        DummyCriterion("c3", "Generation Process", 3.0),
        DummyCriterion("c4", "Real-World Example", 2.0),
    ]

    llm_suggestions = [
        {"criterion_name": "Definition", "suggested_marks": 2.0, "status": "correct", "explanation": "Good def", "supporting_evidence": ["Evidence 1"]},
        {"criterion_name": "Retrieval Process", "suggested_marks": 3.5, "status": "correct", "explanation": "Over max mark test"}, # Should clamp to 3.0
        {"criterion_name": "Generation Process", "suggested_marks": 1.5, "status": "partial", "explanation": "Partial"},
        {"criterion_name": "Real-World Example", "suggested_marks": -0.5, "status": "incorrect", "explanation": "Neg mark test"}, # Should clamp to 0.0
    ]

    processed, total_suggested, total_max, percentage = ScoringService.process_criterion_scores(rubric, llm_suggestions)

    assert total_max == 10.0
    # 2.0 + 3.0 (clamped from 3.5) + 1.5 + 0.0 (clamped from -0.5) = 6.5
    assert total_suggested == 6.5
    assert percentage == 65.0
    assert len(processed) == 4
    assert processed[1]["suggested_marks"] == 3.0
    assert processed[3]["suggested_marks"] == 0.0
