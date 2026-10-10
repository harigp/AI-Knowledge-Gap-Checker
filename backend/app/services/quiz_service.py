"""Quiz concept selection, safe question payloads, and grading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.errors import InvalidInputError
from app.services import graph_service
from app.services.ai_service import GeneratedQuestion
from app.services.session_service import StoredQuestion

OPTION_IDS = ["A", "B", "C", "D"]


def select_quiz_concepts(concepts: list[dict[str, Any]], min_count: int, max_count: int) -> list[dict[str, Any]]:
    """Pick the concepts with the most downstream dependents (most diagnostic value).

    Ties break by prerequisite-first order. Returns all concepts if there are fewer than min_count.
    """
    desc = graph_service.descendants(concepts)
    order = {cid: i for i, cid in enumerate(graph_service.topological_sort(concepts))}
    ranked = sorted(concepts, key=lambda c: (-len(desc[c["id"]]), order[c["id"]]))
    count = len(concepts) if len(concepts) <= min_count else min(max_count, len(concepts))
    chosen = {c["id"] for c in ranked[:count]}
    return sorted((c for c in concepts if c["id"] in chosen), key=lambda c: order[c["id"]])


def store_questions(generated: list[GeneratedQuestion]) -> list[StoredQuestion]:
    return [StoredQuestion(id=f"q{i}", concept_id=q.concept_id, question=q.question, options=list(q.options),
                           correct_index=q.correct_index, explanation=q.explanation)
            for i, q in enumerate(generated, start=1)]


def public_questions(questions: list[StoredQuestion], concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Question payloads WITHOUT correct answers or explanations."""
    names = {c["id"]: c["name"] for c in concepts}
    return [{
        "id": q.id,
        "concept_id": q.concept_id,
        "concept_name": names.get(q.concept_id, q.concept_id),
        "question": q.question,
        "options": [{"id": OPTION_IDS[i], "text": text} for i, text in enumerate(q.options)],
    } for q in questions]


@dataclass
class GradeResult:
    question_results: list[dict[str, Any]]
    concept_tallies: dict[str, tuple[int, int]]  # concept_id -> (correct, total)
    total_correct: int
    total_questions: int
    unanswered_count: int

    @property
    def overall_score(self) -> float:
        return round(self.total_correct / self.total_questions, 4) if self.total_questions else 0.0


def grade(questions: list[StoredQuestion], answers: list[tuple[str, str]]) -> GradeResult:
    """Grade (question_id, option_id) pairs. Unanswered questions count as incorrect.

    Raises InvalidInputError for unknown or duplicate question IDs.
    """
    by_id = {q.id: q for q in questions}
    selected: dict[str, str] = {}
    duplicates: list[str] = []
    for qid, option in answers:
        if qid in selected:
            duplicates.append(qid)
        selected[qid] = option
    invalid = sorted({qid for qid, _ in answers if qid not in by_id})
    if invalid:
        raise InvalidInputError("Some answers reference questions that are not in this quiz.",
                                code="invalid_question_id", details={"invalid_question_ids": invalid})
    if duplicates:
        raise InvalidInputError("Each question may only be answered once.", code="duplicate_answer",
                                details={"question_ids": sorted(set(duplicates))})

    results = []
    tallies: dict[str, tuple[int, int]] = {}
    total_correct = 0
    for q in questions:
        choice = selected.get(q.id)
        correct_id = OPTION_IDS[q.correct_index]
        is_correct = choice == correct_id
        total_correct += is_correct
        c, t = tallies.get(q.concept_id, (0, 0))
        tallies[q.concept_id] = (c + is_correct, t + 1)
        results.append({
            "question_id": q.id,
            "concept_id": q.concept_id,
            "question": q.question,
            "selected_option_id": choice,
            "correct_option_id": correct_id,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })
    return GradeResult(results, tallies, total_correct, len(questions),
                       sum(1 for q in questions if q.id not in selected))
