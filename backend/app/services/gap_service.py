"""Knowledge gap detection: mastery classification, downstream impact and review priority.

Priority = (1 - score) * (1 + weight * descendant_count)

All explanations are built from actual scores and graph relationships only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services import graph_service


@dataclass(frozen=True)
class GapConfig:
    strong_threshold: float = 0.80
    developing_threshold: float = 0.50
    descendant_weight: float = 0.25


def classify(score: float | None, cfg: GapConfig) -> str:
    if score is None:
        return "unassessed"
    if score >= cfg.strong_threshold:
        return "strong"
    if score >= cfg.developing_threshold:
        return "developing"
    return "weak"


def priority(score: float, descendant_count: int, cfg: GapConfig) -> float:
    return round((1 - score) * (1 + cfg.descendant_weight * descendant_count), 4)


def _pct(score: float) -> str:
    return f"{round(score * 100)}%"


def _name_list(ids: list[str], names: dict[str, str], limit: int = 4) -> str:
    shown = [names[i] for i in ids[:limit]]
    if len(ids) > limit:
        shown.append(f"{len(ids) - limit} more")
    return ", ".join(shown)


@dataclass
class GapAnalysis:
    concept_scores: list[dict[str, Any]]
    learning_gaps: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    # Lookups reused by the learning path.
    info: dict[str, dict[str, Any]]


def analyze(concepts: list[dict[str, Any]], tallies: dict[str, tuple[int, int]], cfg: GapConfig) -> GapAnalysis:
    order = graph_service.topological_sort(concepts)
    position = {cid: i for i, cid in enumerate(order)}
    by_id = {c["id"]: c for c in concepts}
    names = {c["id"]: c["name"] for c in concepts}
    desc = graph_service.descendants(concepts)
    anc = graph_service.ancestors(concepts)

    info: dict[str, dict[str, Any]] = {}
    concept_scores = []
    for cid in order:
        correct, total = tallies.get(cid, (0, 0))
        score = round(correct / total, 4) if total else None
        mastery = classify(score, cfg)
        downstream = sorted(desc[cid], key=position.__getitem__)
        info[cid] = {
            "concept_id": cid, "concept_name": names[cid], "correct": correct, "total": total, "score": score,
            "mastery": mastery, "descendant_count": len(downstream), "downstream": downstream,
            "priority": priority(score, len(downstream), cfg) if score is not None else None,
        }
        concept_scores.append({"concept_id": cid, "concept_name": names[cid], "correct": correct, "total": total,
                               "score": score, "mastery": mastery})

    gap_ids = [cid for cid in order if info[cid]["mastery"] in ("weak", "developing")]
    gap_ids.sort(key=lambda cid: (-info[cid]["priority"], position[cid]))

    def gap_reason(cid: str) -> str:
        i = info[cid]
        text = (f"You answered {i['correct']} of {i['total']} questions on {i['concept_name']} correctly "
                f"({_pct(i['score'])}), so it is classified as {i['mastery']}.")
        if i["descendant_count"]:
            noun = "concept" if i["descendant_count"] == 1 else "concepts"
            verb = "builds" if i["descendant_count"] == 1 else "build"
            text += (f" {i['descendant_count']} other {noun} in this lecture {verb} on it "
                     f"({_name_list(i['downstream'], names)}), giving it a review priority of {i['priority']:g}.")
        else:
            text += (f" No other concepts in this lecture depend on it, so its review priority is "
                     f"{i['priority']:g}.")
        weak_prereqs = [p for p in sorted(anc[cid], key=position.__getitem__)
                        if info[p]["mastery"] in ("weak", "developing")]
        if weak_prereqs:
            text += f" Its prerequisite{'s' if len(weak_prereqs) > 1 else ''} " \
                    f"{_name_list(weak_prereqs, names)} also scored low, which may contribute to this gap."
        return text

    learning_gaps = []
    for cid in gap_ids:
        i = info[cid]
        i["reason"] = gap_reason(cid)
        i["action"] = "review"
        learning_gaps.append({
            "concept_id": cid, "concept_name": i["concept_name"], "score": i["score"], "mastery": i["mastery"],
            "descendant_count": i["descendant_count"], "downstream_concept_ids": i["downstream"],
            "priority": i["priority"], "reason": i["reason"],
        })

    # Unassessed prerequisites of a gap may be where the gap actually starts.
    verify_ids = sorted({p for g in gap_ids for p in anc[g] if info[p]["mastery"] == "unassessed"},
                        key=lambda cid: (-info[cid]["descendant_count"], position[cid]))
    for cid in verify_ids:
        i = info[cid]
        dependent_gaps = [g for g in gap_ids if cid in anc[g]]
        dependent_gaps.sort(key=position.__getitem__)
        i["action"] = "verify"
        i["reason"] = (f"{i['concept_name']} was not covered by the quiz, but it is a prerequisite of "
                       f"{_name_list(dependent_gaps, names)}, where you scored low. Check that you are comfortable "
                       f"with it before reviewing {'that concept' if len(dependent_gaps) == 1 else 'those concepts'}.")

    recommendations = []
    for rank, cid in enumerate(gap_ids + verify_ids, start=1):
        i = info[cid]
        recommendations.append({
            "rank": rank, "concept_id": cid, "concept_name": i["concept_name"], "action": i["action"],
            "score": i["score"], "mastery": i["mastery"], "descendant_count": i["descendant_count"],
            "priority": i["priority"], "reason": i["reason"],
        })
    return GapAnalysis(concept_scores, learning_gaps, recommendations, info)
