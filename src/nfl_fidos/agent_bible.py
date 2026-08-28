"""Validator for the controlled Agent Organization Bible."""

from __future__ import annotations

from typing import Any


REQUIRED_ROLE_FIELDS = ("id", "name", "family", "mission", "inputs", "outputs", "collaborators", "authority", "escalation")


def validate_agent_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    roles = bible.get("roles", [])
    ids: set[str] = set()
    for role in roles:
        role_id = role.get("id")
        if role_id in ids:
            issues.append(f"duplicate agent role: {role_id}")
        ids.add(role_id)
        for field in REQUIRED_ROLE_FIELDS:
            if not role.get(field):
                issues.append(f"{role_id}: missing {field}")
        if not str(role_id).startswith("AGT-"):
            issues.append(f"invalid agent id: {role_id}")
    if not bible.get("handoff_matrix") or not bible.get("collaboration_rules") or not bible.get("prompt_requirements") or not bible.get("agent_eval_requirements"):
        issues.append("handoff, collaboration, prompt, and eval requirements are required")
    return {"bible_id":bible.get("bible_id"), "status":"valid" if not issues else "invalid", "role_count":len(roles), "errors":issues}
