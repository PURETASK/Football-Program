"""Organization-scoped approval inbox for governance operators."""

from __future__ import annotations

from typing import Any

from .tenant_repository import TenantRepository


PENDING_STATES = {"draft", "under_review", "needs_review", "pending_approval", "blocked", "retryable"}
COLLECTIONS = ("play_drafts", "core_play_slices", "evidence_intelligence_slices", "game_plans", "rule_recommendations", "governance_audits", "release_candidates", "weekly_delivery_packages", "change_requests", "decisions", "knowledge_items", "film_observations", "media_processing_jobs")


def build_approval_inbox(*, repository: TenantRepository, role: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for collection in COLLECTIONS:
        for record in repository.list(collection):
            status = record.get("status") or record.get("approval_state")
            if status not in PENDING_STATES and not record.get("human_review_required") and not record.get("approval_required"):
                continue
            items.append({
                "collection": collection, "id": record.get("id"), "status": status,
                "owner": record.get("owner") or record.get("requester") or record.get("analyst") or record.get("requested_by"),
                "human_review_required": bool(record.get("human_review_required") or record.get("approval_required") or status in {"pending_approval", "under_review", "needs_review"}),
                "blockers": record.get("blockers", []) + record.get("issues", []),
                "evidence_refs": record.get("evidence_refs", []) + record.get("source_refs", []) + record.get("output_refs", []),
                "can_approve": role == "program_owner" and status in {"pending_approval", "under_review"},
            })
    return {"organization_id": repository.organization_id, "role": role, "items": sorted(items, key=lambda item: (item["collection"], item["id"] or "")), "count": len(items), "approval_boundary": "Approval actions require the applicable workflow endpoint and explicit human decision reference."}
