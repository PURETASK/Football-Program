"""Organization-scoped drill validation package with an explicit human-review boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
from typing import Any

from .position_drill_library import load_position_drill_library
from .seasonal_role_drill_variants import load_seasonal_role_variants, validate_seasonal_role_variants


def _available_drills() -> dict[str, dict[str, Any]]:
    base = {drill.get("id"): drill for entry in load_position_drill_library().get("positions", []) for drill in entry.get("drills", [])}
    variants = load_seasonal_role_variants().get("variants", [])
    return {**base, **{variant.get("variant_id"): variant for variant in variants}}


def build_organization_drill_validation(*, validation_id: str, organization_id: str, season: str, position: str, selected_drill_ids: list[str], source_refs: list[str], validator: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues = validate_organization_drill_selection(organization_id=organization_id, season=season, position=position, selected_drill_ids=selected_drill_ids, source_refs=source_refs, validator=validator)
    return {
        "id": validation_id,
        "organization_id": organization_id,
        "season": season,
        "position": position,
        "selected_drill_ids": list(selected_drill_ids),
        "source_refs": list(source_refs),
        "validator": validator,
        "status": "under_review" if not issues else "rejected",
        "human_review_required": True,
        "owner_decision_ref": owner_decision_ref,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
    }


def validate_organization_drill_selection(*, organization_id: str, season: str, position: str, selected_drill_ids: list[str], source_refs: list[str], validator: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "ORG-DRILL-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not season.strip():
        issues.append({"code": "ORG-DRILL-SEASON", "message": "season is required", "path": "season"})
    if not position.strip():
        issues.append({"code": "ORG-DRILL-POSITION", "message": "position is required", "path": "position"})
    if not selected_drill_ids:
        issues.append({"code": "ORG-DRILL-SELECTION", "message": "at least one drill must be selected", "path": "selected_drill_ids"})
    if not source_refs:
        issues.append({"code": "ORG-DRILL-SOURCE", "message": "authorized source references are required", "path": "source_refs"})
    if not validator:
        issues.append({"code": "ORG-DRILL-VALIDATOR", "message": "validator identity is required", "path": "validator"})
    variants_result = validate_seasonal_role_variants(variants_library=load_seasonal_role_variants())
    if variants_result["status"] != "valid":
        issues.append({"code": "ORG-DRILL-CORPUS", "message": "seasonal variant corpus must validate before organization selection", "path": "corpus"})
    available = _available_drills()
    for index, drill_id in enumerate(selected_drill_ids):
        drill = available.get(drill_id)
        if drill is None:
            issues.append({"code": "ORG-DRILL-UNKNOWN", "message": f"Unknown drill selection: {drill_id}", "path": f"selected_drill_ids[{index}]"})
            continue
        drill_position = drill.get("position")
        if drill_position and drill_position != position:
            issues.append({"code": "ORG-DRILL-POSITION-LINK", "message": "Selected drill does not match the requested position", "path": f"selected_drill_ids[{index}]"})
    return issues


def approve_organization_drill_validation(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    """Apply an explicit owner decision without enabling production or stage advancement."""
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-DRILL-STATE", "message": "Only an under_review package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-DRILL-ROLE", "message": "Only a program_owner may validate an organization drill package", "path": "approver_role"})
    if not isinstance(decision_ref, str) or not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-DRILL-DECISION", "message": "A DEC-* or APPROVAL-* decision reference is required", "path": "decision_ref"})
    if not approver:
        issues.append({"code": "ORG-DRILL-APPROVER", "message": "Approver identity is required", "path": "approver"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        result["status"] = "under_review"
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "approved_at": datetime.now(timezone.utc).isoformat(), "owner_decision_ref": decision_ref, "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
