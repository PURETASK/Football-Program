"""Persistent, organization-scoped team terminology controls."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .ontology import OntologyResolver
from .tenant_repository import TenantRepository


class TeamOntologyService:
    def __init__(self, repository: TenantRepository, resolver: OntologyResolver | None = None):
        self.repository = repository
        self.resolver = resolver or OntologyResolver()

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    @staticmethod
    def _record_id(team_id: str, alias: str) -> str:
        safe = "-".join(TeamOntologyService._normalize(alias).split())
        return f"TEAM-ALIAS-{team_id}-{safe}"

    def lock_alias(self, *, team_id: str, alias: str, term_id: str, owner: str, reason: str, source_refs: list[str], approval_ref: str, actor: str) -> dict[str, Any]:
        if not team_id or not alias or not owner or not reason:
            raise ValueError("team_id, alias, owner, and reason are required")
        if not source_refs or not approval_ref:
            raise ValueError("source_refs and approval_ref are required before a team alias can be locked")
        if term_id not in self.resolver.terms:
            raise ValueError("term_id does not exist in the canonical ontology")
        record_id = self._record_id(team_id, alias)
        existing = self.repository.get("team_aliases", record_id)
        if existing and existing.get("term_id") != term_id:
            raise ValueError("team alias is already locked to another canonical term")
        record = {
            "id": record_id,
            "organization_id": self.repository.organization_id,
            "team_id": team_id,
            "alias": alias,
            "normalized_alias": self._normalize(alias),
            "term_id": term_id,
            "owner": owner,
            "reason": reason,
            "source_refs": list(source_refs),
            "approval_ref": approval_ref,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "status": "locked",
        }
        return self.repository.put("team_aliases", record_id, record, actor=actor, reason="team_alias_locked")

    def resolve(self, *, team_id: str | None, value: str) -> dict[str, Any]:
        if team_id:
            normalized = self._normalize(value)
            matches = [record for record in self.repository.list("team_aliases") if record.get("team_id") == team_id and record.get("normalized_alias") == normalized and record.get("status") == "locked"]
            if len(matches) == 1:
                term = self.resolver.terms[matches[0]["term_id"]]
                return {"status": "resolved_team_alias", "team_id": team_id, "input": value, "term_id": term["id"], "label": term["label"], "category": term["category"], "team_alias": matches[0]["alias"], "requires_review": False}
            if len(matches) > 1:
                return {"status": "ambiguous", "team_id": team_id, "input": value, "candidates": [item["term_id"] for item in matches], "requires_review": True}
        result = self.resolver.resolve(value)
        if team_id:
            result["team_id"] = team_id
        return result

    def list_aliases(self, *, team_id: str | None = None) -> list[dict[str, Any]]:
        records = self.repository.list("team_aliases")
        if team_id:
            records = [record for record in records if record.get("team_id") == team_id]
        return sorted(records, key=lambda record: record.get("id", ""))


def validate_team_alias_record(record: dict[str, Any]) -> list[str]:
    required = ("id", "organization_id", "team_id", "alias", "term_id", "owner", "reason", "source_refs", "approval_ref", "approved_at", "status")
    issues = [f"missing {field}" for field in required if not record.get(field)]
    if record.get("status") == "locked" and not record.get("source_refs"):
        issues.append("locked alias requires source_refs")
    if record.get("team_id") and not str(record["team_id"]).startswith("TEAM-"):
        issues.append("team_id must start with TEAM-")
    return issues
