"""Tenant-scoped special-teams personnel assignments and mastery review."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .special_teams_bible import validate_special_teams_bible


def _units() -> dict[str, dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "special_teams" / "special-teams-bible.json"
    return {item.get("id"): item for item in json.loads(path.read_text(encoding="utf-8")).get("units", [])}


def build_organization_special_teams(*, package_id: str, organization_id: str, team_context: str, season: str, assignments: list[dict[str, Any]], source_refs: list[str], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-SPECIAL-TEAMS-"):
        issues.append({"code": "ORG-ST-ID", "message": "Package id must use ORG-SPECIAL-TEAMS- prefix", "path": "id"})
    if not organization_id.startswith("ORG-") or not team_context or not season or not compiler:
        issues.append({"code": "ORG-ST-METADATA", "message": "organization, team context, season, and compiler are required", "path": "metadata"})
    if not assignments or not source_refs:
        issues.append({"code": "ORG-ST-EMPTY", "message": "Assignments and source references are required", "path": "assignments"})
    units = _units()
    assignment_results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, assignment in enumerate(assignments):
        assignment_id = assignment.get("assignment_id", f"ST-ASSIGNMENT-{index + 1:03d}")
        unit_id = assignment.get("unit_id", "")
        specialist_id = assignment.get("specialist_id", "")
        evidence = assignment.get("mastery_evidence", [])
        source_ref = assignment.get("source_ref", source_refs[0] if source_refs else "")
        entry = {"id": assignment_id, "specialist_id": specialist_id, "unit_id": unit_id, "unit": units.get(unit_id, {}).get("unit"), "role": assignment.get("role", ""), "responsibilities": assignment.get("responsibilities", []), "mastery_evidence": evidence, "source_ref": source_ref, "review_owner": assignment.get("review_owner", ""), "status": "review_required"}
        assignment_results.append(entry)
        if assignment_id in seen:
            issues.append({"code": "ORG-ST-DUPLICATE", "message": "Duplicate assignment id", "path": f"assignments[{index}].assignment_id"})
        seen.add(assignment_id)
        if unit_id not in units:
            issues.append({"code": "ORG-ST-UNIT", "message": "Unknown special-teams unit", "path": f"assignments[{index}].unit_id"})
        if not specialist_id or not assignment.get("role") or not assignment.get("responsibilities") or not evidence or not assignment.get("review_owner"):
            issues.append({"code": "ORG-ST-ASSIGNMENT", "message": "Specialist, role, responsibilities, mastery evidence, and review owner are required", "path": f"assignments[{index}]"})
        if source_ref not in source_refs:
            issues.append({"code": "ORG-ST-SOURCE-LINK", "message": "Assignment source_ref must be listed in package source_refs", "path": f"assignments[{index}].source_ref"})
    if validate_special_teams_bible_cached() != "valid":
        issues.append({"code": "ORG-ST-REFERENCE", "message": "Canonical special-teams bible is invalid", "path": "reference"})
    return {"id": package_id, "organization_id": organization_id, "team_context": team_context, "season": season, "assignments": assignment_results, "source_refs": list(source_refs), "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def validate_special_teams_bible_cached() -> str:
    path = Path(__file__).resolve().parents[2] / "special_teams" / "special-teams-bible.json"
    return validate_special_teams_bible(json.loads(path.read_text(encoding="utf-8"))).get("status", "invalid")


def approve_organization_special_teams(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-ST-STATE", "message": "Only an under_review package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-ST-ROLE", "message": "Only a program_owner may validate special-teams personnel", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-ST-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
