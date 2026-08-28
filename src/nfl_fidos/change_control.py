"""Decision ledger and controlled change-request primitives."""

from __future__ import annotations

from typing import Any


CHANGE_TYPES = {"scope", "schema", "terminology", "agent", "workflow", "doctrine", "security", "architecture"}


def build_decision_record(
    *,
    decision_id: str,
    title: str,
    decision: str,
    owner: str,
    rationale: str,
    alternatives: list[str],
    affected_ids: list[str],
    status: str = "proposed",
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not decision_id.startswith("DEC-"):
        issues.append({"code": "DECISION-ID", "message": "Decision id must start with DEC-", "path": "decision_id"})
    if not title or not decision or not owner or not rationale or not alternatives or not affected_ids:
        issues.append({"code": "DECISION-METADATA", "message": "Decision requires title, decision, owner, rationale, alternatives, and affected ids", "path": "metadata"})
    if status not in {"proposed", "approved", "superseded"}:
        issues.append({"code": "DECISION-STATUS", "message": "Invalid decision status", "path": "status"})
    return {
        "id": decision_id, "title": title, "decision": decision, "owner": owner,
        "rationale": rationale, "alternatives": alternatives, "affected_ids": affected_ids,
        "status": "proposed" if issues else status, "issues": issues,
    }


def build_change_request(
    *,
    request_id: str,
    title: str,
    requester: str,
    change_type: str,
    description: str,
    impact_scope: str,
    dependencies: list[str],
    risks: list[str],
    roadmap_effect: str,
    affected_ids: list[str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not request_id.startswith("CR-"):
        issues.append({"code": "CR-ID", "message": "Change request id must start with CR-", "path": "request_id"})
    if change_type not in CHANGE_TYPES:
        issues.append({"code": "CR-TYPE", "message": "Unknown change type", "path": "change_type"})
    if not title or not requester or not description or not impact_scope or not roadmap_effect or not affected_ids:
        issues.append({"code": "CR-METADATA", "message": "Change request metadata and affected ids are required", "path": "metadata"})
    if not dependencies or not risks:
        issues.append({"code": "CR-IMPACT", "message": "Dependencies and risks must be explicitly recorded", "path": "impact"})
    return {
        "id": request_id, "title": title, "requester": requester, "change_type": change_type,
        "description": description, "impact": {"scope": impact_scope, "dependencies": dependencies, "risks": risks, "roadmap_effect": roadmap_effect},
        "affected_ids": affected_ids, "status": "draft" if issues else "under_review",
        "approval_required": True, "issues": issues,
    }


def approve_change_request(change_request: dict[str, Any], *, approver: str, decision_id: str) -> dict[str, Any]:
    result = dict(change_request)
    issues = list(result.get("issues", []))
    if result.get("status") != "under_review":
        issues.append({"code": "CR-APPROVAL-STATE", "message": "Only under-review requests can be approved", "path": "status"})
    if not approver or not decision_id.startswith("DEC-"):
        issues.append({"code": "CR-APPROVAL-AUTHORITY", "message": "Approver and DEC-* decision id are required", "path": "approval"})
    if issues:
        result["status"] = "rejected"
        result["issues"] = issues
        return result
    result.update({"status": "approved", "approved_by": approver, "decision_id": decision_id})
    return result
