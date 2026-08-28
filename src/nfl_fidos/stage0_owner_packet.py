"""Build a value-free Stage 0 owner-approval review packet."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .stage0 import evaluate_stage0_exit


def build_stage0_owner_packet(*, registry: dict[str, Any], gap_audit: dict[str, Any], source_audit_ref: str = "NFL_FIDOS_SOURCE_AUDIT.md") -> dict[str, Any]:
    """Prepare owner-review evidence without recording a decision or changing control state."""
    gap_complete = gap_audit.get("status") == "complete"
    gate = evaluate_stage0_exit(registry, gap_audit_complete=gap_complete, owner_approved=False)
    return {
        "packet_id": "STAGE0-OWNER-REVIEW-PACKET-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": gate,
        "review_status": "ready_for_owner_review" if gate["status"] == "ready_for_approval" else "blocked",
        "required_evidence_refs": [
            "control/stage-0a-registry.json",
            "control/stage-0-gap-audit.json",
            "control/stage-0-exit-gate.json",
            source_audit_ref,
            "NFL_FIDOS_IMPLEMENTATION_STATUS.md",
        ],
        "approval_payload_template": {
            "approval_id": "APPROVAL-STAGE0-<OWNER-REFERENCE>",
            "rationale": "<Program owner records review rationale>",
            "evidence_refs": ["control/stage-0a-registry.json", "control/stage-0-gap-audit.json", "control/stage-0-exit-gate.json"],
            "approved_at": "<ISO-8601 timestamp>",
        },
        "safety": {
            "approval_recorded": False,
            "stage_advance_authorized": False,
            "production_implementation_allowed": False,
            "external_state_changed": False,
        },
    }
