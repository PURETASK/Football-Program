"""Compose pilot selection, readiness, and rollback into one non-live package."""

from __future__ import annotations

from typing import Any


def build_pilot_delivery_package(*, package_id: str, selection: dict[str, Any], readiness: dict[str, Any], rollback: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if not package_id.startswith("PILOT-PKG-"):
        blockers.append("package_id must start with PILOT-PKG-")
    if selection.get("status") != "selected":
        blockers.append("pilot organization selection must be selected")
    if readiness.get("status") != "ready_for_pilot":
        blockers.append("pilot readiness must be ready_for_pilot")
    if selection.get("organization_id") != readiness.get("organization_id"):
        blockers.append("selection and readiness organization scope must match")
    if selection.get("wave_id") != readiness.get("wave_id"):
        blockers.append("selection and readiness wave must match")
    if rollback.get("status") != "passed":
        blockers.append("rollback rehearsal must pass")
    if rollback.get("external_state_changed") is not False:
        blockers.append("rollback rehearsal must report no external state change")
    if any(value is not False for value in readiness.get("feature_flags", {}).values()):
        blockers.append("all feature flags must remain off")
    return {
        "id": package_id,
        "organization_id": selection.get("organization_id"),
        "wave_id": selection.get("wave_id"),
        "selection_id": selection.get("id"),
        "readiness_id": readiness.get("id"),
        "rollback": dict(rollback),
        "status": "ready_for_bounded_pilot" if not blockers else "blocked",
        "blockers": blockers,
        "live_pilot": False,
        "production_implementation_allowed": False,
        "external_state_changed": False,
        "human_review_required": True,
    }
