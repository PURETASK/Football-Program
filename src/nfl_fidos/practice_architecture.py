"""Stage 12 practice periods, objective mapping, and load controls."""

from __future__ import annotations

from typing import Any


PERIOD_TYPES = {"individual", "group", "inside_run", "skelly", "team", "situational", "special_teams", "installation", "correction", "walkthrough", "competitive"}


def validate_practice_architecture(practice: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ("id", "team_context", "season_phase", "week_context", "objective", "opponent_priorities", "periods", "staff_available", "facility_constraints", "load_controls", "restrictions")
    for field in required:
        if not practice.get(field) and practice.get(field) != []:
            issues.append({"code":"PRACTICE-SPEC-REQUIRED", "message":f"Missing practice field: {field}", "path":field})
    if practice.get("id") and not str(practice["id"]).startswith("PRACTICE-"):
        issues.append({"code":"PRACTICE-ID", "message":"Practice id must start with PRACTICE-", "path":"id"})
    if not isinstance(practice.get("periods"), list) or not practice["periods"]:
        issues.append({"code":"PRACTICE-PERIODS", "message":"At least one period is required", "path":"periods"})
    total_minutes = 0
    for index, period in enumerate(practice.get("periods", [])):
        path = f"periods[{index}]"
        if period.get("type") not in PERIOD_TYPES:
            issues.append({"code":"PRACTICE-PERIOD-TYPE", "message":"Unknown period type", "path":f"{path}.type"})
        for field in ("id", "objective", "owner", "players", "minutes", "reps", "learning_rationale", "load_rationale"):
            if not period.get(field) and period.get(field) != 0:
                issues.append({"code":"PRACTICE-PERIOD-REQUIRED", "message":f"Period requires {field}", "path":f"{path}.{field}"})
        if isinstance(period.get("minutes"), (int, float)):
            total_minutes += period["minutes"]
    controls = practice.get("load_controls", {})
    if not isinstance(controls, dict) or not controls.get("max_total_minutes") or not controls.get("max_reps_by_position"):
        issues.append({"code":"PRACTICE-LOAD", "message":"Maximum total minutes and position rep controls are required", "path":"load_controls"})
    elif total_minutes > controls["max_total_minutes"]:
        issues.append({"code":"PRACTICE-LOAD-EXCEEDED", "message":"Period minutes exceed maximum total minutes", "path":"periods"})
    return issues


def build_practice_architecture(*, practice_id: str, team_context: str, season_phase: str, week_context: str, objective: str, opponent_priorities: list[str], periods: list[dict[str, Any]], staff_available: list[str], facility_constraints: list[str], load_controls: dict[str, Any], restrictions: list[dict[str, Any]]) -> dict[str, Any]:
    practice = {"id":practice_id, "team_context":team_context, "season_phase":season_phase, "week_context":week_context, "objective":objective, "opponent_priorities":opponent_priorities, "periods":periods, "staff_available":staff_available, "facility_constraints":facility_constraints, "load_controls":load_controls, "restrictions":restrictions}
    issues = validate_practice_architecture(practice)
    practice["status"] = "invalid" if issues else "draft"
    practice["issues"] = issues
    practice["objective_to_period"] = [{"objective":objective, "period_ids":[period.get("id") for period in periods]}]
    practice["total_minutes"] = sum(period.get("minutes", 0) for period in periods)
    return practice
