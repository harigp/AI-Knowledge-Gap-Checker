import pytest
from pydantic import ValidationError

from models import (
    Concept,
    ConceptScore,
    LearningSession,
    QuizQuestion,
    QuizQuestionPrivate,
    SubmitRequest,
)


def make_private(**overrides):
    data = dict(
        id="q1",
        concept_id="prob",
        question="P(even) on a fair die?",
        options=["1/6", "1/3", "1/2", "2/3"],
        explanation="3 of 6 faces are even.",
        correct_index=2,
    )
    data.update(overrides)
    return QuizQuestionPrivate(**data)


# ---------- Concept ----------

def test_valid_concept_uses_defaults():
    c = Concept(id="prob", name="Probability")
    assert c.prerequisite_ids == []
    assert c.difficulty == "intermediate"
    assert c.source_type == "direct"


def test_concept_rejects_self_dependency():
    with pytest.raises(ValidationError):
        Concept(id="a", name="A", prerequisite_ids=["a"])


def test_concept_rejects_empty_id_or_name():
    with pytest.raises(ValidationError):
        Concept(id="", name="A")
    with pytest.raises(ValidationError):
        Concept(id="a", name="")


def test_concept_rejects_bad_difficulty():
    with pytest.raises(ValidationError):
        Concept(id="a", name="A", difficulty="impossible")


def test_concepts_do_not_share_default_prerequisite_list():
    a = Concept(id="a", name="A")
    b = Concept(id="b", name="B")
    a.prerequisite_ids.append("x")
    assert b.prerequisite_ids == []


# ---------- Quiz questions ----------

def test_question_requires_exactly_four_options():
    for opts in (["a", "b", "c"], ["a", "b", "c", "d", "e"]):
        with pytest.raises(ValidationError):
            QuizQuestion(id="q", concept_id="c", question="?", options=opts)


def test_private_question_correct_index_must_be_0_to_3():
    for bad in (-1, 4):
        with pytest.raises(ValidationError):
            make_private(correct_index=bad)


def test_to_public_strips_answer_and_explanation():
    public = make_private().to_public()
    dumped = public.model_dump()
    assert "correct_index" not in dumped
    assert dumped["explanation"] == ""
    assert type(public) is QuizQuestion


def test_public_json_never_contains_answer_key():
    """The most important security test: nothing answer-related can leak."""
    json_str = make_private().to_public().model_dump_json()
    assert "correct" not in json_str


# ---------- Submit request ----------

def test_submit_accepts_valid_answers():
    req = SubmitRequest(answers={"q1": 0, "q2": 3})
    assert req.answers["q2"] == 3


def test_submit_rejects_out_of_range_answers():
    for bad in (-1, 4, 99):
        with pytest.raises(ValidationError):
            SubmitRequest(answers={"q1": bad})


def test_submit_accepts_empty_answers():
    # Missing answers are handled by the grader, not the model
    assert SubmitRequest(answers={}).answers == {}


# ---------- Scores ----------

def test_unassessed_concept_score_is_none_not_zero():
    s = ConceptScore(concept_id="x", correct=0, total=0)
    assert s.score is None
    assert s.classification == "unknown"


def test_score_must_be_between_0_and_1():
    for bad in (-0.1, 1.5):
        with pytest.raises(ValidationError):
            ConceptScore(concept_id="x", correct=1, total=2, score=bad)


# ---------- Session / serialization ----------

def test_session_defaults():
    s = LearningSession(id="s1", document_name="notes.pdf")
    assert s.status == "created"
    assert s.concepts == [] and s.questions == [] and s.results is None
    assert s.created_at.tzinfo is not None  # timezone-aware


def test_concept_round_trips_through_json():
    c = Concept(id="stats", name="Statistics", prerequisite_ids=["prob"])
    assert Concept.model_validate_json(c.model_dump_json()) == c