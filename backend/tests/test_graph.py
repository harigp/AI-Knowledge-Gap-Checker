import pytest

from app.errors import GraphValidationError
from app.services import graph_service as g


def c(cid, *prereqs):
    return {"id": cid, "name": cid.title(), "description": "d", "difficulty": "beginner",
            "prerequisites": list(prereqs), "source_type": "document"}


DIAMOND = [c("a"), c("b", "a"), c("c", "a"), c("d", "b", "c"), c("e", "d")]


def test_valid_graph_passes():
    g.validate_graph(DIAMOND)


def test_duplicate_ids():
    with pytest.raises(GraphValidationError) as e:
        g.validate_graph([c("a"), c("a")])
    assert e.value.code == "duplicate_concept_ids"


def test_missing_prerequisite():
    with pytest.raises(GraphValidationError) as e:
        g.validate_graph([c("a", "ghost")])
    assert e.value.code == "missing_prerequisite"


def test_self_dependency():
    with pytest.raises(GraphValidationError) as e:
        g.validate_graph([c("a", "a")])
    assert e.value.code == "self_dependency"


def test_circular_dependency():
    concepts = [c("a", "c"), c("b", "a"), c("c", "b")]
    with pytest.raises(GraphValidationError) as e:
        g.validate_graph(concepts)
    assert e.value.code == "circular_dependency"
    cycle = e.value.details["cycle"]
    assert cycle[0] == cycle[-1] and set(cycle) == {"a", "b", "c"}


def test_disconnected_components():
    concepts = [c("a"), c("b", "a"), c("x"), c("y", "x"), c("solo")]
    g.validate_graph(concepts)
    order = g.topological_sort(concepts)
    assert set(order) == {"a", "b", "x", "y", "solo"}
    assert g.descendants(concepts)["a"] == {"b"}
    assert g.descendants(concepts)["solo"] == set()


def test_descendants_no_double_counting_on_multiple_paths():
    desc = g.descendants(DIAMOND)
    assert desc["a"] == {"b", "c", "d", "e"}  # d reachable via b and c, counted once
    assert len(desc["a"]) == 4
    assert desc["b"] == {"d", "e"}
    assert desc["e"] == set()


def test_topological_order_is_valid():
    order = g.topological_sort(DIAMOND)
    pos = {cid: i for i, cid in enumerate(order)}
    for concept in DIAMOND:
        for p in concept["prerequisites"]:
            assert pos[p] < pos[concept["id"]]


def test_topological_sort_uses_priority_for_ties():
    order = g.topological_sort([c("low"), c("high")], priority={"low": 0.1, "high": 0.9}.get)
    assert order == ["high", "low"]


def test_topological_sort_raises_on_cycle():
    with pytest.raises(GraphValidationError):
        g.topological_sort([c("a", "b"), c("b", "a")])


def test_levels():
    assert g.levels(DIAMOND) == {"a": 0, "b": 1, "c": 1, "d": 2, "e": 3}


def test_repair_fixes_all_problems():
    raw = [c("a", "a", "ghost"), c("b", "a", "c"), c("c", "b"), c("a", "b")]
    fixed, warnings = g.repair_concepts(raw)
    g.validate_graph(fixed)  # no exception
    assert len(fixed) == 3
    assert warnings


def test_serialize_graph():
    out = g.serialize_graph(DIAMOND)
    assert out["topological_order"][0] == "a"
    by_id = {n["id"]: n for n in out["concepts"]}
    assert by_id["a"]["descendant_count"] == 4
    assert by_id["e"]["level"] == 3
    assert {"id": "a->b", "source": "a", "target": "b", "relationship": "prerequisite"} in out["edges"]
    assert len(out["edges"]) == 5
