"""Report organization package population without fabricating validation state."""

from __future__ import annotations

from typing import Any

from .organization_operating_bundle import COMPONENT_COLLECTIONS, REQUIRED_COMPONENTS, _component_scope


def build_organization_population_readiness(*, tenant: Any, organization_id: str, season: str) -> dict[str, Any]:
    """Return a tenant-scoped checklist for the packages required by the operating bundle."""
    if not organization_id.startswith("ORG-"):
        raise ValueError("organization_id must start with ORG-")
    if not season:
        raise ValueError("season is required")
    if tenant.organization_id != organization_id:
        raise PermissionError("tenant organization does not match requested organization")

    components: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []
    for name in REQUIRED_COMPONENTS:
        collection = COMPONENT_COLLECTIONS[name]
        records = tenant.list(collection)
        records = sorted(records, key=lambda item: item.get("created_at") or item.get("_saved_at") or "", reverse=True)
        record = records[0] if records else None
        required_status = "active" if name == "organization_context" else "approved" if name == "terminology_bundle" else "validated"
        component_org = component_season = None
        if isinstance(record, dict):
            component_org, component_season = _component_scope(name, record)
        scope_valid = component_org == organization_id if record else False
        season_valid = component_season in (None, season) if record else False
        state_valid = isinstance(record, dict) and record.get("status") == required_status
        ready = bool(record and scope_valid and season_valid and state_valid)
        item = {
            "component": name,
            "collection": collection,
            "required_status": required_status,
            "found": bool(record),
            "record_id": record.get("id") if record else None,
            "actual_status": record.get("status") if record else None,
            "scope_valid": scope_valid,
            "season_valid": season_valid,
            "ready": ready,
        }
        components.append(item)
        if not record:
            blockers.append({"code": "POPULATION-MISSING", "component": name, "message": f"No persisted {name} package is available"})
        elif not scope_valid:
            blockers.append({"code": "POPULATION-SCOPE", "component": name, "message": f"Latest {name} package is outside the requested organization scope"})
        elif not season_valid:
            blockers.append({"code": "POPULATION-SEASON", "component": name, "message": f"Latest {name} package does not match season {season}"})
        elif not state_valid:
            blockers.append({"code": "POPULATION-STATE", "component": name, "message": f"{name} must be {required_status} before bundle composition"})

    ready_count = sum(1 for item in components if item["ready"])
    return {
        "organization_id": organization_id,
        "season": season,
        "status": "ready_for_bundle" if not blockers else "population_incomplete",
        "components": components,
        "ready_component_count": ready_count,
        "required_component_count": len(REQUIRED_COMPONENTS),
        "blockers": blockers,
        "owner_review_required": True,
        "activation_performed": False,
        "production_implementation_allowed": False,
        "external_state_changed": False,
    }
