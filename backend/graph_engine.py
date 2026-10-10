"""
graph_engine.py: pure graph logic for ConceptGraph AI.

No FastAPI, Gemini, database, or quiz-score imports. It only answers
structural questions about a list of Concepts.

Direction: an edge A -> B means "A is a prerequisite for B".
  - concept.prerequisite_ids = incoming edges (parents)
  - adjacency (built here)    = outgoing edges (children / dependents)
"""

import heapq
from collections import Counter

from models import Concept

Adjacency = dict[str, list[str]]


# ---------- Building blocks ----------

def build_adjacency(concepts: list[Concept]) -> Adjacency:
    """Map each concept id -> list of concepts that depend on it (its children).

    Prerequisites that don't exist, and duplicate edges, are ignored here so
    the traversal functions never crash. validate_graph() is what reports them.
    """
    ids = {c.id for c in concepts}
    adjacency: Adjacency = {cid: [] for cid in ids}
    seen_edges: set[tuple[str, str]] = set()
    for c in concepts:
        for prereq in c.prerequisite_ids:
            edge = (prereq, c.id)
            if prereq in ids and edge not in seen_edges:
                seen_edges.add(edge)
                adjacency[prereq].append(c.id)
    return adjacency


def find_cycle(concepts: list[Concept]) -> list[str] | None:
    """Return the ids forming one cycle (e.g. ['a', 'b', 'c']), or None if acyclic."""
    adjacency = build_adjacency(concepts)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in adjacency}
    path: list[str] = []

    def dfs(node: str) -> list[str] | None:
        color[node] = GRAY
        path.append(node)
        for child in adjacency[node]:
            if color[child] == GRAY:  # back edge -> cycle
                return path[path.index(child):]
            if color[child] == WHITE:
                found = dfs(child)
                if found:
                    return found
        path.pop()
        color[node] = BLACK
        return None

    for cid in adjacency:
        if color[cid] == WHITE:
            found = dfs(cid)
            if found:
                return found
    return None


# ---------- Validation ----------

def validate_graph(concepts: list[Concept]) -> list[str]:
    """Return a list of human-readable problems. An empty list means the graph is valid."""
    errors: list[str] = []

    # Duplicate IDs
    id_counts = Counter(c.id for c in concepts)
    for cid, n in id_counts.items():
        if n > 1:
            errors.append(f"Duplicate concept id '{cid}' appears {n} times")

    ids = set(id_counts)
    for c in concepts:
        # Self-dependency (the model blocks this too; checked again for safety)
        if c.id in c.prerequisite_ids:
            errors.append(f"Concept '{c.id}' lists itself as a prerequisite")

        # Duplicate edges
        for prereq, n in Counter(c.prerequisite_ids).items():
            if n > 1:
                errors.append(f"Concept '{c.id}' lists prerequisite '{prereq}' {n} times")

        # Missing prerequisites
        for prereq in c.prerequisite_ids:
            if prereq not in ids:
                errors.append(f"Concept '{c.id}' has unknown prerequisite '{prereq}'")

    # Cycles (only meaningful if the structure above is sound, but harmless otherwise)
    cycle = find_cycle(concepts)
    if cycle:
        errors.append("Circular dependency: " + " -> ".join(cycle + [cycle[0]]))

    return errors


# ---------- Descendants ----------

def get_descendants(concept_id: str, adjacency: Adjacency) -> set[str]:
    """All unique concepts reachable downstream of concept_id (not including itself).

    A set is used so a concept reachable via several paths is counted once.
    Unknown ids return an empty set.
    """
    descendants: set[str] = set()
    stack = list(adjacency.get(concept_id, []))
    while stack:
        node = stack.pop()
        if node in descendants:
            continue
        descendants.add(node)
        stack.extend(adjacency.get(node, []))
    return descendants


def count_descendants(concepts: list[Concept]) -> dict[str, int]:
    """Map each concept id -> number of unique downstream concepts."""
    adjacency = build_adjacency(concepts)
    return {cid: len(get_descendants(cid, adjacency)) for cid in adjacency}


# ---------- Ordering ----------

def topological_order(
    concepts: list[Concept],
    priority: dict[str, float] | None = None,
) -> list[str]:
    """Return concept ids so every prerequisite comes before its dependents (Kahn's algorithm).

    Whenever several concepts are available at once, the one with the HIGHEST
    priority goes first. Ties (and the no-priority case) fall back to the
    original input order, so the result is deterministic.

    Raises ValueError if the graph has a cycle.
    """
    priority = priority or {}
    adjacency = build_adjacency(concepts)
    position = {c.id: i for i, c in enumerate(concepts)}

    in_degree = {cid: 0 for cid in adjacency}
    for children in adjacency.values():
        for child in children:
            in_degree[child] += 1

    def key(cid: str) -> tuple[float, int]:
        return (-priority.get(cid, 0.0), position[cid])

    heap = [key(cid) + (cid,) for cid, deg in in_degree.items() if deg == 0]
    heapq.heapify(heap)

    order: list[str] = []
    while heap:
        *_, cid = heapq.heappop(heap)
        order.append(cid)
        for child in adjacency[cid]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                heapq.heappush(heap, key(child) + (child,))

    if len(order) != len(adjacency):
        raise ValueError("Cannot order concepts: the graph contains a cycle")
    return order