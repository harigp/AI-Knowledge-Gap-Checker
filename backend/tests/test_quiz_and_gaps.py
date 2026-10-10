import pytest

from app.errors import InvalidInputError
from app.services import gap_service, quiz_service
from app.services.gap_service import GapConfig
from app.services.learning_path_service import build_learning_path
from app.services.session_service import StoredQuestion

CFG = GapConfig()


def c(cid, *prereqs):
    return {"id": cid, "name": cid.replace("_", " ").title(), "description": "d", "difficulty": "beginner",
            "prerequisites": list(prereqs), "source_type": "document"}


# probability -> statistics -> regression ; probability -> bayes ; isolated "trivia"
CONCEPTS = [c("probability"), c("statistics", "probability"), c("regression", "statistics"),
            c("bayes", "probability"), c("trivia")]


def questions():
    qs = []
    n = 1
    for cid in ["probability", "statistics", "regression", "trivia"]:
        for _ in range(2):
            qs.append(StoredQuestion(id=f"q{n}", concept_id=cid, question=f"Q{n}?", options=["w", "x", "y", "z"],
                                     correct_index=1, explanation="because"))
            n += 1
    return qs


def answer_all(correct_map):
    """correct_map: concept_id -> number of its 2 questions answered correctly."""
    answers = []
    for q in questions():
        right = correct_map.get(q.concept_id, 2) > 0
        if right:
            correct_map[q.concept_id] = correct_map.get(q.concept_id, 2) - 1
        answers.append((q.id, "B" if right else "A"))
    return answers


# --------------------------------------------------------------------------- grading
def test_all_correct():
    r = quiz_service.grade(questions(), [(q.id, "B") for q in questions()])
    assert r.total_correct == 8 and r.total_questions == 8 and r.overall_score == 1.0
    assert all(res["is_correct"] for res in r.question_results)


def test_incorrect_answers():
    r = quiz_service.grade(questions(), [(q.id, "C") for q in questions()])
    assert r.total_correct == 0 and r.overall_score == 0.0
    assert r.question_results[0]["correct_option_id"] == "B"
    assert r.question_results[0]["selected_option_id"] == "C"


def test_missing_answers_count_as_unanswered():
    r = quiz_service.grade(questions(), [("q1", "B")])
    assert r.unanswered_count == 7 and r.total_correct == 1
    assert r.question_results[1]["selected_option_id"] is None
    assert r.question_results[1]["is_correct"] is False


def test_invalid_question_id():
    with pytest.raises(InvalidInputError) as e:
        quiz_service.grade(questions(), [("q999", "A")])
    assert e.value.code == "invalid_question_id"
    assert e.value.details["invalid_question_ids"] == ["q999"]


def test_duplicate_answer():
    with pytest.raises(InvalidInputError) as e:
        quiz_service.grade(questions(), [("q1", "A"), ("q1", "B")])
    assert e.value.code == "duplicate_answer"


def test_concept_level_tallies():
    r = quiz_service.grade(questions(), answer_all({"probability": 1, "statistics": 0}))
    assert r.concept_tallies["probability"] == (1, 2)
    assert r.concept_tallies["statistics"] == (0, 2)
    assert r.concept_tallies["regression"] == (2, 2)
    assert "bayes" not in r.concept_tallies


def test_public_questions_hide_answers():
    payload = quiz_service.public_questions(questions(), CONCEPTS)
    text = repr(payload)
    assert "correct" not in text and "because" not in text
    assert [o["id"] for o in payload[0]["options"]] == ["A", "B", "C", "D"]


def test_select_quiz_concepts_prefers_foundational():
    chosen = quiz_service.select_quiz_concepts(CONCEPTS, min_count=2, max_count=2)
    assert [x["id"] for x in chosen] == ["probability", "statistics"]


# --------------------------------------------------------------------------- mastery & priority
@pytest.mark.parametrize("score,expected", [(1.0, "strong"), (0.8, "strong"), (0.79, "developing"),
                                            (0.5, "developing"), (0.49, "weak"), (0.0, "weak"),
                                            (None, "unassessed")])
def test_classification(score, expected):
    assert gap_service.classify(score, CFG) == expected


def test_priority_formula():
    assert gap_service.priority(0.0, 3, CFG) == 1.75
    assert gap_service.priority(0.5, 0, CFG) == 0.5
    assert gap_service.priority(0.25, 2, CFG) == pytest.approx(0.75 * 1.5)
    assert gap_service.priority(0.5, 2, GapConfig(descendant_weight=1.0)) == 1.5


