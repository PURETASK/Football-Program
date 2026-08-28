"""Versioned, source-linked organization terminology bundles."""

from __future__ import annotations

from typing import Any

from .ontology import OntologyResolver


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def validate_organization_terminology(bundle: dict[str, Any], *, resolver: OntologyResolver | None = None) -> dict[str, Any]:
    resolver = resolver or OntologyResolver()
    issues: list[str] = []
    for field in ("id", "organization_id", "team_id", "season", "version", "owner", "source_refs", "approval_ref", "aliases", "status"):
        if not bundle.get(field) and bundle.get(field) != []:
            issues.append(f"missing {field}")
    if bundle.get("id") and not str(bundle["id"]).startswith("TERM-BUNDLE-"):
        issues.append("id must start with TERM-BUNDLE-")
    if bundle.get("organization_id") and not str(bundle["organization_id"]).startswith("ORG-"):
        issues.append("organization_id must start with ORG-")
    if bundle.get("team_id") and not str(bundle["team_id"]).startswith("TEAM-"):
        issues.append("team_id must start with TEAM-")
    if bundle.get("status") == "approved" and (not bundle.get("source_refs") or not bundle.get("approval_ref")):
        issues.append("approved terminology requires source_refs and approval_ref")
    seen: set[str] = set()
    for index, alias in enumerate(bundle.get("aliases", [])):
        key = _normalize(alias.get("alias", ""))
        if not key or key in seen:
            issues.append(f"aliases[{index}] is missing or duplicates a normalized alias")
        seen.add(key)
        if alias.get("term_id") not in resolver.terms:
            issues.append(f"aliases[{index}] references an unknown canonical term")
        if not alias.get("source_refs") or not alias.get("approval_ref"):
            issues.append(f"aliases[{index}] requires source_refs and approval_ref")
        if alias.get("status") not in {"locked", "review_required", "rejected"}:
            issues.append(f"aliases[{index}] has an invalid status")
    return {"id": bundle.get("id"), "status": "valid" if not issues else "invalid", "errors": issues, "alias_count": len(bundle.get("aliases", [])), "organization_id": bundle.get("organization_id"), "team_id": bundle.get("team_id")}


def resolve_organization_term(bundle: dict[str, Any], value: str, *, resolver: OntologyResolver | None = None) -> dict[str, Any]:
    resolver = resolver or OntologyResolver()
    normalized = _normalize(value)
    matches = [alias for alias in bundle.get("aliases", []) if _normalize(alias.get("alias", "")) == normalized and alias.get("status") == "locked"]
    if len(matches) == 1:
        term = resolver.terms[matches[0]["term_id"]]
        return {"status":"resolved_organization_alias", "input":value, "organization_id":bundle.get("organization_id"), "team_id":bundle.get("team_id"), "term_id":term["id"], "label":term["label"], "source_refs":matches[0].get("source_refs", []), "approval_ref":matches[0].get("approval_ref"), "requires_review":False}
    if len(matches) > 1:
        return {"status":"ambiguous", "input":value, "organization_id":bundle.get("organization_id"), "team_id":bundle.get("team_id"), "candidates":[item.get("term_id") for item in matches], "requires_review":True}
    result = resolver.resolve(value)
    result.update({"organization_id":bundle.get("organization_id"), "team_id":bundle.get("team_id")})
    return result
