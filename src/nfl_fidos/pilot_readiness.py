"""Stage 24 pilot-readiness and progressive-rollout gate evaluation."""

from __future__ import annotations

from typing import Any


REQUIRED_PILOT_ROLES = {"program_owner", "coach_staff", "analyst", "player"}


def evaluate_pilot_readiness(*, organization_id: str, pilot_users: list[dict[str, Any]], wave: dict[str, Any], completed_capabilities: set[str], eval_result: dict[str, Any], acceptance_evidence: list[str], feature_flags: dict[str, bool], rollback_tested: bool, owner_approval: str | None) -> dict[str, Any]:
    blockers: list[str] = []
    if not organization_id.startswith("ORG-"):
        blockers.append("pilot organization must be explicitly identified")
    roles = {user.get("role") for user in pilot_users if user.get("id")}
    missing_roles = sorted(REQUIRED_PILOT_ROLES - roles)
    if missing_roles:
        blockers.append(f"pilot role coverage is incomplete: {missing_roles}")
    missing_capabilities = sorted(set(wave.get("capabilities", [])) - completed_capabilities)
    if missing_capabilities:
        blockers.append(f"wave capabilities are incomplete: {missing_capabilities}")
    if eval_result.get("status") != "passed":
        blockers.append("evaluation checkpoint must pass")
    if not acceptance_evidence:
        blockers.append("acceptance evidence is required")
    missing_flags = [flag for flag in wave.get("feature_flags", []) if flag not in feature_flags]
    if missing_flags:
        blockers.append(f"feature flags are not explicitly controlled: {missing_flags}")
    enabled_flags = [flag for flag in wave.get("feature_flags", []) if feature_flags.get(flag) is not False]
    if enabled_flags:
        blockers.append(f"feature flags must remain off before pilot approval: {enabled_flags}")
    if not rollback_tested:
        blockers.append("rollback path must be tested")
    if not owner_approval:
        blockers.append("program owner pilot approval is required")
    return {"organization_id": organization_id, "wave_id": wave.get("id"), "status":"ready_for_pilot" if not blockers else "blocked", "blockers":blockers, "pilot_roles":sorted(roles), "acceptance_evidence":list(acceptance_evidence), "feature_flags":dict(feature_flags), "rollback_tested":rollback_tested, "owner_approval":owner_approval, "production_implementation_allowed":False, "human_review_required":True}