def run(correct_map):
    graded = quiz_service.grade(questions(), answer_all(dict(correct_map)))
    analysis = gap_service.analyze(CONCEPTS, graded.concept_tallies, CFG)
    return analysis, build_learning_path(CONCEPTS, analysis)


def test_weak_foundational_concept_ranks_first():
    analysis, path = run({"probability": 0, "trivia": 0})
    gaps = analysis.learning_gaps
    assert [g["concept_id"] for g in gaps] == ["probability", "trivia"]
    prob = gaps[0]
    assert prob["descendant_count"] == 3
    assert prob["priority"] == 1.75
    assert set(prob["downstream_concept_ids"]) == {"statistics", "regression", "bayes"}
    assert "0 of 2" in prob["reason"] and "1.75" in prob["reason"] and "Statistics" in prob["reason"]


def test_weak_isolated_concept():
    analysis, path = run({"trivia": 0})
    assert len(analysis.learning_gaps) == 1
    gap = analysis.learning_gaps[0]
    assert gap["concept_id"] == "trivia" and gap["descendant_count"] == 0 and gap["priority"] == 1.0
    assert "No other concepts" in gap["reason"]
    assert [s["concept_id"] for s in path["steps"]] == ["trivia"]


def test_all_strong():
    analysis, path = run({})
    assert analysis.learning_gaps == [] and analysis.recommendations == []
    assert path["total_steps"] == 0 and "No knowledge gaps" in path["summary"]


def test_all_weak_path_respects_prerequisites():
    analysis, path = run({"probability": 0, "statistics": 0, "regression": 0, "trivia": 0})
    order = [s["concept_id"] for s in path["steps"]]
    assert order.index("probability") < order.index("statistics") < order.index("regression")
    # bayes is unassessed but not a prerequisite of any gap -> not recommended
    assert "bayes" not in order
    # probability (1.75) outranks trivia (1.0) among the initially ready concepts
    assert order[0] == "probability"
    stats = next(s for s in path["steps"] if s["concept_id"] == "statistics")
    assert stats["prerequisites_in_path"] == ["probability"]


def test_unassessed_concepts_not_scored_zero():
    analysis, _ = run({"statistics": 0})
    scores = {s["concept_id"]: s for s in analysis.concept_scores}
    assert scores["bayes"]["score"] is None and scores["bayes"]["mastery"] == "unassessed"
    assert scores["bayes"]["total"] == 0


def test_unassessed_prerequisite_of_gap_is_verified_first():
    concepts = [c("base"), c("mid", "base"), c("top", "mid")]
    tallies = {"mid": (2, 2), "top": (0, 2)}  # base unassessed, mid strong, top weak
    analysis = gap_service.analyze(concepts, tallies, CFG)
    recs = analysis.recommendations
    assert [(r["concept_id"], r["action"]) for r in recs] == [("top", "review"), ("base", "verify")]
    path = build_learning_path(concepts, analysis)
    # base is a (transitive) prerequisite of top, so it must come first despite lower rank
    assert [s["concept_id"] for s in path["steps"]] == ["base", "top"]
    assert path["steps"][1]["prerequisites_in_path"] == ["base"]
    assert "mid" not in [s["concept_id"] for s in path["steps"]]  # strong concepts skipped


def test_path_is_not_just_priority_sorted():
    # dependent has higher priority than its prerequisite, yet must come after it
    concepts = [c("pre"), c("dep", "pre"), c("d2", "dep"), c("d3", "dep")]
    tallies = {"pre": (1, 2), "dep": (0, 2)}
    analysis = gap_service.analyze(concepts, tallies, CFG)
    assert analysis.learning_gaps[0]["concept_id"] == "dep"  # priority 1.5 vs pre 0.5*1.75=0.875
    path = build_learning_path(concepts, analysis)
    assert [s["concept_id"] for s in path["steps"]] == ["pre", "dep"]


def test_tie_break_by_priority_among_ready_concepts():
    concepts = [c("a"), c("b"), c("a_child", "a")]
    tallies = {"a": (1, 2), "b": (0, 2)}  # a: 0.5*1.25=0.625 ; b: 1.0
    analysis = gap_service.analyze(concepts, tallies, CFG)
    path = build_learning_path(concepts, analysis)
    assert [s["concept_id"] for s in path["steps"]] == ["b", "a"]
