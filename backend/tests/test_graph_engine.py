import pytest

from graph_engine import (
    build_adjacency,
    count_descendants,
    find_cycle,
    get_descendants,
    topological_order,
    validate_graph,
)
from models import Concept


def C(cid, prereqs=()):
    return Concept(id=cid, name=cid.title(), prerequisite_ids=list(prereqs))


def chain():
    """prob -> stats -> inference -> ml  (the worked example from the plan)"""
    return [
        C("prob"),
        C("stats", ["prob"]),
        C("inference", ["stats"]),
        C("ml", ["inference"]),
    ]


def diamond():
    """a -> b, a -> c, b -> d, c -> d"""
    return [C("a"), C("b", ["a"]), C("c", ["a"]), C("d", ["b", "c"])]


# ---------- validate_graph ----------

def test_valid_graph_has_no_errors():
    assert validate_graph(chain()) == []
    assert validate_graph(diamond()) == []


def test_empty_graph_is_valid():
    assert validate_graph([]) == []


def test_duplicate_ids_detected():
    errors = validate_graph([C("a"), C("a")])
    assert any("Duplicate concept id 'a'" in e for e in errors)


def test_missing_prerequisite_detected():
    errors = validate_graph([C("a", ["ghost"])])
    assert any("unknown prerequisite 'ghost'" in e for e in errors)


def test_self_loop_detected():
    # model_construct bypasses the Concept validator so we can test the engine itself
    bad = Concept.model_construct(
        id="a", name="A", description="", difficulty="intermediate",
        source_type="direct", prerequisite_ids=["a"],
    )
    errors = validate_graph([bad])
    assert any("itself" in e for e in errors)


def test_duplicate_edge_detected():
    errors = validate_graph([C("a"), C("b", ["a", "a"])])
    assert any("'a' 2 times" in e for e in errors)


def test_three_node_cycle_detected():
    errors = validate_graph([C("a", ["c"]), C("b", ["a"]), C("c", ["b"])])
    assert any("Circular dependency" in e for e in errors)


def test_multiple_problems_all_reported():
    errors = validate_graph([C("a", ["ghost"]), C("a")])
    assert len(errors) >= 2


# ---------- find_cycle ----------

def test_find_cycle_returns_none_for_dag():
    assert find_cycle(diamond()) is None


def test_find_cycle_returns_the_cycle_members():
    cycle = find_cycle([C("a", ["c"]), C("b", ["a"]), C("c", ["b"]), C("x")])
    assert set(cycle) == {"a", "b", "c"}  # x is not part of it


def test_two_node_cycle():
    cycle = find_cycle([C("a", ["b"]), C("b", ["a"])])
    assert set(cycle) == {"a", "b"}


# ---------- adjacency ----------

def test_build_adjacency_points_prerequisite_to_dependents():
    adj = build_adjacency(chain())
    assert adj["prob"] == ["stats"]
    assert adj["ml"] == []


def test_build_adjacency_ignores_missing_and_duplicate_edges():
    adj = build_adjacency([C("a"), C("b", ["a", "a", "ghost"])])
    assert adj == {"a": ["b"], "b": []}


# ---------- descendants ----------

def test_chain_descendant_counts_match_the_plan():
    counts = count_descendants(chain())
    assert counts == {"prob": 3, "stats": 2, "inference": 1, "ml": 0}


def test_diamond_does_not_double_count():
    counts = count_descendants(diamond())
    assert counts["a"] == 3  # b, c, d. NOT 4, even though d is reachable twice
    assert counts["b"] == 1
    assert counts["c"] == 1
    assert counts["d"] == 0


def test_get_descendants_returns_the_actual_ids():
    adj = build_adjacency(diamond())
    assert get_descendants("a", adj) == {"b", "c", "d"}


def test_descendants_of_unknown_id_is_empty():
    assert get_descendants("nope", build_adjacency(chain())) == set()


def test_disconnected_components():
    concepts = chain() + [C("alg"), C("deriv", ["alg"])]
    counts = count_descendants(concepts)
    assert counts["prob"] == 3
    assert counts["alg"] == 1
    assert counts["deriv"] == 0


def test_single_node_has_no_descendants():
    assert count_descendants([C("a")]) == {"a": 0}


# ---------- topological order ----------

def assert_prereqs_first(concepts, order):
    pos = {cid: i for i, cid in enumerate(order)}
    for c in concepts:
        for p in c.prerequisite_ids:
            assert pos[p] < pos[c.id], f"{p} must come before {c.id}"


def test_topological_order_respects_prerequisites():
    for g in (chain(), diamond()):
        order = topological_order(g)
        assert sorted(order) == sorted(c.id for c in g)
        assert_prereqs_first(g, order)


def test_topological_order_with_disconnected_components():
    g = chain() + [C("alg"), C("deriv", ["alg"])]
    order = topological_order(g)
    assert len(order) == 6
    assert_prereqs_first(g, order)


def test_topological_order_is_deterministic():
    assert topological_order(diamond()) == topological_order(diamond())


def test_priority_breaks_ties_between_available_concepts():
    # b and c are both available after a; higher priority goes first
    order = topological_order(diamond(), priority={"b": 0.1, "c": 0.9})
    assert order == ["a", "c", "b", "d"]
    order = topological_order(diamond(), priority={"b": 0.9, "c": 0.1})
    assert order == ["a", "b", "c", "d"]


def test_priority_can_never_violate_prerequisites():
    # ml has by far the highest priority but still can't come first
    g = chain()
    order = topological_order(g, priority={"ml": 100.0, "inference": 50.0})
    assert order == ["prob", "stats", "inference", "ml"]
    assert_prereqs_first(g, order)


def test_topological_order_raises_on_cycle():
    with pytest.raises(ValueError):
        topological_order([C("a", ["b"]), C("b", ["a"])])