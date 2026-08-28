"""Privacy-scoped player assignment and Today workspace services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PlayerWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_assignment(self, *, assignment_id: str, player_id: str, title: str, assignment_type: str, artifact_id: str, due_date: str | None, owner: str, source_refs: list[str], actor: str) -> dict[str, Any]:
        issues: list[str] = []
        if not assignment_id.startswith("ASSIGNMENT-"):
            issues.append("assignment id must start with ASSIGNMENT-")
        if not player_id or not title or not assignment_type or not artifact_id or not owner or not source_refs:
            issues.append("player, title, type, artifact, owner, and source refs are required")
        assignment = {"id":assignment_id, "organization_id":self.repository.organization_id, "player_id":player_id, "title":title, "assignment_type":assignment_type, "artifact_id":artifact_id, "due_date":due_date, "owner":owner, "source_refs":source_refs, "status":"assigned" if not issues else "invalid", "created_at":_now(), "issues":issues, "human_review_required":False}
        if assignment["status"] == "assigned":
            return self.repository.put("player_assignments", assignment_id, assignment, actor=actor, reason="player_assignment_created")
        return assignment

    def today(self, *, player_id: str) -> dict[str, Any]:
        def owned(record: dict[str, Any]) -> bool:
            return player_id in {record.get("player_id"), record.get("athlete_id"), record.get("participant"), record.get("learner_id")}
        assignments = [record for record in self.repository.list("player_assignments") if record.get("player_id") == player_id]
        lessons = [record for record in self.repository.list("lessons") if owned(record)]
        mastery = [record for record in self.repository.list("mastery_records") if owned(record)]
        plans = [record for record in self.repository.list("development_plans") if owned(record)]
        quizzes = [record for record in self.repository.list("film_quiz_attempts") if owned(record)]
        return {"organization_id":self.repository.organization_id, "player_id":player_id, "status":"ready" if any((assignments, lessons, mastery, plans, quizzes)) else "empty", "assignments":assignments, "lessons":lessons, "mastery":mastery, "development_plans":plans, "quiz_attempts":quizzes, "next_step":assignments[0] if assignments else None, "privacy":"only records belonging to this player are returned"}
