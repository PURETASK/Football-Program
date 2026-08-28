"""Team-specific terminology and context controls."""

from __future__ import annotations

from typing import Any

from .ontology import OntologyResolver


class TeamContextRegistry:
    def __init__(self, resolver: OntologyResolver):
        self.resolver = resolver
        self._aliases: dict[str, dict[str, dict[str, Any]]] = {}

    def lock_alias(self, *, team_id: str, alias: str, term_id: str, owner: str, reason: str) -> dict[str, Any]:
        if not team_id or not alias or not owner or not reason:
            raise ValueError({"code": "TEAM-ALIAS-METADATA", "message": "Team, alias, owner, and reason are required"})
        if term_id not in self.resolver.terms:
            raise ValueError({"code": "TEAM-ALIAS-TERM", "message": "Term does not exist in canonical ontology"})
        key = " ".join(alias.casefold().split())
        existing = self._aliases.setdefault(team_id, {}).get(key)
        if existing and existing["term_id"] != term_id:
            raise ValueError({"code": "TEAM-ALIAS-CONFLICT", "message": "Alias is already locked to another term"})
        record = {"team_id": team_id, "alias": alias, "term_id": term_id, "owner": owner, "reason": reason, "status": "locked"}
        self._aliases[team_id][key] = record
        return dict(record)

    def resolve(self, *, team_id: str, value: str) -> dict[str, Any]:
        key = " ".join(value.casefold().split())
        team_alias = self._aliases.get(team_id, {}).get(key)
        if team_alias:
            term = self.resolver.terms[team_alias["term_id"]]
            return {"status": "resolved_team_alias", "team_id": team_id, "input": value, "term_id": term["id"], "label": term["label"], "team_alias": team_alias["alias"], "requires_review": False}
        result = self.resolver.resolve(value)
        result["team_id"] = team_id
        return result

    def export(self, team_id: str) -> list[dict[str, Any]]:
        return [dict(record) for record in self._aliases.get(team_id, {}).values()]
