import pytest

from gap_analyzer import (
    build_learning_path,
    build_results,
    classify,
    explain,
    make_concept_score,
    overall_score,
    priority,
    rank_priorities,
)
from models import Concept


def C(cid, prereqs=()):
    return Concept(id=cid, name=cid.title(), prerequisite_ids=list(prereqs))


def chain():
    """prob -> stats -> inference -> ml"""
    return [
        C("prob"),
        C("stats", ["prob"]),
        C("inference", ["stats"]),
        C("ml", ["inference"]),
    ]


def scores(**pairs):
    """scores(prob=(1, 4), stats=(2, 4)) -> list[ConceptScore]"""
    return [make_concept_score(cid, c, t) for cid, (c, t) in pairs.items()]


def plan_example():
    """The worked example from the project plan: 25%, 50%, 75%, 75%."""
    return scores(prob=(1, 4), stats=(2, 4), inference=(3, 4), ml=(3, 4))


# ---------- classify ----------

@pytest.mark.parametrize(
    "score,expected",
    [
        (1.0, "strong"),
        (0.80, "strong"),
        (0.7999, "developing"),
        (0.79, "developing"),
        (0.50, "developing"),
        (0.4999, "weak"),
        (0.49, "weak"),
        (0.0, "weak"),
        (None, "unknown"),
    ],
)
def test_classification_boundaries(score, expected):
    assert classify(score) == expected


def test_exact_fractions_hit_boundaries_correctly():
    assert classify(4 / 5) == "strong"
    assert classify(2 / 4) == "developing"
    assert classify(1 / 3) == "weak"


# ---------- priority formula ----------

@pytest.mark.parametrize(
    "score,descendants,expected",
    [
        (0.25, 3, 1.3125),   # Probability in the plan
        (0.50, 2, 0.75),     # Statistics
        (0.75, 1, 0.3125),   # Statistical Inference
        (0.75, 0, 0.25),     # Machine Learning
        (1.0, 5, 0.0),       # perfect score -> no priority
        (0.0, 3, 1.75),      # zero score -> maximum for 3 descendants
        (0.0, 0, 1.0),
    ],
)
def test_priority_formula(score, descendants, expected):
    assert priority(score, descendants) == pytest.approx(expected)


# ---------- make_concept_score / overall ----------

def test_make_concept_score():
    s = make_concept_score("prob", 1, 4)
    assert s.score == 0.25 and s.classification == "weak"


def test_zero_questions_is_unassessed_not_zero():
    s = make_concept_score("x", 0, 0)
    assert s.score is None and s.classification == "unknown"


def test_overall_score():
    assert overall_score(plan_example()) == pytest.approx(9 / 16)


def test_overall_score_with_no_questions():
    assert overall_score([]) == 0.0
    assert overall_score([make_concept_score("x", 0, 0)]) == 0.0


# ---------- rank_priorities ----------

def test_rank_priorities_matches_the_plan():
    ranked = rank_priorities(plan_example(), chain())
    assert [cid for cid, _ in ranked] == ["prob", "stats", "inference", "ml"]
    values = dict(ranked)
    assert values["prob"] == pytest.approx(1.3125)
    assert values["stats"] == pytest.approx(0.75)
    assert values["inference"] == pytest.approx(0.3125)
    assert values["ml"] == pytest.approx(0.25)


def test_unassessed_concepts_are_not_ranked():
    ranked = rank_priorities(scores(prob=(1, 4)), chain())
    assert [cid for cid, _ in ranked] == ["prob"]


def test_scores_for_unknown_concepts_are_ignored():
    ranked = rank_priorities(scores(prob=(1, 4), ghost=(0, 4)), chain())
    assert [cid for cid, _ in ranked] == ["prob"]


# ---------- build_learning_path ----------

def test_plan_example_path_order_and_positions():
    path = build_learning_path(plan_example(), chain())
    assert [r.concept_id for r in path] == ["prob", "stats", "inference", "ml"]
    assert [r.position for r in path] == [1, 2, 3, 4]
    assert path[0].descendant_count == 3
    assert path[0].classification == "weak"
    assert path[0].priority == pytest.approx(1.3125)


def test_strong_concepts_are_left_out():
    s = scores(prob=(4, 4), stats=(1, 4), inference=(3, 4), ml=(4, 4))
    path = build_learning_path(s, chain())
    assert [r.concept_id for r in path] == ["stats", "inference"]
    assert [r.position for r in path] == [1, 2]


