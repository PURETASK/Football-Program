"""Build a value-free review packet for Stage 25 specification acceptance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .master_spec import validate_master_spec


def build_stage25_acceptance_packet(*, spec: dict[str, Any], audit_ref: str = "NFL_FIDOS_SOURCE_AUDIT.md") -> dict[str, Any]:
    validation = validate_master_spec(spec)
    return {
        "packet_id": "STAGE25-ACCEPTANCE-REVIEW-PACKET-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_id": spec.get("spec_id"),
        "spec_validation": validation,
        "review_status": "ready_for_owner_review" if validation.get("status") == "valid" else "blocked",
        "required_evidence_refs": [
            "control/master-codex-build-spec.json",
            audit_ref,
            "control/requirements-traceability.json",
            "NFL_FIDOS_IMPLEMENTATION_STATUS.md",
        ],
        "acceptance_payload_template": {
            "acceptance_id": "ACCEPTANCE-STAGE25-<OWNER-REFERENCE>",
            "rationale": "<Program owner records specification acceptance rationale>",
            "evidence_refs": ["control/master-codex-build-spec.json", audit_ref, "control/requirements-traceability.json"],
            "accepted_at": "<ISO-8601 timestamp>",
        },
        "safety": {
            "acceptance_recorded": False,
            "stage_advance_authorized": False,
            "production_implementation_allowed": False,
            "external_state_changed": False,
        },
    }
