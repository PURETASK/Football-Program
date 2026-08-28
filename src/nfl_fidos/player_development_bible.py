"""Validator for the controlled NFL Player Development Bible."""

from __future__ import annotations

from typing import Any


REQUIRED_POSITION_FIELDS = ("id", "position", "roles", "competencies", "evidence", "drills", "assessment_methods")


def validate_player_development_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    positions = bible.get("position_families", [])
    ids: set[str] = set()
    covered_roles: set[str] = set()
    for position in positions:
        if position.get("id") in ids:
            issues.append(f"duplicate position family: {position.get('id')}")
        ids.add(position.get("id"))
        for field in REQUIRED_POSITION_FIELDS:
            if not position.get(field):
                issues.append(f"{position.get('id')}: missing {field}")
        covered_roles.update(position.get("roles", []))
    if len(positions) < 12:
        issues.append("position coverage is incomplete")
    if len(covered_roles) < 20:
        issues.append("role coverage is incomplete")
    for field in ("mastery_levels", "common_competencies", "idp_requirements", "assessment_rules", "learning_path_requirements"):
        if not bible.get(field):
            issues.append(f"missing development control: {field}")
    return {"bible_id":bible.get("bible_id"), "status":"valid" if not issues else "invalid", "position_count":len(positions), "role_count":len(covered_roles), "errors":issues}
