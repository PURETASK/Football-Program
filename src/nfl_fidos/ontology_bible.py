"""Validation and coverage reporting for the controlled NFL ontology artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict[str, Any]:
    with (ROOT / "ontology" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_ontology_bible(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root) if root else ROOT
    with (base / "ontology" / "football-terms.json").open(encoding="utf-8") as handle:
        terms_doc = json.load(handle)
    with (base / "ontology" / "alias-registry.json").open(encoding="utf-8") as handle:
        aliases_doc = json.load(handle)
    with (base / "ontology" / "relationship-graph.json").open(encoding="utf-8") as handle:
        graph_doc = json.load(handle)
    with (base / "ontology" / "naming-standard.json").open(encoding="utf-8") as handle:
        naming_doc = json.load(handle)

    term_ids = {term.get("id") for term in terms_doc.get("terms", [])}
    issues: list[str] = []
    seen_aliases: set[str] = set()
    for entry in aliases_doc.get("entries", []):
        alias = str(entry.get("alias", "")).casefold()
        if not alias or entry.get("canonical_term_id") not in term_ids:
            issues.append(f"invalid alias entry: {entry}")
        if alias in seen_aliases:
            issues.append(f"duplicate alias: {alias}")
        seen_aliases.add(alias)
    valid_types = set(graph_doc.get("relationship_types", []))
    for edge in graph_doc.get("edges", []):
        if edge.get("from") not in term_ids or edge.get("to") not in term_ids:
            issues.append(f"relationship references unknown term: {edge}")
        if edge.get("type") not in valid_types:
            issues.append(f"unknown relationship type: {edge}")
    for term_id in term_ids:
        if not re.fullmatch(r"TERM-[A-Z0-9-]+", str(term_id)):
            issues.append(f"term id violates naming standard: {term_id}")

    categories = sorted({term.get("category") for term in terms_doc.get("terms", []) if term.get("category")})
    required = naming_doc.get("required_work_packages", [])
    category_map = {
        "positions": "position", "archetypes": "archetype", "personnel": "personnel", "alignments": "alignment", "formations": "formation",
        "motions": "motion", "blocking": "blocking", "runs": "run_concept", "routes": "route_family", "passes": "pass_concept", "protections": "protection",
        "play_action": "play_action", "screens": "screen", "rpo_option": "rpo_option", "coverages": "coverage", "match_rules": "match_rule",
        "pressures": "pressure", "run_fits": "run_fit", "landmarks": "landmark", "situations": "situation", "reads": "read", "checks": "check", "special_teams": "special_teams",
    }
    missing_work_packages = [item for item in required if not category_map.get(item) or category_map[item] not in categories]
    return {
        "status": "valid" if not issues else "invalid",
        "term_count": len(term_ids),
        "category_count": len(categories),
        "categories": categories,
        "alias_count": len(aliases_doc.get("entries", [])),
        "relationship_count": len(graph_doc.get("edges", [])),
        "missing_work_packages": missing_work_packages,
        "issues": issues,
        "expansion_required": bool(missing_work_packages) or terms_doc.get("status") != "complete",
    }
