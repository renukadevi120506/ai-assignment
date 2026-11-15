from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


# Pydantic Schemas for Structured LLM Outputs
class CriterionResultSchema(BaseModel):
    criterion_name: str
    maximum_marks: float
    suggested_marks: float
    status: str = Field(default="correct", description="correct, partial, missing, incorrect")
    explanation: str
    supporting_evidence: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)

class IdentifiedConceptSchema(BaseModel):
    concept: str
    status: str
    notes: str | None = ""

class LearningGapItemSchema(BaseModel):
    concept_name: str
    description: str
    evidence: str | None = ""
    recommended_material: str | None = ""
    difficulty_level: str = "Intermediate"

class EvaluationResponseSchema(BaseModel):
    criteria_results: list[CriterionResultSchema]
    identified_concepts: list[IdentifiedConceptSchema] = Field(default_factory=list)
    learning_gaps: list[LearningGapItemSchema] = Field(default_factory=list)
    overall_feedback: str
    requires_teacher_review: bool = True

class PracticeQuestionDetailSchema(BaseModel):
    difficulty_level: str = "Intermediate"
    question_text: str
    sample_answer: str | None = ""

class PracticeItemSchema(BaseModel):
    concept_name: str
    questions: list[PracticeQuestionDetailSchema]

class PracticeResponseSchema(BaseModel):
    practice_items: list[PracticeItemSchema]

class RubricCriterionItemSchema(BaseModel):
    criterion_name: str
    maximum_marks: float
    criterion_description: str | None = ""
    expected_concepts: str | None = ""
    important_keywords: str | None = ""
    evaluation_guidelines: str | None = ""

class RubricResponseSchema(BaseModel):
    rubric_title: str
    total_marks: float
    criteria: list[RubricCriterionItemSchema]


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_json(self, prompt: str, schema_class: type[BaseModel]) -> dict[str, Any]:
        """Generate structured JSON conforming to a Pydantic schema."""

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generate unstructured text."""
