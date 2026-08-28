"""Guarded review actions for records surfaced by the governance inbox."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .approval_inbox import COLLECTIONS
from .change_control import approve_change_request, build_decision_record
from .tenant_repository import TenantRepository


REVIEW_DECISIONS = {"returned", "rejected", "approved"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def review_inbox_item(
    *,
    repository: TenantRepository,
    collection: str,
    record_id: str,
    decision: str,
    decision_ref: str,
    rationale: str,
    reviewer: str,
    reviewer_role: str,
) -> dict[str, Any]:
    if reviewer_role != "program_owner":
        raise PermissionError("Governance inbox decisions require the program_owner role")
    if collection not in COLLECTIONS:
        raise ValueError("Record collection is not reviewable through the governance inbox")
    if decision not in REVIEW_DECISIONS:
        raise ValueError("decision must be returned, rejected, or approved")
    if not record_id or not decision_ref.startswith("DEC-") or not rationale.strip():
        raise ValueError("record_id, DEC-* decision_ref, and rationale are required")

    current = repository.get(collection, record_id)
    if current is None:
        raise KeyError(f"Unknown governance inbox record: {collection}/{record_id}")

    canonical_approval_performed = False
    if decision == "approved":
        if collection != "change_requests":
            raise ValueError("Approval must use the record's applicable workflow endpoint; this inbox action cannot bypass it")
        updated = approve_change_request(current, approver=reviewer, decision_id=decision_ref)
        if updated.get("status") != "approved":
            raise ValueError("The change request is not eligible for approval")
        canonical_approval_performed = True
    else:
        updated = dict(current)
        review_history = list(updated.get("review_history", []))
        review_history.append({
            "decision": decision,
            "decision_ref": decision_ref,
            "rationale": rationale.strip(),
            "reviewer": reviewer,
            "reviewed_at": _now(),
        })
        updated.update({
            "status": "needs_review" if decision == "returned" else "rejected",
            "review_history": review_history,
            "reviewed_by": reviewer,
            "review_decision_ref": decision_ref,
            "review_rationale": rationale.strip(),
            "human_review_required": decision == "returned",
        })

    decision_record = build_decision_record(
        decision_id=decision_ref,
        title=f"Governance review for {collection}/{record_id}",
        decision=decision,
        owner=reviewer,
        rationale=rationale.strip(),
        alternatives=["return for correction", "reject", "approve through the applicable workflow"],
        affected_ids=[record_id],
        status="approved",
    )
    decision_record.update({
        "organization_id": repository.organization_id,
        "collection": collection,
        "record_id": record_id,
        "reviewer_role": reviewer_role,
        "canonical_approval_performed": canonical_approval_performed,
        "created_at": _now(),
    })

    saved_item = repository.put(collection, record_id, updated, actor=reviewer, reason=f"governance_review_{decision}")
    saved_decision = repository.put("governance_review_decisions", decision_ref, decision_record, actor=reviewer, reason="governance_review_decision_recorded")
    return {
        "item": saved_item,
        "decision": saved_decision,
        "canonical_approval_performed": canonical_approval_performed,
        "approval_boundary": "Only change requests can be approved directly here; all other approvals require their applicable workflow endpoint.",
    }
