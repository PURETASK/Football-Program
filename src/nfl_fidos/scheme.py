"""Compositional offensive, defensive, and special-teams scheme validation."""

from __future__ import annotations

from typing import Any


UNITS = {"offense", "defense", "special_teams"}
REQUIRED_COMPONENT_KINDS = {
    "offense": {"personnel", "formation", "concept"},
    "defense": {"front", "coverage", "pressure_or_check"},
    "special_teams": {"unit", "phase", "operation"},
}


def validate_scheme(scheme: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "version", "unit", "name", "components", "assignments", "source"):
        if field not in scheme or scheme[field] in (None, "", []):
            issues.append({"code": "SCHEME-REQUIRED", "message": f"Missing required field: {field}", "path": field})
    if "constraints" not in scheme or scheme["constraints"] is None:
        issues.append({"code": "SCHEME-REQUIRED", "message": "Missing required field: constraints", "path": "constraints"})
    if scheme.get("id") and not scheme["id"].startswith("SCHEME-"):
        issues.append({"code": "SCHEME-ID", "message": "Scheme id must start with SCHEME-", "path": "id"})
    unit = scheme.get("unit")
    if unit not in UNITS:
        issues.append({"code": "SCHEME-UNIT", "message": "Unit must be offense, defense, or special_teams", "path": "unit"})
    components = scheme.get("components")
    component_kinds: set[str] = set()
    component_ids: set[str] = set()
    if not isinstance(components, list):
        issues.append({"code": "SCHEME-COMPONENTS", "message": "Components must be a list", "path": "components"})
    else:
        for index, component in enumerate(components):
            path = f"components[{index}]"
            if not isinstance(component, dict) or not component.get("id") or not component.get("kind") or not component.get("label"):
                issues.append({"code": "SCHEME-COMPONENT-SHAPE", "message": "Each component requires id, kind, and label", "path": path})
                continue
            if component["id"] in component_ids:
                issues.append({"code": "SCHEME-DUPLICATE-COMPONENT", "message": f"Duplicate component: {component['id']}", "path": path})
            component_ids.add(component["id"])
            component_kinds.add(component["kind"])
        if unit in REQUIRED_COMPONENT_KINDS:
            missing = sorted(REQUIRED_COMPONENT_KINDS[unit] - component_kinds)
            if missing:
                issues.append({"code": "SCHEME-INCOMPLETE", "message": f"Missing required component kinds: {', '.join(missing)}", "path": "components"})

    assignments = scheme.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        issues.append({"code": "SCHEME-ASSIGNMENTS", "message": "At least one assignment is required", "path": "assignments"})
    else:
        assigned_roles: set[str] = set()
        for index, assignment in enumerate(assignments):
            path = f"assignments[{index}]"
            if not isinstance(assignment, dict) or not assignment.get("role") or not assignment.get("responsibility"):
                issues.append({"code": "SCHEME-ASSIGNMENT-SHAPE", "message": "Each assignment requires role and responsibility", "path": path})
                continue
            if assignment["role"] in assigned_roles:
                issues.append({"code": "SCHEME-DUPLICATE-ROLE", "message": f"Duplicate role: {assignment['role']}", "path": path})
            assigned_roles.add(assignment["role"])

    source = scheme.get("source")
    if not isinstance(source, dict) or not source.get("kind") or not source.get("ref"):
        issues.append({"code": "SCHEME-PROVENANCE", "message": "Source kind and ref are required", "path": "source"})
    return issues


def build_scheme(scheme: dict[str, Any]) -> dict[str, Any]:
    issues = validate_scheme(scheme)
    output = dict(scheme)
    output["status"] = "invalid" if issues else "validated"
    output["issues"] = issues
    return output


def build_countermeasure(*, scheme_id: str, threat: str, response: str, trigger: str, evidence_refs: list[str]) -> dict[str, Any]:
    if not scheme_id.startswith("SCHEME-") or not threat or not response or not trigger or not evidence_refs:
        raise ValueError({"code": "COUNTERMEASURE-INCOMPLETE", "message": "Scheme, threat, response, trigger, and evidence are required"})
    return {
        "id": f"COUNTER-{scheme_id.removeprefix('SCHEME-')}",
        "scheme_id": scheme_id,
        "threat": threat,
        "response": response,
        "trigger": trigger,
        "evidence_refs": evidence_refs,
        "requires_human_review": True,
        "status": "draft",
    }
