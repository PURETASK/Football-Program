"""Organization-specific scheme and special-teams doctrine review boundary."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scheme_family_corpus import load_scheme_family_corpus
from .special_teams_bible import validate_special_teams_bible


def _special_teams_bible() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "special_teams" / "special-teams-bible.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_organization_doctrine(*, doctrine_id: str, organization_id: str, team_context: str, season: str, scheme_family_ids: list[str], special_teams_unit_ids: list[str], source_refs: list[str], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not doctrine_id.startswith("ORG-DOCTRINE-"):
        issues.append({"code": "ORG-DOCTRINE-ID", "message": "Doctrine id must use ORG-DOCTRINE- prefix", "path": "id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "ORG-DOCTRINE-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not team_context or not season or not compiler:
        issues.append({"code": "ORG-DOCTRINE-METADATA", "message": "team_context, season, and compiler are required", "path": "metadata"})
    if not source_refs:
        issues.append({"code": "ORG-DOCTRINE-SOURCE", "message": "source_refs are required", "path": "source_refs"})
    if not scheme_family_ids and not special_teams_unit_ids:
        issues.append({"code": "ORG-DOCTRINE-EMPTY", "message": "At least one scheme family or special-teams unit is required", "path": "entries"})
    families = {item.get("id"): item for item in load_scheme_family_corpus().get("families", [])}
    units = {item.get("id"): item for item in _special_teams_bible().get("units", [])}
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, family_id in enumerate(scheme_family_ids):
        entry_id = f"{doctrine_id}-SCHEME-{index + 1:03d}"
        entry = {"id": entry_id, "kind": "scheme_family", "reference_id": family_id, "unit": families.get(family_id, {}).get("unit"), "team_context": team_context, "source_ref": source_refs[0] if source_refs else None, "review_status": "review_required"}
        if entry_id in seen:
            issues.append({"code": "ORG-DOCTRINE-DUPLICATE", "message": "Duplicate doctrine entry id", "path": f"scheme_family_ids[{index}]"})
        seen.add(entry_id)
        if family_id not in families:
            issues.append({"code": "ORG-DOCTRINE-SCHEME", "message": "Unknown scheme family reference", "path": f"scheme_family_ids[{index}]"})
        entries.append(entry)
    for index, unit_id in enumerate(special_teams_unit_ids):
        entry_id = f"{doctrine_id}-SPECIAL-{index + 1:03d}"
        entry = {"id": entry_id, "kind": "special_teams_unit", "reference_id": unit_id, "unit": units.get(unit_id, {}).get("unit"), "team_context": team_context, "source_ref": source_refs[0] if source_refs else None, "review_status": "review_required"}
        if unit_id not in units:
            issues.append({"code": "ORG-DOCTRINE-SPECIAL", "message": "Unknown special-teams unit reference", "path": f"special_teams_unit_ids[{index}]"})
        entries.append(entry)
    if not validate_special_teams_bible(_special_teams_bible()).get("status") == "valid":
        issues.append({"code": "ORG-DOCTRINE-REFERENCE", "message": "Canonical special-teams reference is invalid", "path": "references"})
    return {"id": doctrine_id, "organization_id": organization_id, "team_context": team_context, "season": season, "source_refs": list(source_refs), "entries": entries, "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_doctrine(*, doctrine: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(doctrine)
    issues: list[dict[str, str]] = []
    if doctrine.get("status") != "under_review":
        issues.append({"code": "ORG-DOCTRINE-STATE", "message": "Only an under_review doctrine package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-DOCTRINE-ROLE", "message": "Only a program_owner may validate organization doctrine", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-DOCTRINE-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
