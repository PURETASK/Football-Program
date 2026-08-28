"""Tenant-scoped playbook authoring, review, and role-view workspace."""

from __future__ import annotations

from typing import Any

from .playbook_architecture import approve_play, build_extended_play, extract_role_play_spec, request_play_approval
from .tenant_repository import TenantRepository


class PlaybookWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_draft(
        self, *, play: dict[str, Any], play_family_id: str, install_level: str,
        checks: list[dict[str, Any]], situational_variants: list[dict[str, Any]],
        opponent_notes: list[str], coaching_notes: list[str], dependencies: list[str], actor: str,
    ) -> dict[str, Any]:
        play = dict(play)
        play.setdefault("status", "draft")
        extended = build_extended_play(
            play, play_family_id=play_family_id, install_level=install_level,
            checks=checks, situational_variants=situational_variants,
            opponent_notes=opponent_notes, coaching_notes=coaching_notes,
            dependencies=dependencies,
        )
        extended["organization_id"] = self.repository.organization_id
        if extended["status"] != "draft":
            return {"status": "rejected", "play": extended, "issues": extended["spec_issues"], "human_review_required": True}
        return self.repository.put("playbook_drafts", extended["id"], extended, actor=actor, reason="playbook_draft_created")

    def request_approval(self, *, play_id: str, requester: str, decision_ref: str) -> dict[str, Any]:
        draft = self.repository.get("playbook_drafts", play_id)
        if draft is None:
            raise KeyError(f"Unknown playbook draft: {play_id}")
        requested = request_play_approval(draft, requester=requester, decision_ref=decision_ref)
        return self.repository.put("playbook_drafts", play_id, requested, actor=requester, reason="playbook_approval_requested")

    def approve(self, *, play_id: str, approver: str, decision_ref: str) -> dict[str, Any]:
        draft = self.repository.get("playbook_drafts", play_id)
        if draft is None:
            raise KeyError(f"Unknown playbook draft: {play_id}")
        approved = approve_play(draft, approver=approver, decision_ref=decision_ref)
        self.repository.put("playbook_drafts", play_id, approved, actor=approver, reason="playbook_approval_decision")
        if approved["approval"]["state"] == "approved":
            return self.repository.put("plays", play_id, approved, actor=approver, reason="playbook_locked_publish")
        return approved

    def workspace(self, *, include_rejected: bool = False) -> dict[str, Any]:
        drafts = self.repository.list("playbook_drafts")
        if not include_rejected:
            drafts = [draft for draft in drafts if draft.get("status") != "rejected" and draft.get("approval", {}).get("state") != "rejected"]
        return {"organization_id": self.repository.organization_id, "status": "ready" if drafts else "empty", "drafts": drafts, "human_review_required": any(draft.get("approval", {}).get("state") != "approved" for draft in drafts)}

    def role_view(self, *, play_id: str, role: str) -> dict[str, Any]:
        draft = self.repository.get("playbook_drafts", play_id)
        if draft is None:
            raise KeyError(f"Unknown playbook draft: {play_id}")
        return extract_role_play_spec(draft, role=role)
