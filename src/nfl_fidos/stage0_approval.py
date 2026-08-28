"""Explicit, non-activating Stage 0 owner-approval evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def build_stage0_owner_approval(
    *,
    approval_id: str,
    gate_result: dict[str, Any],
    registry_id: str,
    approver: str,
    rationale: str,
    evidence_refs: list[str],
    approved_at: str,
) -> dict[str, Any]:
    """Create a record only when the gate is ready and the approver is the owner.

    This function records evidence; it never changes ``control/manifest.json``
    and never enables production implementation or stage advancement.
    """
    issues: list[dict[str, str]] = []
    if not approval_id.startswith("APPROVAL-STAGE0-"):
        issues.append({"code":"STAGE0-APPROVAL-ID","message":"Approval id must start with APPROVAL-STAGE0-","path":"approval_id"})
    if gate_result.get("status") != "ready_for_approval":
        issues.append({"code":"STAGE0-GATE-NOT-READY","message":"Stage 0 exit gate must be ready_for_approval before owner approval can be recorded","path":"gate_result.status"})
    if gate_result.get("gate_id") != "STAGE0-EXIT-001":
        issues.append({"code":"STAGE0-GATE-ID","message":"Approval must reference STAGE0-EXIT-001","path":"gate_result.gate_id"})
    if not registry_id or registry_id != gate_result.get("registry_id"):
        issues.append({"code":"STAGE0-REGISTRY","message":"Approval registry id must match the evaluated registry","path":"registry_id"})
    if not approver or not rationale or not evidence_refs:
        issues.append({"code":"STAGE0-APPROVAL-METADATA","message":"Approver, rationale, and evidence references are required","path":"metadata"})
    if not isinstance(approved_at, str):
        issues.append({"code":"STAGE0-APPROVAL-TIME","message":"approved_at must be an ISO-8601 string","path":"approved_at"})
    else:
        try:
            datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
        except ValueError:
            issues.append({"code":"STAGE0-APPROVAL-TIME","message":"approved_at must be an ISO-8601 timestamp","path":"approved_at"})
    return {
        "id": approval_id,
        "stage":"STAGE-0",
        "work_package":"STAGE-0A",
        "gate_id":"STAGE0-EXIT-001",
        "registry_id":registry_id,
        "decision":"approved" if not issues else "rejected",
        "approver":approver,
        "approver_role":"program_owner",
        "approved_at":approved_at,
        "rationale":rationale,
        "evidence_refs":list(evidence_refs),
        "production_implementation_allowed":False,
        "stage_advance_authorized":False,
        "issues":issues,
    }


def validate_stage0_owner_approval(record: dict[str, Any], *, gate_result: dict[str, Any]) -> dict[str, Any]:
    """Validate persisted evidence without treating it as a stage transition."""
    issues = list(record.get("issues", []))
    required = ("id","stage","work_package","gate_id","registry_id","decision","approver","approver_role","approved_at","rationale","evidence_refs")
    issues.extend({"code":"STAGE0-APPROVAL-FIELD","message":f"Missing required field: {field}","path":field} for field in required if field not in record)
    if record.get("decision") != "approved":
        issues.append({"code":"STAGE0-APPROVAL-DECISION","message":"Owner approval decision is not approved","path":"decision"})
    if record.get("approver_role") != "program_owner":
        issues.append({"code":"STAGE0-APPROVAL-ROLE","message":"Only program_owner may approve the Stage 0 exit","path":"approver_role"})
    if record.get("production_implementation_allowed") is not False or record.get("stage_advance_authorized") is not False:
        issues.append({"code":"STAGE0-APPROVAL-SAFETY","message":"Approval evidence cannot enable production or automatically advance the stage","path":"safety"})
    if record.get("gate_id") != gate_result.get("gate_id") or record.get("registry_id") != gate_result.get("registry_id"):
        issues.append({"code":"STAGE0-APPROVAL-LINK","message":"Approval must link to the evaluated gate and registry","path":"links"})
    return {"status":"valid" if not issues else "invalid", "stage":"STAGE-0", "production_implementation_allowed":False, "stage_advance_authorized":False, "issues":issues, "record":record}
