"""Runtime canonical-term and alias resolution for the NFL ontology."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OntologyResolver:
    def __init__(self, ontology_path: str | Path | None = None, *, terms: list[dict[str, Any]] | None = None, relationship_path: str | Path | None = None, alias_registry_path: str | Path | None = None):
        self.relationships: list[dict[str, Any]] = []
        self.controlled_aliases: dict[str, dict[str, Any]] = {}
        if terms is None:
            path = Path(ontology_path) if ontology_path else Path(__file__).resolve().parents[2] / "ontology" / "football-terms.json"
            with path.open(encoding="utf-8") as handle:
                terms = json.load(handle)["terms"]
            base = path.parent
            graph_path = Path(relationship_path) if relationship_path else base / "relationship-graph.json"
            alias_path = Path(alias_registry_path) if alias_registry_path else base / "alias-registry.json"
            if graph_path.exists():
                with graph_path.open(encoding="utf-8") as handle:
                    self.relationships = list(json.load(handle).get("edges", []))
            if alias_path.exists():
                with alias_path.open(encoding="utf-8") as handle:
                    entries = json.load(handle).get("entries", [])
                self.controlled_aliases = {self._normalize(entry["alias"]): dict(entry) for entry in entries if entry.get("alias")}
        self.terms = {term["id"]: dict(term) for term in terms}
        self._index: dict[str, list[str]] = {}
        for term in self.terms.values():
            for label in [term["label"], *term.get("aliases", [])]:
                self._index.setdefault(self._normalize(label), []).append(term["id"])
        for normalized, entry in self.controlled_aliases.items():
            term_id = entry.get("canonical_term_id")
            if term_id in self.terms:
                self._index.setdefault(normalized, [])
                if term_id not in self._index[normalized]:
                    self._index[normalized].append(term_id)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().replace("_", " ").split())

    def resolve(self, value: str) -> dict[str, Any]:
        candidates = self._index.get(self._normalize(value), [])
        if not candidates:
            return {"status": "unresolved", "input": value, "candidates": [], "requires_review": True}
        if len(candidates) > 1:
            return {"status": "ambiguous", "input": value, "candidates": candidates, "requires_review": True}
        term = self.terms[candidates[0]]
        return {"status": "resolved", "input": value, "term_id": term["id"], "label": term["label"], "category": term["category"], "definition": term["definition"], "requires_review": False}

    def related(self, term_id: str, *, relationship_type: str | None = None) -> list[dict[str, Any]]:
        """Return graph edges and resolved target terms for agent/tool consumption."""
        if term_id not in self.terms:
            return []
        matches = []
        for edge in self.relationships:
            if edge.get("from") != term_id and edge.get("to") != term_id:
                continue
            if relationship_type and edge.get("type") != relationship_type:
                continue
            other_id = edge.get("to") if edge.get("from") == term_id else edge.get("from")
            other = self.terms.get(other_id)
            if other:
                matches.append({"relationship": edge.get("type"), "direction": "outgoing" if edge.get("from") == term_id else "incoming", "term_id": other_id, "label": other.get("label"), "category": other.get("category")})
        return matches

    def validate(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        for term_id, term in self.terms.items():
            for field in ("id", "label", "category", "definition"):
                if not term.get(field):
                    issues.append({"code": "ONTOLOGY-REQUIRED", "message": f"Term {term_id} lacks {field}", "path": term_id})
        for label, candidates in self._index.items():
            if len(candidates) > 1:
                issues.append({"code": "ONTOLOGY-AMBIGUOUS-ALIAS", "message": f"Alias maps to multiple terms: {label}", "path": label})
        for edge in self.relationships:
            if edge.get("from") not in self.terms or edge.get("to") not in self.terms:
                issues.append({"code": "ONTOLOGY-UNKNOWN-RELATIONSHIP", "message": "Relationship references an unknown term", "path": str(edge)})
        return issues
