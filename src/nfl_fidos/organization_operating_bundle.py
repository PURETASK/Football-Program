"""Compose organization packages into one owner-reviewed operating boundary.

This module deliberately does not activate an organization.  It verifies that
the independently validated tenant packages agree on organization and season,
then emits a value-free readiness record for a program owner to review.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


REQUIRED_COMPONENTS = (
    "organization_context",
    "terminology_bundle",
    "doctrine",
    "play_corpus",
    "player_development",
    "staff_review",
    "drill_validation",
    "special_teams",
    "performance",
    "media_review",
    "scouting",
    "analytics",
    "game_plan",
)

COMPONENT_COLLECTIONS = {
    "organization_context": "organizations",
    "terminology_bundle": "organization_terminology_bundles",
    "doctrine": "organization_doctrine_packages",
    "play_corpus": "organization_play_corpora",
    "player_development": "organization_player_development_packages",
    "staff_review": "organization_staff_packages",
    "drill_validation": "organization_drill_validations",
    "special_teams": "organization_special_teams_packages",
    "performance": "organization_performance_packages",
    "media_review": "organization_media_review_packages",
    "scouting": "organization_scouting_packages",
    "analytics": "organization_analytics_packages",
    "game_plan": "organization_game_plan_packages",
}


def load_persisted_organization_components(tenant: Any, component_ids: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """Resolve persisted tenant-scoped packages without bypassing isolation."""
    selected: dict[str, dict[str, Any]] = {}
    requested = component_ids or {}
    for name in REQUIRED_COMPONENTS:
        collection = COMPONENT_COLLECTIONS[name]
        record = tenant.get(collection, requested[name]) if requested.get(name) else None
        if record is None and not requested.get(name):
            records = tenant.list(collection)
            if records:
                record = sorted(records, key=lambda item: item.get("created_at") or item.get("_saved_at") or "", reverse=True)[0]
        if isinstance(record, dict):
            selected[name] = record
    return selected


def _component_scope(name: str, component: dict[str, Any]) -> tuple[str | None, str | None]:
    if name == "organization_context":
        organization = component.get("organization") if isinstance(component.get("organization"), dict) else component
        return organization.get("id") or organization.get("organization_id"), organization.get("season")
    return component.get("organization_id"), component.get("season")


def build_organization_operating_bundle(
    *, bundle_id: str, organization_id: str, season: str, components: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a composed readiness record without changing component state."""
    issues: list[dict[str, str]] = []
    if not bundle_id.startswith("ORG-BUNDLE-"):
        issues.append({"code": "BUNDLE-ID", "message": "bundle_id must start with ORG-BUNDLE-", "path": "bundle_id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "BUNDLE-ORG-ID", "message": "organization_id must start with ORG-", "path": "organization_id"})
    if not season:
        issues.append({"code": "BUNDLE-SEASON", "message": "season is required", "path": "season"})

    refs: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_COMPONENTS:
        component = components.get(name)
        if not isinstance(component, dict):
            issues.append({"code": "BUNDLE-MISSING", "message": f"required component is missing: {name}", "path": f"components.{name}"})
            continue
        component_org, component_season = _component_scope(name, component)
        if component_org != organization_id:
            issues.append({"code": "BUNDLE-SCOPE", "message": f"component organization scope mismatch: {name}", "path": f"components.{name}.organization_id"})
        if component_season and component_season != season:
            issues.append({"code": "BUNDLE-SEASON-SCOPE", "message": f"component season mismatch: {name}", "path": f"components.{name}.season"})
        status = component.get("status")
        required_status = "active" if name == "organization_context" else "approved" if name == "terminology_bundle" else "validated"
        if status != required_status:
            issues.append({"code": "BUNDLE-COMPONENT-STATE", "message": f"{name} must be {required_status}", "path": f"components.{name}.status"})
        refs[name] = {"id": component.get("id") or component.get("organization_id"), "status": status}

    return {
        "id": bundle_id,
        "organization_id": organization_id,
        "season": season,
        "component_refs": refs,
        "required_components": list(REQUIRED_COMPONENTS),
        "status": "ready_for_owner_review" if not issues else "blocked",
        "issues": issues,
        "owner_approval_required": True,
        "human_review_required": True,
        "activation_performed": False,
        "stage_advance_authorized": False,
        "production_implementation_allowed": False,
        "external_state_changed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def approve_organization_operating_bundle(
    *, bundle: dict[str, Any], approver: str, approver_role: str, decision_ref: str,
) -> dict[str, Any]:
    """Record owner approval for bounded non-production readiness only."""
    issues: list[dict[str, str]] = []
    if bundle.get("status") != "ready_for_owner_review":
        issues.append({"code": "BUNDLE-STATE", "message": "only a ready bundle can be approved", "path": "status"})
    if not approver or approver_role != "program_owner":
        issues.append({"code": "BUNDLE-APPROVER", "message": "a program_owner approver is required", "path": "approver_role"})
    if not decision_ref.startswith("DEC-"):
        issues.append({"code": "BUNDLE-DECISION", "message": "approval requires a DEC-* decision record", "path": "decision_ref"})
    if issues:
        return {"status": "rejected", "issues": issues, "production_implementation_allowed": False, "activation_performed": False}
    result = deepcopy(bundle)
    result.update({
        "status": "approved_for_non_production",
        "approved_by": approver,
        "approver_role": approver_role,
        "decision_ref": decision_ref,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "owner_approval_required": False,
        "human_review_required": False,
        "production_implementation_allowed": False,
        "activation_performed": False,
        "stage_advance_authorized": False,
        "external_state_changed": False,
        "issues": [],
    })
    return result
