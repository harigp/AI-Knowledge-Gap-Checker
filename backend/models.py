"""
models.py: the shared data contract for ConceptGraph AI.

Rules:
- Models only. No logic beyond simple field validation.
- Everyone imports from here. Change it only with the team's agreement.
- Correct answers live ONLY in QuizQuestionPrivate. Never return that to the frontend.

Graph direction: an edge A -> B means "A is a prerequisite for B".
Each Concept stores its own prerequisite_ids (the incoming edges).
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------- Shared types ----------

Difficulty = Literal["beginner", "intermediate", "advanced"]
SourceType = Literal["direct", "inferred"]  # in the notes vs. inferred prerequisite
Classification = Literal["strong", "developing", "weak", "unknown"]
SessionStatus = Literal["created", "graph_ready", "quiz_ready", "completed", "failed"]


# ---------- Concepts / graph ----------

class Concept(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    difficulty: Difficulty = "intermediate"
    source_type: SourceType = "direct"
    prerequisite_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def no_self_dependency(self):
        if self.id in self.prerequisite_ids:
            raise ValueError(f"Concept '{self.id}' cannot be its own prerequisite")
        return self
    # Cycles, duplicate IDs, and missing prerequisites need the WHOLE graph,
    # so those checks belong in graph_engine.validate_graph, not here.


class GraphResponse(BaseModel):
    session_id: str
    document_name: str
    concepts: list[Concept]


class AnalyzeResponse(BaseModel):
    session_id: str
    document_name: str
    status: SessionStatus
    concepts: list[Concept]


# ---------- Quiz ----------

class QuizQuestion(BaseModel):
    """Public version. Safe to send to the frontend (no answer)."""
    id: str
    concept_id: str
    question: str
    options: list[str]
    explanation: str = ""  # sent after submission only; blank this out in GET /quiz

    @field_validator("options")
    @classmethod
    def exactly_four_options(cls, v: list[str]):
        if len(v) != 4:
            raise ValueError("Each question must have exactly 4 options")
        return v


class QuizQuestionPrivate(QuizQuestion):
    """Backend-only version. Includes the answer key."""
    correct_index: int = Field(ge=0, le=3)  # index into options

    def to_public(self) -> QuizQuestion:
        # Strip the answer AND the explanation before sending to the client
        return QuizQuestion(
            id=self.id,
            concept_id=self.concept_id,
            question=self.question,
            options=self.options,
            explanation="",
        )


class QuizResponse(BaseModel):
    session_id: str
    questions: list[QuizQuestion]


class SubmitRequest(BaseModel):
    # session_id comes from the URL: POST /api/quiz/{sessionId}/submit
    answers: dict[str, int]  # question_id -> chosen option index (0-3)

    @field_validator("answers")
    @classmethod
    def valid_indices(cls, v: dict[str, int]):
        for qid, idx in v.items():
            if not 0 <= idx <= 3:
                raise ValueError(f"Answer for '{qid}' must be between 0 and 3")
        return v


# ---------- Results ----------

class ConceptScore(BaseModel):
    concept_id: str
    correct: int = Field(ge=0)
    total: int = Field(ge=0)
    score: float | None = Field(default=None, ge=0, le=1)  # None = unassessed
    classification: Classification = "unknown"


class LearningRecommendation(BaseModel):
    concept_id: str
    concept_name: str
    score: float = Field(ge=0, le=1)
    classification: Classification
    descendant_count: int = Field(ge=0)
    priority: float = Field(ge=0)
    explanation: str  # built from real numbers by a template, not by an LLM
    position: int = Field(ge=1)  # 1-based spot in the study order


class ResultsResponse(BaseModel):
    session_id: str
    overall_score: float = Field(ge=0, le=1)
    concept_scores: list[ConceptScore]
    recommendations: list[LearningRecommendation]  # already in prerequisite-safe order
    disclaimer: str = (
        "Estimates are based on a short diagnostic quiz and are preliminary."
    )


# ---------- Session (backend-internal) ----------

class LearningSession(BaseModel):
    id: str
    document_name: str
    file_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: SessionStatus = "created"
    concepts: list[Concept] = Field(default_factory=list)
    questions: list[QuizQuestionPrivate] = Field(default_factory=list)
    results: ResultsResponse | None = None