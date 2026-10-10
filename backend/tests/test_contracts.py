"""Guards the shared contract files: they must stay valid, consistent, and answer-free."""

import json
from pathlib import Path

import pytest

from gap_analyzer import build_results
from graph_engine import validate_graph
from models import (
    AnalyzeResponse,
    GraphResponse,
    QuizQuestionPrivate,
    QuizResponse,
    ResultsResponse,
    SubmitRequest,
)

BACKEND = Path(__file__).resolve().parents[1]
CONTRACTS = BACKEND.parent / "contracts"
PRIVATE_QUIZ = BACKEND / "tests" / "fixtures" / "mock_quiz_private.json"

HINT = "Run `python make_contracts.py` from backend/ to regenerate."


def load(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def graph():
    return GraphResponse.model_validate(load("mock_graph.json"))


@pytest.fixture(scope="module")
def quiz():
    return QuizResponse.model_validate(load("mock_quiz.json"))


@pytest.fixture(scope="module")
def results():
    return ResultsResponse.model_validate(load("mock_results.json"))


# ---------- every file matches its model ----------

@pytest.mark.parametrize(
    "filename,model",
    [
        ("mock_analyze.json", AnalyzeResponse),
        ("mock_graph.json", GraphResponse),
        ("mock_quiz.json", QuizResponse),
        ("mock_submit_request.json", SubmitRequest),
        ("mock_results.json", ResultsResponse),
    ],
)
def test_contract_file_matches_its_model(filename, model):
    model.model_validate(load(filename))  # raises if the shape drifted: HINT


# ---------- graph ----------

def test_graph_is_a_valid_dag(graph):
    assert validate_graph(graph.concepts) == []


def test_analyze_and_graph_agree(graph):
    analyze = AnalyzeResponse.model_validate(load("mock_analyze.json"))
    assert analyze.concepts == graph.concepts
    assert analyze.session_id == graph.session_id


def test_graph_size_is_within_spec(graph):
    assert 8 <= len(graph.concepts) <= 12


# ---------- quiz ----------

def test_public_quiz_contains_no_answer_keys():
    raw = (CONTRACTS / "mock_quiz.json").read_text(encoding="utf-8")
    assert "correct" not in raw
    assert all(q["explanation"] == "" for q in json.loads(raw)["questions"])


def test_quiz_questions_reference_real_concepts(graph, quiz):
    ids = {c.id for c in graph.concepts}
    assert all(q.concept_id in ids for q in quiz.questions)


def test_quiz_size_is_within_spec(quiz):
    assert 8 <= len(quiz.questions) <= 12


def test_private_fixture_matches_public_quiz(quiz):
    private = [QuizQuestionPrivate.model_validate(q) for q in json.loads(PRIVATE_QUIZ.read_text(encoding="utf-8"))]
    assert [q.to_public() for q in private] == quiz.questions
    assert all(q.explanation for q in private)  # explanations exist backend-side


# ---------- submit + results ----------

def test_submitted_answers_reference_real_questions(quiz):
    answers = SubmitRequest.model_validate(load("mock_submit_request.json")).answers
    assert set(answers) <= {q.id for q in quiz.questions}


def test_results_cover_every_concept_exactly_once(graph, results):
    assert [s.concept_id for s in results.concept_scores] == [c.id for c in graph.concepts]


def test_unassessed_concepts_have_null_score(graph, results):
    quizzed = {q.concept_id for q in QuizResponse.model_validate(load("mock_quiz.json")).questions}
    for s in results.concept_scores:
        if s.concept_id in quizzed:
            assert s.score is not None
        else:
            assert s.score is None and s.classification == "unknown" and s.total == 0


def test_results_match_what_the_algorithms_produce(graph, results):
    """If gap_analyzer or graph_engine changes behavior, the contract must be regenerated."""
    recomputed = build_results(results.session_id, results.concept_scores, graph.concepts)
    assert recomputed == results, HINT


def test_demo_story_has_all_three_colors(results):
    kinds = {s.classification for s in results.concept_scores}
    assert {"strong", "developing", "weak", "unknown"} <= kinds


def test_study_path_starts_with_the_foundational_gap(results):
    first = results.recommendations[0]
    assert first.concept_id == "probability"
    assert first.classification == "weak"
    assert first.descendant_count == 3
    assert [r.position for r in results.recommendations] == list(range(1, len(results.recommendations) + 1))