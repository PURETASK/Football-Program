"""Bounded, non-live pilot-organization selection controls."""

from __future__ import annotations

from typing import Any


REQUIRED_PILOT_ROLES = {"program_owner", "coach_staff", "analyst", "player"}


def build_pilot_selection(*, selection_id: str, organization: dict[str, Any], terminology_bundle: dict[str, Any], wave_id: str, pilot_users: list[dict[str, Any]], owner: str, decision_ref: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not selection_id.startswith("PILOT-SEL-"):
        issues.append({"code": "PILOT-SELECTION-ID", "message": "selection_id must start with PILOT-SEL-", "path": "selection_id"})
    if not wave_id.startswith("WAVE-"):
        issues.append({"code": "PILOT-WAVE-ID", "message": "wave_id must start with WAVE-", "path": "wave_id"})
    if organization.get("status") != "active":
        issues.append({"code": "PILOT-ORG-STATE", "message": "Pilot organization context must be active", "path": "organization.status"})
    if terminology_bundle.get("status") != "approved":
        issues.append({"code": "PILOT-TERMINOLOGY-STATE", "message": "Pilot terminology bundle must be approved", "path": "terminology_bundle.status"})
    if organization.get("id") != terminology_bundle.get("organization_id"):
        issues.append({"code": "PILOT-SCOPE", "message": "Organization and terminology bundle must share scope", "path": "scope"})
    roles = {user.get("role") for user in pilot_users if isinstance(user, dict) and user.get("id")}
    missing_roles = sorted(REQUIRED_PILOT_ROLES - roles)
    if missing_roles:
        issues.append({"code": "PILOT-ROLE-COVERAGE", "message": f"Pilot role coverage is incomplete: {missing_roles}", "path": "pilot_users"})
    if not owner:
        issues.append({"code": "PILOT-OWNER", "message": "Program owner is required", "path": "owner"})
    if not decision_ref.startswith("DEC-"):
        issues.append({"code": "PILOT-DECISION", "message": "Selection must reference a DEC-* decision record", "path": "decision_ref"})
    return {
        "id": selection_id,
        "organization_id": organization.get("id"),
        "wave_id": wave_id,
        "pilot_users": list(pilot_users),
        "pilot_roles": sorted(roles),
        "selected_by": owner,
        "decision_ref": decision_ref,
        "status": "selected" if not issues else "rejected",
        "live_pilot": False,
        "production_implementation_allowed": False,
        "external_state_changed": False,
        "human_review_required": True,
        "issues": issues,
    }
