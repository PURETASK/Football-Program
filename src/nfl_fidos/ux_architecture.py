"""Stage 22 UX information architecture, journeys, states, and permission validation."""

from __future__ import annotations

from typing import Any


ROLES = {"player", "coach_staff", "analyst", "program_owner", "validator", "performance_staff"}
REQUIRED_STATES = {"loading", "ready", "error", "restricted", "blocked"}


def validate_ux_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    screens = architecture.get("screen_inventory", [])
    screen_ids = {screen.get("id") for screen in screens}
    if not screens or len(screen_ids) != len(screens):
        issues.append("screen inventory must be non-empty and uniquely identified")
    for screen in screens:
        for field in ("id", "name", "primary_roles", "entry_point", "workflow", "states", "outputs", "responsive"):
            if not screen.get(field):
                issues.append(f"{screen.get('id')}: missing {field}")
        if not REQUIRED_STATES.issubset(set(screen.get("states", []))):
            issues.append(f"{screen.get('id')}: missing required interaction states")
        if any(role not in ROLES for role in screen.get("primary_roles", [])):
            issues.append(f"{screen.get('id')}: unknown role")
    journey_roles = {journey.get("role") for journey in architecture.get("role_journeys", [])}
    if not {"player", "coach_staff", "analyst", "program_owner"}.issubset(journey_roles):
        issues.append("core role journeys are required")
    for permission in architecture.get("permissions_to_ui", []):
        if permission.get("role") not in ROLES or not permission.get("action") or not permission.get("ui_surfaces"):
            issues.append("permission-to-UI mapping is incomplete")
        if any(surface not in screen_ids for surface in permission.get("ui_surfaces", [])):
            issues.append(f"permission mapping references unknown screen: {permission.get('action')}")
    if not architecture.get("accessibility") or not architecture.get("notification_rules"):
        issues.append("accessibility and notification rules are required")
    return {"architecture_id":architecture.get("architecture_id"), "status":"valid" if not issues else "invalid", "errors":issues, "screen_count":len(screens), "journey_count":len(architecture.get("role_journeys", []))}
