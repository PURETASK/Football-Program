"""Tenant-scoped staff roster and observable coaching review package."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .coach_development import build_coaching_staff_architecture, evaluate_coach_performance


def build_organization_staff_package(*, package_id: str, organization_id: str, team_context: str, season: str, staff: list[dict[str, Any]], evaluations: list[dict[str, Any]], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-STAFF-"):
        issues.append({"code": "ORG-STAFF-ID", "message": "Package id must use ORG-STAFF- prefix", "path": "id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "ORG-STAFF-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not team_context or not season or not compiler:
        issues.append({"code": "ORG-STAFF-METADATA", "message": "team_context, season, and compiler are required", "path": "metadata"})
    if not staff:
        issues.append({"code": "ORG-STAFF-EMPTY", "message": "At least one staff record is required", "path": "staff"})
    architecture = build_coaching_staff_architecture(architecture_id=f"STAFF-{package_id.removeprefix('ORG-STAFF-')}", staff=staff, season=season, team_context=team_context)
    for issue in architecture.get("issues", []):
        issues.append({"code": issue["code"], "message": issue["message"], "path": f"staff.{issue['path']}"})
    evaluations_out: list[dict[str, Any]] = []
    for index, evaluation in enumerate(evaluations):
        result = evaluate_coach_performance(evaluation_id=evaluation.get("evaluation_id", f"EVAL-COACH-{index + 1:03d}"), coach_id=evaluation.get("coach_id", ""), role=evaluation.get("role", ""), ratings=evaluation.get("ratings", {}), evidence=evaluation.get("evidence", []), evaluator=evaluation.get("evaluator", compiler))
        evaluations_out.append(result)
        if result["status"] != "under_review":
            issues.extend({"code": item["code"], "message": item["message"], "path": f"evaluations[{index}].{item['path']}"} for item in result.get("issues", []))
    return {"id": package_id, "organization_id": organization_id, "team_context": team_context, "season": season, "staff": architecture["staff"], "interfaces": architecture["interfaces"], "evaluations": evaluations_out, "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_staff_package(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-STAFF-STATE", "message": "Only an under_review staff package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-STAFF-ROLE", "message": "Only a program_owner may validate organization staff records", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-STAFF-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
