import json
from datetime import datetime
from pathlib import Path

from app.ai.gemini_provider import GeminiProvider
from app.ai.llm_provider import EvaluationResponseSchema
from app.ai.ollama_provider import OllamaProvider
from app.ai.rag_service import RAGService
from app.database import db
from app.models.evaluation import CriterionScore, Evaluation, TeacherFeedback
from app.models.submission import StudentAnswer
from app.services.learning_gap_service import LearningGapService
from app.services.practice_service import PracticeService
from app.services.scoring_service import ScoringService

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"

class EvaluationService:
    @classmethod
    def get_llm_provider(cls, provider_type: str = "gemini"):
        if provider_type == "ollama":
            return OllamaProvider()
        return GeminiProvider()

    @classmethod
    def run_evaluation(
        cls,
        submission_id: str,
        provider_name: str = "gemini",
        include_rag: bool = True
    ) -> Evaluation:
        """Execute full semantic AI evaluation pipeline on a student submission."""
        submission = StudentAnswer.query.get_or_404(submission_id)
        question = submission.question
        rubric = question.rubric

        if not rubric or not rubric.criteria:
            raise ValueError(f"Cannot evaluate: Question '{question.id}' does not have a defined rubric.")

        # Update status to evaluating
        submission.status = "evaluating"
        db.session.commit()

        # Step 1: Retrieve RAG reference context if educational materials exist for teacher
        retrieved_passages = []
        reference_context = "No reference document provided."
        if include_rag and question.assessment and question.assessment.teacher_id:
            rag = RAGService()
            search_query = f"{question.question_text} {submission.answer_text}"
            retrieved_passages = rag.search_relevant_passages(
                query=search_query,
                teacher_id=question.assessment.teacher_id,
                top_k=3
            )
            if retrieved_passages:
                reference_context = "\n---\n".join([p["text"] for p in retrieved_passages])

        # Step 2: Prepare prompt with question, rubric criteria, student answer, and context
        rubric_payload = [
            {
                "criterion_name": c.criterion_name,
                "maximum_marks": c.maximum_marks,
                "expected_concepts": c.expected_concepts,
                "important_keywords": c.important_keywords,
                "evaluation_guidelines": c.evaluation_guidelines
            }
            for c in rubric.criteria
        ]

        prompt_file = PROMPTS_DIR / "evaluation.txt"
        with open(prompt_file, "r") as f:
            template = f.read()

        prompt = template.format(
            question=question.question_text,
            rubric_json=json.dumps(rubric_payload, indent=2),
            reference_context=reference_context,
            student_answer=submission.answer_text
        )

        # Step 3: Call LLM provider
        provider = cls.get_llm_provider(provider_name)
        llm_response = provider.generate_json(prompt, EvaluationResponseSchema)

        # Step 4: Scoring Engine - Deterministic verification and mathematical recalculation
        criteria_results = llm_response.get("criteria_results", [])
        processed_criteria, total_suggested, total_max, percentage = ScoringService.process_criterion_scores(
            rubric_criteria=rubric.criteria,
            suggested_results=criteria_results
        )

        # Step 5: Save or update Evaluation record
        eval_record = Evaluation.query.filter_by(submission_id=submission.id).first()
        if not eval_record:
            eval_record = Evaluation(
                submission_id=submission.id,
                total_suggested_marks=total_suggested,
                total_approved_marks=total_suggested, # Initially set to suggested
                max_marks=total_max,
                percentage=percentage,
                status="pending_review",
                overall_feedback=llm_response.get("overall_feedback", "Completed evaluation.")
            )
            db.session.add(eval_record)
            db.session.flush()
        else:
            eval_record.total_suggested_marks = total_suggested
            eval_record.total_approved_marks = total_suggested
            eval_record.max_marks = total_max
            eval_record.percentage = percentage
            eval_record.status = "pending_review"
            eval_record.overall_feedback = llm_response.get("overall_feedback", "Completed evaluation.")
            # Clear old criterion scores and gaps if re-evaluating
            CriterionScore.query.filter_by(evaluation_id=eval_record.id).delete()
            db.session.flush()

        # Step 6: Store criterion-wise scores with evidence and explanations
        for c in processed_criteria:
            cs = CriterionScore(
                evaluation_id=eval_record.id,
                criterion_id=c.get("criterion_id"),
                criterion_name=c.get("criterion_name"),
                max_marks=c.get("max_marks"),
                suggested_marks=c.get("suggested_marks"),
                approved_marks=c.get("approved_marks"),
                status=c.get("status"),
                explanation=c.get("explanation")
            )
            cs.supporting_evidence = c.get("supporting_evidence", [])
            cs.missing_concepts = c.get("missing_concepts", [])
            db.session.add(cs)

        # Step 7: Identify & persist Learning Gaps
        raw_gaps = llm_response.get("learning_gaps", [])
        saved_gaps = LearningGapService.save_learning_gaps(
            evaluation_id=eval_record.id,
            student_id=submission.student_id,
            gaps_data=raw_gaps
        )

        # Step 8: Generate Targeted Practice Questions for identified gaps
        if saved_gaps:
            PracticeService.generate_practice_for_gaps(saved_gaps)

        submission.status = "evaluated"
        db.session.commit()
        return eval_record

    @classmethod
    def teacher_approve_evaluation(
        cls,
        evaluation_id: str,
        teacher_id: str,
        approved_criterion_marks: dict[str, float],
        teacher_notes: str | None = None
    ) -> Evaluation:
        """Teacher review step: overrides marks, adds audit notes, and marks approved."""
        evaluation = Evaluation.query.get_or_404(evaluation_id)
        
        # Update criterion-level approved marks
        for cs in evaluation.criterion_scores:
            if cs.id in approved_criterion_marks:
                new_mark = ScoringService.clamp_mark(approved_criterion_marks[cs.id], cs.max_marks)
                cs.approved_marks = new_mark

        # Re-compute total approved score programmatically
        total_approved, percentage = ScoringService.recalculate_total_from_approved(
            evaluation.criterion_scores,
            evaluation.max_marks
        )
        evaluation.total_approved_marks = total_approved
        evaluation.percentage = percentage
        evaluation.status = "approved"
        evaluation.teacher_notes = teacher_notes or evaluation.teacher_notes
        evaluation.reviewed_at = datetime.utcnow()

        # Update submission status
        evaluation.submission.status = "approved"

        # Audit feedback record
        feedback = TeacherFeedback(
            evaluation_id=evaluation.id,
            teacher_id=teacher_id,
            comments=teacher_notes or "Evaluation approved by teacher.",
            action="approve"
        )
        db.session.add(feedback)
        db.session.commit()
        return evaluation

    @classmethod
    def teacher_reject_evaluation(
        cls,
        evaluation_id: str,
        teacher_id: str,
        reason: str
    ) -> Evaluation:
        """Teacher rejects evaluation for re-evaluation or manual grading."""
        evaluation = Evaluation.query.get_or_404(evaluation_id)
        evaluation.status = "rejected"
        evaluation.teacher_notes = reason
        evaluation.reviewed_at = datetime.utcnow()
        evaluation.submission.status = "rejected"

        feedback = TeacherFeedback(
            evaluation_id=evaluation.id,
            teacher_id=teacher_id,
            comments=reason,
            action="reject"
        )
        db.session.add(feedback)
        db.session.commit()
        return evaluation
