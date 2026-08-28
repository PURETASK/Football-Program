"""Practice architecture primitives with objective-to-evaluation traceability."""

from __future__ import annotations

from typing import Any


def build_practice_plan(
    *,
    plan_id: str,
    team_context: str,
    objective: str,
    drills: list[dict[str, Any]],
    constraints: list[str] | None = None,
) -> dict[str, Any]:
    """Build a practice plan only when each drill has a measurable evaluation."""
    constraints = constraints or []
    periods = []
    evaluation = []
    for index, drill in enumerate(drills, start=1):
        if not drill.get("id") or not drill.get("skill") or not drill.get("evaluation"):
            raise ValueError({"code": "PRACTICE-DRILL-INCOMPLETE", "index": index})
        periods.append({"period": index, "drill_id": drill["id"], "skill": drill["skill"], "constraint": drill.get("constraint")})
        evaluation.append({"drill_id": drill["id"], "measure": drill["evaluation"]})
    if not periods:
        raise ValueError({"code": "PRACTICE-NO-DRILLS", "message": "At least one drill is required"})
    return {
        "id": plan_id,
        "capability_id": "CAP-013",
        "workflow_id": "WF-005",
        "team_context": team_context,
        "objective": objective,
        "constraints": constraints,
        "periods": periods,
        "evaluation": evaluation,
        "status": "draft",
    }
