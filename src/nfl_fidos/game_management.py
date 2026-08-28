"""Situation-aware game-management decision records."""

from __future__ import annotations

from typing import Any


def build_game_situation(
    *,
    situation_id: str,
    quarter: int,
    clock_seconds: int,
    score_differential: int,
    down: int,
    distance: int,
    timeouts: dict[str, int],
    field_zone: str,
    possession: str,
    rule_refs: list[str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not situation_id.startswith("SITUATION-"):
        issues.append({"code": "SITUATION-ID", "message": "Situation id must start with SITUATION-", "path": "situation_id"})
    if quarter < 1 or quarter > 5 or clock_seconds < 0 or clock_seconds > 900:
        issues.append({"code": "SITUATION-CLOCK", "message": "Quarter or clock is outside supported bounds", "path": "clock"})
    if down < 1 or down > 4 or distance < 1:
        issues.append({"code": "SITUATION-DOWN", "message": "Down and distance are invalid", "path": "down_distance"})
    if not timeouts or any(not isinstance(value, int) or value < 0 for value in timeouts.values()):
        issues.append({"code": "SITUATION-TIMEOUTS", "message": "Timeout map must contain non-negative integer values", "path": "timeouts"})
    if not field_zone or not possession or not rule_refs:
        issues.append({"code": "SITUATION-CONTEXT", "message": "Field zone, possession, and rule references are required", "path": "context"})
    return {
        "id": situation_id, "quarter": quarter, "clock_seconds": clock_seconds,
        "score_differential": score_differential, "down": down, "distance": distance,
        "timeouts": timeouts, "field_zone": field_zone, "possession": possession,
        "rule_refs": rule_refs, "status": "invalid" if issues else "ready", "issues": issues,
    }


def build_game_decision(
    *,
    decision_id: str,
    situation: dict[str, Any],
    options: list[dict[str, Any]],
    rule_refs: list[str],
    evidence_refs: list[str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not decision_id.startswith("DECISION-"):
        issues.append({"code": "DECISION-ID", "message": "Decision id must start with DECISION-", "path": "decision_id"})
    if situation.get("status") != "ready":
        issues.append({"code": "DECISION-SITUATION", "message": "Decision requires a ready game situation", "path": "situation"})
    if not options:
        issues.append({"code": "DECISION-OPTIONS", "message": "At least one decision option is required", "path": "options"})
    for index, option in enumerate(options):
        if not option.get("id") or not option.get("action") or not option.get("rationale") or not option.get("risk"):
            issues.append({"code": "DECISION-OPTION", "message": "Each option requires id, action, rationale, and risk", "path": f"options[{index}]"})
    if not rule_refs:
        issues.append({"code": "DECISION-RULES", "message": "Decision must retain rule references", "path": "rule_refs"})
    return {
        "id": decision_id, "situation_id": situation.get("id"), "options": options,
        "rule_refs": rule_refs, "evidence_refs": evidence_refs,
        "human_review_required": True, "status": "rejected" if issues else "draft", "issues": issues,
    }
