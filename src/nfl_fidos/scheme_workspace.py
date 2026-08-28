"""Compositional scheme workspace with review and red-team visibility."""

from __future__ import annotations

from typing import Any

from .scheme import build_scheme
from .tenant_repository import TenantRepository


class SchemeWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def save_scheme(self, *, scheme: dict[str, Any], actor: str) -> dict[str, Any]:
        record = dict(scheme)
        result = build_scheme(record)
        record.update({"status": result.get("status", "invalid"), "issues": result.get("issues", []), "organization_id": self.repository.organization_id, "human_review_required": True})
        if record["status"] == "validated":
            return self.repository.put("schemes", record["id"], record, actor=actor, reason="scheme_workspace_saved")
        return record

    def workspace(self, *, unit: str | None = None) -> dict[str, Any]:
        schemes = self.repository.list("schemes")
        if unit:
            schemes = [scheme for scheme in schemes if scheme.get("unit") == unit]
        compatibility = self.repository.list("compatibility_results")
        red_team = self.repository.list("red_team_matrices")
        pending = [scheme for scheme in schemes if scheme.get("status") in {"draft", "under_review", "invalid"}]
        return {"organization_id":self.repository.organization_id, "status":"ready" if schemes else "empty", "unit":unit, "schemes":schemes, "compatibility_results":compatibility, "red_team_matrices":red_team, "pending_review_count":len(pending), "human_review_required":bool(schemes), "incompatibility_count":sum(1 for item in compatibility if item.get("compatible") is False)}
