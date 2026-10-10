"""Public API schemas (request/response models). These define the frontend contract.

Field names are snake_case. Do not change these without updating API_CONTRACT.md and
notifying the frontend team.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["beginner", "intermediate", "advanced"]
SourceType = Literal["document", "inferred"]
Mastery = Literal["strong", "developing", "weak", "unassessed"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class ErrorDetail(_Model):
    code: str = Field(examples=["session_not_found"])
    message: str = Field(examples=["Session not found or expired. Upload the document again."])
    details: dict | None = None


class ErrorResponse(_Model):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(_Model):
    status: Literal["ok"]
    service: str
    version: str
    ai_configured: bool
    timestamp: datetime


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class Concept(_Model):
    id: str = Field(description="Stable snake_case identifier.", examples=["probability"])
    name: str = Field(examples=["Probability"])
    description: str
    difficulty: Difficulty
    prerequisites: list[str] = Field(description="IDs of concepts that must be understood first.")
    source_type: SourceType = Field(
        description="'document' = covered in the uploaded notes; 'inferred' = assumed prior knowledge."
    )
    descendant_count: int = Field(description="Number of unique concepts that depend on this one (directly "
                                              "or indirectly).")
    level: int = Field(description="Longest prerequisite chain length from a root concept (roots are 0). "
                                   "Useful for layered layouts.")


class Edge(_Model):
    id: str = Field(examples=["probability->statistics"])
    source: str = Field(description="Prerequisite concept ID.", examples=["probability"])
    target: str = Field(description="Dependent concept ID.", examples=["statistics"])
    relationship: Literal["prerequisite"] = "prerequisite"


class ProcessingStatus(_Model):
    status: Literal["completed"]
    processing_mode: Literal["direct", "chunked"]
    page_count: int
    estimated_tokens: int
    chunk_count: int
    concept_count: int
    ai_requests_used: int
    quiz_status: Literal["pending", "ready"] = Field(
        description="'pending' = quiz will be generated on first GET /api/quiz/{session_id}."
    )
    warnings: list[str] = Field(default_factory=list,
                                description="Non-fatal adjustments made while validating AI output.")


class AnalyzeResponse(_Model):
    session_id: str
    document_name: str
    concepts: list[Concept]
    edges: list[Edge]
    topological_order: list[str] = Field(description="Concept IDs in prerequisite-first order.")
    processing_status: ProcessingStatus
    expires_at: datetime


class GraphResponse(_Model):
    session_id: str
    document_name: str
    concepts: list[Concept]
    edges: list[Edge]
    topological_order: list[str]


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
class QuizOption(_Model):
    id: Literal["A", "B", "C", "D"]
    text: str


class QuizQuestion(_Model):
    """A question as shown to the student. Never contains the answer or explanation."""

    id: str = Field(examples=["q1"])
    concept_id: str
    concept_name: str
    question: str
    options: list[QuizOption] = Field(min_length=4, max_length=4)


class QuizResponse(_Model):
    session_id: str
    total_questions: int
    assessed_concept_ids: list[str]
    submitted: bool
    questions: list[QuizQuestion]


class AnswerSubmission(_Model):
    question_id: str = Field(min_length=1, max_length=20, examples=["q1"])
    selected_option_id: Literal["A", "B", "C", "D"]


class QuizSubmitRequest(_Model):
    answers: list[AnswerSubmission] = Field(max_length=100)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
class QuestionResult(_Model):
    question_id: str
    concept_id: str
    question: str
    selected_option_id: str | None = Field(description="null if the question was left unanswered.")
    correct_option_id: str
    is_correct: bool
    explanation: str


class ConceptScore(_Model):
    concept_id: str
    concept_name: str
    correct: int
    total: int
    score: float | None = Field(description="correct/total in [0,1]; null when unassessed.")
    mastery: Mastery


class LearningGap(_Model):
    concept_id: str
    concept_name: str
    score: float
    mastery: Literal["weak", "developing"]
    descendant_count: int
    downstream_concept_ids: list[str]
    priority: float = Field(description="(1 - score) * (1 + weight * descendant_count)")
    reason: str


class Recommendation(_Model):
    rank: int
    concept_id: str
    concept_name: str
    action: Literal["review", "verify"] = Field(
        description="'review' = assessed as weak/developing; 'verify' = unassessed prerequisite of a gap."
    )
    score: float | None
    mastery: Mastery
    descendant_count: int
    priority: float | None
    reason: str


class LearningPathStep(_Model):
    step: int
    concept_id: str
    concept_name: str
    action: Literal["review", "verify"]
    mastery: Mastery
    score: float | None
    priority: float | None
    prerequisites_in_path: list[str] = Field(description="Earlier steps this step builds on.")
    reason: str


class LearningPath(_Model):
    total_steps: int
    summary: str
    steps: list[LearningPathStep]


class AssessmentResults(_Model):
    session_id: str
    submitted_at: datetime
    overall_score: float
    total_correct: int
    total_questions: int
    unanswered_count: int
    concept_scores: list[ConceptScore]
    question_results: list[QuestionResult]
    learning_gaps: list[LearningGap]
    recommendations: list[Recommendation]
    learning_path: LearningPath