def test_unassessed_concepts_are_left_out_of_path():
    path = build_learning_path(scores(prob=(1, 4)), chain())
    assert [r.concept_id for r in path] == ["prob"]


def test_dependent_never_precedes_prerequisite_even_with_higher_priority():
    # b (score 0, no descendants) has priority 1.0; a (score 0.75, 1 descendant) only 0.3125
    concepts = [C("a"), C("b", ["a"])]
    path = build_learning_path(scores(a=(3, 4), b=(0, 4)), concepts)
    assert [r.concept_id for r in path] == ["a", "b"]


def test_prerequisite_order_holds_when_a_strong_concept_sits_in_between():
    # stats is strong and skipped, but ml (depends on stats) must still follow prob
    concepts = [C("prob"), C("stats", ["prob"]), C("ml", ["stats"])]
    path = build_learning_path(scores(prob=(0, 4), stats=(4, 4), ml=(0, 4)), concepts)
    assert [r.concept_id for r in path] == ["prob", "ml"]


def test_higher_priority_goes_first_between_independent_concepts():
    concepts = [C("x"), C("y")]
    path = build_learning_path(scores(x=(3, 4), y=(0, 4)), concepts)
    assert [r.concept_id for r in path] == ["y", "x"]


def test_all_correct_gives_empty_path():
    s = scores(prob=(4, 4), stats=(4, 4), inference=(4, 4), ml=(4, 4))
    assert build_learning_path(s, chain()) == []


def test_all_wrong_includes_everything_in_prerequisite_order():
    s = scores(prob=(0, 4), stats=(0, 4), inference=(0, 4), ml=(0, 4))
    path = build_learning_path(s, chain())
    assert [r.concept_id for r in path] == ["prob", "stats", "inference", "ml"]
    assert all(r.classification == "weak" for r in path)


def test_disconnected_components():
    concepts = chain() + [C("alg"), C("deriv", ["alg"])]
    s = scores(prob=(1, 4), alg=(0, 4), deriv=(1, 4))
    path = build_learning_path(s, concepts)
    ids = [r.concept_id for r in path]
    assert set(ids) == {"prob", "alg", "deriv"}
    assert ids.index("alg") < ids.index("deriv")


def test_multi_path_descendant_counted_once():
    # diamond: a -> b, a -> c, b -> d, c -> d
    concepts = [C("a"), C("b", ["a"]), C("c", ["a"]), C("d", ["b", "c"])]
    path = build_learning_path(scores(a=(0, 4)), concepts)
    assert path[0].descendant_count == 3


def test_cyclic_graph_raises():
    with pytest.raises(ValueError):
        build_learning_path(scores(a=(0, 4)), [C("a", ["b"]), C("b", ["a"])])


# ---------- explanations ----------

def test_weak_explanation_is_grounded_and_cautious():
    path = build_learning_path(plan_example(), chain())
    text = path[0].explanation
    assert "potential gap" in text
    assert "Prob" in text
    assert "25%" in text
    assert "3 other concepts" in text
    assert "Stats" in text          # named direct dependent
    assert "1.31" in text           # priority 1.3125 to 2 decimals


def test_developing_explanation_does_not_claim_a_gap():
    text = build_learning_path(plan_example(), chain())[1].explanation
    assert "potential gap" not in text
    assert "50%" in text


def test_leaf_concept_explanation_makes_no_dependent_claims():
    text = build_learning_path(plan_example(), chain())[-1].explanation
    assert "No other concepts in your graph depend on it" in text
    assert "including" not in text


def test_singular_wording_for_one_dependent():
    text = explain("Inference", 0.75, "developing", 1, 0.3125, ["Ml"])
    assert "1 other concept in your graph" in text
    assert "concepts" not in text


def test_explanation_lists_at_most_three_dependents():
    text = explain("Root", 0.0, "weak", 5, 2.25, ["A", "B", "C", "D", "E"])
    assert "A, B and C" in text
    assert "D" not in text.replace("Root", "").replace("depend", "")


# ---------- build_results ----------

def test_build_results_bundles_everything():
    r = build_results("s1", plan_example(), chain())
    assert r.session_id == "s1"
    assert r.overall_score == pytest.approx(9 / 16)
    assert len(r.concept_scores) == 4
    assert [x.concept_id for x in r.recommendations][0] == "prob"
    assert "preliminary" in r.disclaimer