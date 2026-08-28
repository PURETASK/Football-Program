"""Validation for the Stage 1 system architecture artifact."""

from __future__ import annotations

from typing import Any


def validate_system_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    """Validate structural homes, ownership, flows, and human authority boundaries."""
    errors: list[str] = []
    if architecture.get("scope") != "NFL football intelligence and development operating system":
        errors.append("architecture must be explicitly NFL-scoped")
    if architecture.get("stage") != "STAGE-1":
        errors.append("architecture must identify STAGE-1")
    components = architecture.get("components", [])
    component_ids = {item.get("id") for item in components}
    if not components or len(component_ids) != len(components):
        errors.append("components must be non-empty and uniquely identified")
    for component in components:
        for field in ("id", "name", "owner", "system_of_record", "responsibilities"):
            if not component.get(field):
                errors.append(f"component {component.get('id')}: missing {field}")
    flow_errors = []
    for flow in architecture.get("information_flows", []):
        if flow.get("from") not in component_ids or flow.get("to") not in component_ids:
            flow_errors.append(flow.get("id", "<unknown>"))
    if flow_errors:
        errors.append(f"flows reference unknown components: {', '.join(flow_errors)}")
    if not architecture.get("roles_and_permissions"):
        errors.append("role and permission architecture is required")
    if not architecture.get("state_model"):
        errors.append("state and memory model is required")
    states = {state.get("state") for state in architecture.get("state_model", [])}
    if not {"draft", "validated", "needs_review", "approved", "rejected"}.issubset(states):
        errors.append("state model lacks required review and approval states")
    if not architecture.get("events"):
        errors.append("event architecture is required")
    if not architecture.get("feedback_loops"):
        errors.append("system feedback loops are required")
    authority = set(architecture.get("human_authority_points", []))
    for required in ("locked terminology", "authoritative rules", "health-related escalation", "stage advancement"):
        if required not in authority:
            errors.append(f"human authority point missing: {required}")
    return {
        "architecture_id": architecture.get("architecture_id"),
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "component_count": len(components),
        "flow_count": len(architecture.get("information_flows", [])),
        "event_count": len(architecture.get("events", [])),
        "feedback_loop_count": len(architecture.get("feedback_loops", [])),
    }
