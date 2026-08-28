"""Stage 23 engineering architecture and operational contract validation."""

from __future__ import annotations

from typing import Any


def validate_engineering_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for section in ("repo_map", "runtime_boundaries", "api_contracts", "agent_runtime", "data_access", "testing_strategy", "environments", "ci_cd", "migrations", "feature_flags", "operational_runbooks", "security_controls"):
        if not architecture.get(section):
            issues.append(f"missing engineering architecture section: {section}")
    runtime_ids = {runtime.get("id") for runtime in architecture.get("runtime_boundaries", [])}
    if len(runtime_ids) != len(architecture.get("runtime_boundaries", [])):
        issues.append("runtime boundaries must be uniquely identified")
    required_signals = {"structured_logs", "audit_events", "eval_results", "validation_failures", "permission_denials"}
    if not required_signals.issubset(set(architecture.get("observability", {}).get("signals", []))):
        issues.append("observability signal set is incomplete")
    required_fields = {"event_id", "request_id", "actor", "organization_id", "operation", "status", "error_code"}
    if not required_fields.issubset(set(architecture.get("observability", {}).get("required_fields", []))):
        issues.append("observability fields are incomplete")
    if not any("run unit and contract tests" in command for command in architecture.get("ci_cd", [])):
        issues.append("CI must run unit and contract tests")
    if not any("require governance audit" in command for command in architecture.get("ci_cd", [])):
        issues.append("CI must require governance audit")
    return {"architecture_id":architecture.get("architecture_id"), "status":"valid" if not issues else "invalid", "errors":issues, "repo_area_count":len(architecture.get("repo_map", [])), "runtime_boundary_count":len(architecture.get("runtime_boundaries", []))}
