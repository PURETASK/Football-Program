"""Stage 24 MVP wave, priority, acceptance, and rollout validation."""

from __future__ import annotations

from typing import Any


def validate_mvp_strategy(strategy: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    waves = strategy.get("waves", [])
    wave_ids = {wave.get("id") for wave in waves}
    if not waves or len(wave_ids) != len(waves):
        issues.append("waves must be non-empty and uniquely identified")
    previous_number = 0
    for wave in waves:
        if wave.get("number") != previous_number + 1:
            issues.append("wave numbers must be sequential")
        previous_number = wave.get("number", previous_number)
        for field in ("id", "name", "classification", "capabilities", "dependencies", "pilot_outcome", "acceptance_criteria", "eval_checkpoint", "feature_flags", "rollback"):
            if not wave.get(field):
                issues.append(f"{wave.get('id')}: missing {field}")
        if any(dependency.startswith("WAVE-") and dependency not in wave_ids for dependency in wave.get("dependencies", [])):
            issues.append(f"{wave.get('id')}: unknown wave dependency")
    if not strategy.get("mvp_outcome") or not strategy.get("pilot_users") or not strategy.get("priority_matrix") or not strategy.get("risk_register") or not strategy.get("rollout_controls"):
        issues.append("MVP outcome, pilot users, priority matrix, risk register, and rollout controls are required")
    return {"strategy_id":strategy.get("strategy_id"), "status":"valid" if not issues else "invalid", "errors":issues, "wave_count":len(waves), "pilot_count":len(strategy.get("pilot_users", []))}


def evaluate_mvp_wave(*, wave: dict[str, Any], completed_capabilities: set[str], eval_result: dict[str, Any], acceptance_evidence: list[str], feature_flags: dict[str, bool], approval: str | None) -> dict[str, Any]:
    blockers: list[str] = []
    missing = sorted(set(wave.get("capabilities", [])) - completed_capabilities)
    if missing:
        blockers.append(f"missing completed capabilities: {missing}")
    if eval_result.get("status") != "passed":
        blockers.append("evaluation checkpoint did not pass")
    if not acceptance_evidence:
        blockers.append("acceptance evidence is required")
    if any(feature_flags.get(flag) is not False for flag in wave.get("feature_flags", [])):
        blockers.append("feature flags must be explicitly controlled before promotion")
    if not approval:
        blockers.append("human wave approval is required")
    return {"wave_id":wave.get("id"), "status":"ready" if not blockers else "blocked", "blockers":blockers, "rollback":wave.get("rollback"), "approval":approval}
