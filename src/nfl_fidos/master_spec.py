"""Stage 25 Master Codex Build Specification validation."""

from __future__ import annotations

from typing import Any


REQUIRED_STAGES = {f"STAGE-{number}" for number in range(26)}


def validate_master_spec(spec: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not spec.get("spec_id", "").startswith("MASTER-CODEX-BUILD-SPEC-"):
        issues.append("spec id must identify the Master Codex Build Specification")
    stages = spec.get("stage_sequence", [])
    stage_ids = {stage.get("stage") for stage in stages}
    missing = sorted(REQUIRED_STAGES - stage_ids)
    if missing:
        issues.append(f"missing stage sequence entries: {missing}")
    if len(stage_ids) != len(stages):
        issues.append("stage sequence entries must be unique")
    for stage in stages:
        for field in ("stage", "work", "exit_evidence"):
            if not stage.get(field):
                issues.append(f"{stage.get('stage')}: missing {field}")
    for section in ("locked_principles", "upstream_artifacts", "domain_contracts", "workflow_contracts", "permission_rules", "quality_commands", "coding_standards", "change_control", "acceptance_criteria", "allowed_changes", "prohibited_changes", "traceability_requirements"):
        if not spec.get(section):
            issues.append(f"missing master-spec section: {section}")
    if not any("unittest" in command for command in spec.get("quality_commands", [])) or not any("run_evals" in command for command in spec.get("quality_commands", [])):
        issues.append("reproducible test and eval commands are required")
    if not any("human approval" in rule.lower() for rule in spec.get("permission_rules", []) + spec.get("change_control", [])):
        issues.append("human approval rule is required")
    return {"spec_id":spec.get("spec_id"), "status":"valid" if not issues else "invalid", "errors":issues, "stage_count":len(stages), "upstream_artifact_count":len(spec.get("upstream_artifacts", []))}
