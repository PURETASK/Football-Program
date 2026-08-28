"""Validator for compositional NFL offensive and defensive scheme architecture."""

from __future__ import annotations

from typing import Any


REQUIRED_TAXONOMY_KEYS = {
    "offense": {"personnel", "formations", "motions", "run_families", "pass_families", "protections", "situations"},
    "defense": {"personnel", "fronts", "techniques", "coverages", "pressures", "checks", "situations"},
}


def validate_scheme_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for unit in ("offense", "defense"):
        section = architecture.get(unit, {})
        taxonomy = section.get("taxonomies", {})
        missing = sorted(REQUIRED_TAXONOMY_KEYS[unit] - set(taxonomy))
        if missing:
            issues.append(f"{unit}: missing taxonomy {missing}")
        for field in ("philosophies", "concept_graph", "fit_criteria", "counter_library", "installation_requirements"):
            if not section.get(field):
                issues.append(f"{unit}: missing {field}")
        for index, counter in enumerate(section.get("counter_library", [])):
            for field in ("threat", "primary", "opponent_counter", "counter_counter", "trigger", "evidence_required"):
                if not counter.get(field):
                    issues.append(f"{unit}: counter {index} missing {field}")
    if not architecture.get("shared_controls"):
        issues.append("shared compositional controls are required")
    return {"architecture_id":architecture.get("architecture_id"), "status":"valid" if not issues else "invalid", "errors":issues}
