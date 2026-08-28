"""Progressive delivery wave and release-candidate readiness gates."""

from __future__ import annotations

from typing import Any


def evaluate_delivery_wave(
    *,
    wave_id: str,
    number: int,
    outcome: str,
    capability_ids: list[str],
    feature_gates: list[dict[str, Any]],
    eval_result: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if not wave_id.startswith("WAVE-"):
        blockers.append("Wave id must start with WAVE-")
    if number < 0 or not outcome or not capability_ids:
        blockers.append("Wave number, outcome, and capability ids are required")
    gate_map = {gate.get("capability_id"): gate for gate in feature_gates}
    for capability_id in capability_ids:
        gate = gate_map.get(capability_id)
        if not gate or gate.get("status") != "complete":
            blockers.append(f"Completion gate is not complete for {capability_id}")
    if eval_result.get("status") != "passed":
        blockers.append("Required evaluation suite has not passed")
    return {
        "id": wave_id, "number": number, "outcome": outcome, "capability_ids": capability_ids,
        "status": "ready" if not blockers else "blocked", "blockers": blockers,
        "human_approval_required": True,
    }


def build_release_candidate(
    *,
    release_id: str,
    wave: dict[str, Any],
    feature_gate_ids: list[str],
    eval_result: dict[str, Any],
    approver: str | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not release_id.startswith("RC-"):
        blockers.append("Release id must start with RC-")
    if wave.get("status") != "ready":
        blockers.append("Delivery wave is not ready")
    if not feature_gate_ids:
        blockers.append("Feature gate ids are required")
    if eval_result.get("status") != "passed":
        blockers.append("Evaluation suite must pass")
    if not approver:
        blockers.append("Human approval is required")
    return {
        "id": release_id, "wave_id": wave.get("id"), "eval_status": eval_result.get("status"),
        "feature_gate_ids": feature_gate_ids, "status": "approved" if not blockers else "blocked",
        "approval_required": True, "approved_by": approver if not blockers else None, "blockers": blockers,
    }
