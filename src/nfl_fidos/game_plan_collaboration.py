"""Organization-scoped staff review threads for weekly game plans."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


REVIEW_ROLES = {"coach_staff", "analyst", "program_owner", "validator"}
DECISIONS = {"accepted", "deferred", "rejected"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GamePlanCollaborationService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_thread(self, *, thread_id: str, plan_id: str, week: str, topic: str, comment: str, evidence_refs: list[str], author: str, role: str) -> dict[str, Any]:
        issues: list[str] = []
        if not thread_id.startswith("GAMEPLAN-THREAD-"):
            issues.append("thread_id must start with GAMEPLAN-THREAD-")
        if not plan_id.startswith("GAMEPLAN-"):
            issues.append("plan_id must start with GAMEPLAN-")
        if not week or not topic or not comment or not author:
            issues.append("week, topic, comment, and author are required")
        if role not in REVIEW_ROLES:
            issues.append("role is not authorized for game-plan collaboration")
        if not evidence_refs:
            issues.append("at least one evidence reference is required")
        if issues:
            return {"id": thread_id, "status": "rejected", "issues": issues, "organization_id": self.repository.organization_id, "human_decision_required": True}
        thread = {
            "id": thread_id, "organization_id": self.repository.organization_id, "plan_id": plan_id,
            "week": week, "topic": topic, "status": "open", "created_by": author, "created_role": role,
            "created_at": _now(), "comments":[{"id":f"COMMENT-{thread_id}", "author":author, "role":role, "body":comment, "evidence_refs":evidence_refs, "created_at":_now()}],
            "decision": None, "human_decision_required": True,
        }
        return self.repository.put("game_plan_review_threads", thread_id, thread, actor=author, reason="game_plan_review_thread_created")

    def append_comment(self, *, thread_id: str, comment_id: str, comment: str, evidence_refs: list[str], author: str, role: str) -> dict[str, Any]:
        if role not in REVIEW_ROLES:
            raise PermissionError("role is not authorized for game-plan collaboration")
        if not comment_id.startswith("COMMENT-") or not comment or not evidence_refs:
            raise ValueError("comment_id, comment, and evidence_refs are required")
        thread = self.repository.get("game_plan_review_threads", thread_id)
        if thread is None:
            raise KeyError(f"Unknown review thread: {thread_id}")
        if thread.get("status") != "open":
            raise ValueError("resolved review threads cannot receive comments")
        thread.setdefault("comments", []).append({"id":comment_id, "author":author, "role":role, "body":comment, "evidence_refs":evidence_refs, "created_at":_now()})
        return self.repository.put("game_plan_review_threads", thread_id, thread, actor=author, reason="game_plan_review_comment_added")

    def resolve_thread(self, *, thread_id: str, decision: str, decision_ref: str, resolver: str, role: str, rationale: str) -> dict[str, Any]:
        if role not in {"coach_staff", "program_owner", "validator"}:
            raise PermissionError("only coaching, owner, or validator roles may resolve a review thread")
        if decision not in DECISIONS or not decision_ref.startswith("DEC-") or not rationale:
            raise ValueError("decision, DEC-* decision_ref, and rationale are required")
        thread = self.repository.get("game_plan_review_threads", thread_id)
        if thread is None:
            raise KeyError(f"Unknown review thread: {thread_id}")
        if thread.get("status") != "open":
            raise ValueError("review thread is already resolved")
        thread.update({"status":"resolved", "decision":{"decision":decision, "decision_ref":decision_ref, "rationale":rationale, "resolved_by":resolver, "resolved_role":role, "resolved_at":_now()}, "human_decision_required":False})
        return self.repository.put("game_plan_review_threads", thread_id, thread, actor=resolver, reason="game_plan_review_thread_resolved")

    def workspace(self, *, plan_id: str | None = None) -> dict[str, Any]:
        threads = self.repository.list("game_plan_review_threads")
        if plan_id:
            threads = [thread for thread in threads if thread.get("plan_id") == plan_id]
        return {"organization_id":self.repository.organization_id, "status":"ready" if threads else "empty", "threads":threads, "open_thread_count":sum(1 for thread in threads if thread.get("status") == "open"), "human_decision_required":any(thread.get("status") == "open" for thread in threads)}
