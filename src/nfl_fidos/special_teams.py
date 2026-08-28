"""Explicit special-teams unit, phase, role, and situation modeling."""

from __future__ import annotations

from typing import Any


UNITS = {"kickoff", "kick_return", "punt", "punt_return", "field_goal", "extra_point"}
PHASES = {"operation", "coverage", "return", "protection", "rush", "lane_integrity", "tackling"}


def build_special_teams_plan(
    *,
    plan_id: str,
    unit: str,
    phase: str,
    operation: str,
    roles: list[dict[str, Any]],
    situations: list[str],
    constraints: list[str],
    source: dict[str, str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not plan_id.startswith("ST-"):
        issues.append({"code": "ST-ID", "message": "Special-teams id must start with ST-", "path": "plan_id"})
    if unit not in UNITS:
        issues.append({"code": "ST-UNIT", "message": "Unknown special-teams unit", "path": "unit"})
    if phase not in PHASES:
        issues.append({"code": "ST-PHASE", "message": "Unknown special-teams phase", "path": "phase"})
    if not operation or not roles or not situations:
        issues.append({"code": "ST-CONTEXT", "message": "Operation, roles, and situations are required", "path": "context"})
    seen_roles: set[str] = set()
    for index, role in enumerate(roles):
        if not role.get("role") or not role.get("responsibility"):
            issues.append({"code": "ST-ROLE", "message": "Each role requires a responsibility", "path": f"roles[{index}]"})
        elif role["role"] in seen_roles:
            issues.append({"code": "ST-DUPLICATE-ROLE", "message": f"Duplicate role: {role['role']}", "path": f"roles[{index}]"})
        seen_roles.add(role.get("role", ""))
    if not source.get("kind") or not source.get("ref"):
        issues.append({"code": "ST-PROVENANCE", "message": "Source kind and ref are required", "path": "source"})
    return {
        "id": plan_id, "unit": unit, "phase": phase, "operation": operation, "roles": roles,
        "situations": situations, "constraints": constraints, "source": source,
        "review_required": True, "status": "rejected" if issues else "draft", "issues": issues,
    }
