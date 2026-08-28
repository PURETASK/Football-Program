"""Provider-neutral, read-only calendar and facility resource preflight."""

from __future__ import annotations

from typing import Any

from .practice_resources import plan_practice_resources


ALLOWED_PROVIDER_KINDS = {"calendar", "facility_system"}
MAX_AVAILABILITY_WINDOWS = 500


def plan_resource_integration(
    *,
    organization_id: str,
    integration_id: str,
    provider: dict[str, Any],
    practice_id: str,
    schedule: dict[str, Any],
    availability: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a non-mutating resource plan from provider-supplied availability.

    The provider payload is intentionally treated as already-authorized evidence.
    Fetching, reservation, and calendar writes belong to a separately approved
    adapter; this function never performs external I/O.
    """
    errors: list[str] = []
    if not organization_id.startswith("ORG-"):
        errors.append("organization_id must start with ORG-")
    if not integration_id.startswith("RESOURCE-INTEGRATION-"):
        errors.append("integration_id must start with RESOURCE-INTEGRATION-")
    if provider.get("kind") not in ALLOWED_PROVIDER_KINDS:
        errors.append("provider.kind must be calendar or facility_system")
    if provider.get("mode") != "read_only":
        errors.append("provider.mode must be read_only; reservation writes are not enabled")
    source_ref = str(provider.get("source_ref", ""))
    if not source_ref or not (source_ref.startswith("SOURCE-") or source_ref.startswith("PROVIDER-")):
        errors.append("provider.source_ref must reference an approved SOURCE-* or PROVIDER-* record")
    if len(availability) > MAX_AVAILABILITY_WINDOWS:
        errors.append(f"availability cannot exceed {MAX_AVAILABILITY_WINDOWS} windows")

    resource_plan = plan_practice_resources(
        organization_id=organization_id,
        practice_id=practice_id,
        schedule=schedule,
        availability=availability,
    )
    errors.extend(resource_plan["errors"])
    status = "ready" if not errors and resource_plan["status"] == "ready" else "blocked"
    return {
        "integration_id": integration_id,
        "organization_id": organization_id,
        "provider": {"kind": provider.get("kind"), "source_ref": source_ref, "mode": provider.get("mode")},
        "practice_id": practice_id,
        "status": status,
        "errors": errors,
        "resource_plan": resource_plan,
        "provider_action": "read_availability_only",
        "reservation_status": "not_requested",
        "external_calendar_mutation": False,
        "external_state_changed": False,
        "human_review_required": True,
    }
