"""Validation for the Stage 8 Special Teams Bible."""

from __future__ import annotations

from typing import Any


REQUIRED_UNITS = {"kickoff", "kick_return", "punt", "punt_return", "field_goal_pat", "hands_team_block_units"}
REQUIRED_FIELDS = ("id", "unit", "phases", "operations", "responsibility_map", "specialist_mastery", "situations", "rules_context", "practice_requirements", "scouting_requirements")


def validate_special_teams_unit(unit: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_FIELDS:
        if not unit.get(field):
            issues.append(f"missing {field}")
    if not isinstance(unit.get("id"), str) or not unit.get("id", "").startswith("ST-UNIT-"):
        issues.append("unit id must start with ST-UNIT-")
    for field in REQUIRED_FIELDS[2:]:
        if field in unit and (not isinstance(unit[field], list) or not unit[field]):
            issues.append(f"{field} must be a non-empty list")
    return issues


def validate_special_teams_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    units = bible.get("units", [])
    seen: set[str] = set()
    for unit in units:
        if unit.get("id") in seen:
            issues.append(f"duplicate unit id: {unit.get('id')}")
        seen.add(unit.get("id"))
        issues.extend(f"{unit.get('id')}: {issue}" for issue in validate_special_teams_unit(unit))
    missing = sorted(REQUIRED_UNITS - {unit.get("unit") for unit in units})
    if missing:
        issues.append(f"missing required special-teams units: {', '.join(missing)}")
    controls = bible.get("global_controls", [])
    if not controls or not any("Rule-dependent" in control for control in controls):
        issues.append("global rule-authority control is required")
    return {"bible_id": bible.get("bible_id"), "status": "valid" if not issues else "invalid", "errors": issues, "unit_count": len(units), "covered_units": sorted({unit.get("unit") for unit in units})}
