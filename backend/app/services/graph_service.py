"""Knowledge graph algorithms over concept dicts.

A concept dict has at least ``id`` and ``prerequisites`` (list of concept IDs). An edge
``prereq -> concept`` means "prereq must be learned before concept".

``validate_graph`` is strict (raises). ``repair_concepts`` is the lenient counterpart used on
AI output: it fixes what it safely can and reports each fix as a warning.
"""

from __future__ import annotations

import heapq
import re
from collections.abc import Callable, Iterable
from typing import Any

from app.errors import GraphValidationError

ConceptDict = dict[str, Any]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:60] or "concept"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_graph(concepts: list[ConceptDict]) -> None:
    """Raise GraphValidationError for duplicate IDs, missing refs, self-deps or cycles."""
    ids = [c["id"] for c in concepts]
    seen: set[str] = set()
    duplicates = sorted({i for i in ids if i in seen or seen.add(i)})
    if duplicates:
        raise GraphValidationError("Duplicate concept IDs.", code="duplicate_concept_ids",
                                   details={"concept_ids": duplicates})
    id_set = set(ids)
    for c in concepts:
        if c["id"] in c["prerequisites"]:
            raise GraphValidationError(f"Concept '{c['id']}' depends on itself.", code="self_dependency",
                                       details={"concept_id": c["id"]})
        missing = [p for p in c["prerequisites"] if p not in id_set]
        if missing:
            raise GraphValidationError(f"Concept '{c['id']}' references unknown prerequisites.",
                                       code="missing_prerequisite",
                                       details={"concept_id": c["id"], "missing": missing})
    cycle = find_cycle(concepts)
    if cycle:
        raise GraphValidationError("Circular prerequisite dependency.", code="circular_dependency",
                                   details={"cycle": cycle})


def find_cycle(concepts: list[ConceptDict]) -> list[str] | None:
    """Return one cycle as [a, b, ..., a] (following prerequisite links), or None. Iterative DFS."""
    prereqs = {c["id"]: [p for p in c["prerequisites"] if p != c["id"]] for c in concepts}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(prereqs, WHITE)
    for start in prereqs:
        if color[start] != WHITE:
            continue
        stack: list[tuple[str, Iterable[str]]] = [(start, iter(prereqs[start]))]
        path = [start]
        color[start] = GRAY
        while stack:
            node, children = stack[-1]
            nxt = next(children, None)
            if nxt is None:
                color[node] = BLACK
                stack.pop()
                path.pop()
                continue
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                return path[path.index(nxt):] + [nxt]
            if color[nxt] == WHITE:
                color[nxt] = GRAY
                stack.append((nxt, iter(prereqs[nxt])))
                path.append(nxt)
    return None


def repair_concepts(concepts: list[ConceptDict]) -> tuple[list[ConceptDict], list[str]]:
    """Make a concept list a valid DAG. Returns (repaired copy, warnings).

    Fixes: merges duplicate IDs (union of prerequisites), drops unknown and self references,
    de-duplicates prerequisite lists, and breaks cycles by removing one edge per cycle.
    """
    warnings: list[str] = []
    merged: dict[str, ConceptDict] = {}
    for c in concepts:
        if c["id"] in merged:
            existing = merged[c["id"]]
            existing["prerequisites"] = list(dict.fromkeys(existing["prerequisites"] + list(c["prerequisites"])))
            warnings.append(f"Merged duplicate concept '{c['id']}'.")
        else:
            merged[c["id"]] = {**c, "prerequisites": list(c["prerequisites"])}

    for c in merged.values():
        cleaned = []
        for p in dict.fromkeys(c["prerequisites"]):
            if p == c["id"]:
                warnings.append(f"Removed self-dependency on '{c['id']}'.")
            elif p not in merged:
                warnings.append(f"Removed unknown prerequisite '{p}' from '{c['id']}'.")
            else:
                cleaned.append(p)
        c["prerequisites"] = cleaned

    result = list(merged.values())
    while (cycle := find_cycle(result)) is not None:
        # cycle = [a, b, ..., a] where each next item is a prerequisite of the previous one.
        dependent, prereq = cycle[-2], cycle[-1]
        merged[dependent]["prerequisites"].remove(prereq)
        warnings.append(f"Removed prerequisite '{prereq}' from '{dependent}' to break a cycle "
                        f"({' -> '.join(cycle)}).")
    return result, warnings


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def dependents_map(concepts: list[ConceptDict]) -> dict[str, list[str]]:
    """concept_id -> IDs of concepts that list it as a direct prerequisite."""
    children: dict[str, list[str]] = {c["id"]: [] for c in concepts}
    for c in concepts:
        for p in c["prerequisites"]:
            children[p].append(c["id"])
    return children


