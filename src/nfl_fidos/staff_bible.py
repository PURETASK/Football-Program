"""Validator for the controlled coaching staff development bible."""

from __future__ import annotations

from typing import Any


REQUIRED_ROLE_FIELDS = ("role", "dimensions", "outputs", "collaborators", "review_owner")


def validate_staff_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    roles = bible.get("role_trees", [])
    seen: set[str] = set()
    for role in roles:
        name = role.get("role")
        if name in seen:
            issues.append(f"duplicate staff role: {name}")
        seen.add(name)
        for field in REQUIRED_ROLE_FIELDS:
            if not role.get(field):
                issues.append(f"{name}: missing {field}")
    required_roles = {"head_coach","offensive_coordinator","defensive_coordinator","special_teams_coordinator","position_coach","quality_control","analyst","game_management"}
    if not required_roles.issubset(seen):
        issues.append("required coaching and staff roles are incomplete")
    if bible.get("development_pathway") != ["observe","teach","practice","diagnose","adapt","review"]:
        issues.append("development pathway must preserve observe-to-review stages")
    for field in ("observable_evaluation", "collaboration_model", "boundaries"):
        if not bible.get(field):
            issues.append(f"missing staff control: {field}")
    return {"bible_id":bible.get("bible_id"), "status":"valid" if not issues else "invalid", "role_count":len(roles), "errors":issues}
