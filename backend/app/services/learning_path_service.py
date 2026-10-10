"""Prerequisite-aware study sequencing.

The path contains every recommended concept (review + verify). It is a topological order of
those concepts under the *transitive* prerequisite relation of the full graph, so a concept
always comes after any recommended concept it depends on, even through intermediate concepts
that are not in the path. Ties between ready concepts break by priority (verify items, which
have no score, rank by downstream impact after scored ones).
"""

from __future__ import annotations

from typing import Any

from app.services import graph_service
from app.services.gap_service import GapAnalysis


def build_learning_path(concepts: list[dict[str, Any]], analysis: GapAnalysis) -> dict[str, Any]:
    selected = [r["concept_id"] for r in analysis.recommendations]
    if not selected:
        assessed = any(i["mastery"] != "unassessed" for i in analysis.info.values())
        summary = ("No knowledge gaps were detected: every assessed concept was answered at a strong level. "
                   "These results are preliminary estimates based on a short diagnostic quiz."
                   if assessed else "No concepts were assessed, so no study path could be generated.")
        return {"total_steps": 0, "summary": summary, "steps": []}

    anc = graph_service.ancestors(concepts)
    selected_set = set(selected)
    sub = [{"id": cid, "prerequisites": sorted(anc[cid] & selected_set)} for cid in selected]
    info = analysis.info
    rank = {cid: i for i, cid in enumerate(selected)}

    def tie_break(cid: str) -> float:
        # Higher is picked first. Scored concepts by priority; then unscored by recommendation rank.
        p = info[cid]["priority"]
        return p + 1000.0 if p is not None else -rank[cid] / 1000.0

    order = graph_service.topological_sort(sub, priority=tie_break)
    sub_prereqs = {c["id"]: c["prerequisites"] for c in sub}

    steps = []
    position: dict[str, int] = {}
    for n, cid in enumerate(order, start=1):
        i = info[cid]
        position[cid] = n
        before = sorted(sub_prereqs[cid], key=position.__getitem__)
        if before:
            lead = f"Study after {', '.join(info[b]['concept_name'] for b in before)}, which it builds on. "
        elif n == 1:
            lead = "Start here: it has no unresolved prerequisites in your path. "
        else:
            lead = "Ready now: none of its prerequisites need review. "
        steps.append({
            "step": n, "concept_id": cid, "concept_name": i["concept_name"], "action": i["action"],
            "mastery": i["mastery"], "score": i["score"], "priority": i["priority"],
            "prerequisites_in_path": before, "reason": lead + i["reason"],
        })

    noun = "concept" if len(steps) == 1 else "concepts"
    summary = (f"Study {len(steps)} {noun} in this order. Each step comes after the prerequisites it depends on; "
               "when several concepts are ready at once, the one with the higher review priority comes first.")
    return {"total_steps": len(steps), "summary": summary, "steps": steps}