def descendants(concepts: list[ConceptDict]) -> dict[str, set[str]]:
    """concept_id -> set of all unique downstream dependents (no double counting)."""
    children = dependents_map(concepts)
    memo: dict[str, set[str]] = {}
    for cid in topological_sort(concepts)[::-1]:  # dependents are processed first
        acc: set[str] = set()
        for child in children[cid]:
            acc.add(child)
            acc |= memo[child]
        memo[cid] = acc
    return memo


def ancestors(concepts: list[ConceptDict]) -> dict[str, set[str]]:
    """concept_id -> set of all direct and indirect prerequisites."""
    by_id = {c["id"]: c for c in concepts}
    memo: dict[str, set[str]] = {}
    for cid in topological_sort(concepts):
        acc: set[str] = set()
        for p in by_id[cid]["prerequisites"]:
            acc.add(p)
            acc |= memo[p]
        memo[cid] = acc
    return memo


def topological_sort(concepts: list[ConceptDict],
                     priority: Callable[[str], float] | None = None) -> list[str]:
    """Kahn's algorithm. Prerequisites always precede dependents.

    Among simultaneously-ready nodes, picks the highest ``priority`` first, falling back to the
    original list order so output is deterministic. Raises GraphValidationError on cycles.
    """
    order_index = {c["id"]: i for i, c in enumerate(concepts)}
    indegree = {c["id"]: 0 for c in concepts}
    for c in concepts:
        for p in c["prerequisites"]:
            if p in indegree:
                indegree[c["id"]] += 1
    children = {cid: [] for cid in indegree}
    for c in concepts:
        for p in c["prerequisites"]:
            if p in children:
                children[p].append(c["id"])

    def key(cid: str) -> tuple[float, int]:
        return (-(priority(cid) if priority else 0.0), order_index[cid])

    heap = [(key(cid), cid) for cid, deg in indegree.items() if deg == 0]
    heapq.heapify(heap)
    result: list[str] = []
    while heap:
        _, cid = heapq.heappop(heap)
        result.append(cid)
        for child in children[cid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(heap, (key(child), child))
    if len(result) != len(concepts):
        raise GraphValidationError("Circular prerequisite dependency.", code="circular_dependency")
    return result


def levels(concepts: list[ConceptDict]) -> dict[str, int]:
    """Longest prerequisite chain from any root (roots are level 0)."""
    by_id = {c["id"]: c for c in concepts}
    level: dict[str, int] = {}
    for cid in topological_sort(concepts):
        prereqs = by_id[cid]["prerequisites"]
        level[cid] = 1 + max(level[p] for p in prereqs) if prereqs else 0
    return level


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def serialize_graph(concepts: list[ConceptDict]) -> dict[str, Any]:
    """Frontend-friendly JSON: concepts (with descendant_count, level), edges, topological_order."""
    desc = descendants(concepts)
    lvl = levels(concepts)
    order = topological_sort(concepts)
    by_id = {c["id"]: c for c in concepts}
    nodes = []
    for cid in order:
        c = by_id[cid]
        nodes.append({
            "id": c["id"],
            "name": c["name"],
            "description": c["description"],
            "difficulty": c["difficulty"],
            "prerequisites": list(c["prerequisites"]),
            "source_type": c["source_type"],
            "descendant_count": len(desc[cid]),
            "level": lvl[cid],
        })
    edges = [
        {"id": f"{p}->{c['id']}", "source": p, "target": c["id"], "relationship": "prerequisite"}
        for c in nodes for p in c["prerequisites"]
    ]
    return {"concepts": nodes, "edges": edges, "topological_order": order}
