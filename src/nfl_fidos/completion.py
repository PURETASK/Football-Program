"""Executable feature Definition-of-Done gate."""

from __future__ import annotations

from typing import Any


REQUIRED_CHECKS = (
    "requirement_id", "owner", "inputs_outputs", "ontology_review", "nfl_rule_review",
    "context_rules", "nuance_cases", "data_model", "permissions", "agent_contracts",
    "deterministic_validation", "tests_evals", "observability", "documentation", "acceptance_evidence",
)


def build_completion_gate(*, gate_id: str, capability_id: str, owner: str, checks: dict[str, bool], blockers: list[str] | None = None) -> dict[str, Any]:
    blockers = blockers or []
    issues: list[dict[str, str]] = []
    if not gate_id.startswith("DONE-"):
        issues.append({"code": "DONE-ID", "message": "Completion gate id must start with DONE-", "path": "gate_id"})
    if not capability_id.startswith("CAP-"):
        issues.append({"code": "DONE-CAPABILITY", "message": "Completion gate requires CAP-* id", "path": "capability_id"})
    if not owner:
        issues.append({"code": "DONE-OWNER", "message": "Completion gate owner is required", "path": "owner"})
    missing = [check for check in REQUIRED_CHECKS if checks.get(check) is not True]
    if missing:
        blockers = [*blockers, *[f"Missing completion evidence: {check}" for check in missing]]
    status = "complete" if not issues and not blockers else "blocked" if blockers else "in_progress"
    return {
        "id": gate_id, "capability_id": capability_id, "owner": owner,
        "checks": [{"name": name, "complete": checks.get(name) is True} for name in REQUIRED_CHECKS],
        "status": status, "blockers": blockers, "issues": issues,
    }


def close_completion_gate(gate: dict[str, Any], *, acceptance_evidence: list[str], approver: str) -> dict[str, Any]:
    result = dict(gate)
    blockers = list(result.get("blockers", []))
    if result.get("status") != "complete":
        blockers.append("All Definition-of-Done checks must pass before closure.")
    if not acceptance_evidence:
        blockers.append("Acceptance evidence is required.")
    if not approver:
        blockers.append("Approver is required.")
    result["status"] = "complete" if not blockers else "blocked"
    result["acceptance_evidence"] = acceptance_evidence
    result["approved_by"] = approver if not blockers else None
    result["blockers"] = blockers
    return result
