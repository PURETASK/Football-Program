"""Controlled scheme-family dossier validation for Stages 6 and 7."""

from __future__ import annotations

from typing import Any


REQUIRED_DOSSIER_FIELDS = (
    "id", "unit", "name", "identity", "components", "personnel_fit", "teaching_cost",
    "strengths", "weaknesses", "counters", "counter_counters", "adaptation_logic",
    "installation_requirements", "nuance",
)


def validate_scheme_dossier(dossier: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(dossier.get("id"), str) or not dossier["id"].startswith("SCHEME-FAM-"):
        issues.append({"code":"DOSSIER-ID", "message":"Scheme-family id must start with SCHEME-FAM-", "path":"id"})
    if dossier.get("unit") not in {"offense", "defense"}:
        issues.append({"code":"DOSSIER-UNIT", "message":"Dossier unit must be offense or defense", "path":"unit"})
    for field in REQUIRED_DOSSIER_FIELDS:
        value = dossier.get(field)
        if value in (None, "", []):
            issues.append({"code":"DOSSIER-REQUIRED", "message":f"Missing required dossier field: {field}", "path":field})
    for field in ("components", "personnel_fit", "strengths", "weaknesses", "counters", "counter_counters", "adaptation_logic", "installation_requirements", "nuance"):
        if field in dossier and (not isinstance(dossier[field], list) or not dossier[field]):
            issues.append({"code":"DOSSIER-LIST", "message":f"Dossier field must be a non-empty list: {field}", "path":field})
    if dossier.get("counters") and not dossier.get("counter_counters"):
        issues.append({"code":"DOSSIER-COUNTER", "message":"Counters require counter-counter logic", "path":"counter_counters"})
    return issues


def validate_scheme_bible(bible: dict[str, Any]) -> dict[str, Any]:
    """Validate coverage of the controlled starter dossier library."""
    issues: list[str] = []
    families = bible.get("families", [])
    ids: set[str] = set()
    for family in families:
        if family.get("id") in ids:
            issues.append(f"duplicate dossier id: {family.get('id')}")
        ids.add(family.get("id"))
        issues.extend(f"{family.get('id')}: {item['message']}" for item in validate_scheme_dossier(family))
    units = {family.get("unit") for family in families}
    if "offense" not in units or "defense" not in units:
        issues.append("starter library must cover both offense and defense")
    return {"bible_id": bible.get("bible_id"), "status":"valid" if not issues else "invalid", "errors":issues, "family_count":len(families), "units":sorted(units)}
