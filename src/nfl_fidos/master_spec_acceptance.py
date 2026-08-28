"""Non-activating Stage 25 acceptance evidence for the compiled Master Spec."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .master_spec import validate_master_spec


def load_master_spec(path: str | Path | None = None) -> dict[str, Any]:
    spec_path = Path(path) if path else Path(__file__).resolve().parents[2] / "control" / "master-codex-build-spec.json"
    return json.loads(spec_path.read_text(encoding="utf-8"))


def build_stage25_spec_acceptance(*, acceptance_id: str, spec: dict[str, Any], approver: str, rationale: str, evidence_refs: list[str], accepted_at: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    validation = validate_master_spec(spec)
    if not acceptance_id.startswith("ACCEPTANCE-STAGE25-"):
        issues.append({"code": "STAGE25-ACCEPTANCE-ID", "message": "Acceptance id must start with ACCEPTANCE-STAGE25-", "path": "id"})
    if validation["status"] != "valid":
        issues.append({"code": "STAGE25-SPEC-INVALID", "message": "Compiled Master Spec must validate before acceptance", "path": "spec"})
    if not approver or not rationale or not evidence_refs:
        issues.append({"code": "STAGE25-ACCEPTANCE-METADATA", "message": "Approver, rationale, and evidence references are required", "path": "metadata"})
    try:
        datetime.fromisoformat(accepted_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        issues.append({"code": "STAGE25-ACCEPTANCE-TIME", "message": "accepted_at must be an ISO-8601 timestamp", "path": "accepted_at"})
    return {
        "id": acceptance_id,
        "stage": "STAGE-25",
        "spec_id": spec.get("spec_id"),
        "decision": "accepted" if not issues else "rejected",
        "approver": approver,
        "approver_role": "program_owner",
        "accepted_at": accepted_at,
        "rationale": rationale,
        "evidence_refs": list(evidence_refs),
        "spec_validation": validation,
        "production_implementation_allowed": False,
        "stage_advance_authorized": False,
        "issues": issues,
    }


def validate_stage25_spec_acceptance(record: dict[str, Any], *, spec: dict[str, Any]) -> dict[str, Any]:
    issues = list(record.get("issues", []))
    required = ("id", "stage", "spec_id", "decision", "approver", "approver_role", "accepted_at", "rationale", "evidence_refs")
    issues.extend({"code": "STAGE25-ACCEPTANCE-FIELD", "message": f"Missing required field: {field}", "path": field} for field in required if field not in record)
    if record.get("decision") != "accepted":
        issues.append({"code": "STAGE25-ACCEPTANCE-DECISION", "message": "Specification acceptance decision is not accepted", "path": "decision"})
    if record.get("approver_role") != "program_owner":
        issues.append({"code": "STAGE25-ACCEPTANCE-ROLE", "message": "Only program_owner may accept the compiled specification", "path": "approver_role"})
    if record.get("spec_id") != spec.get("spec_id"):
        issues.append({"code": "STAGE25-ACCEPTANCE-LINK", "message": "Acceptance must link to the current compiled specification", "path": "spec_id"})
    if record.get("production_implementation_allowed") is not False or record.get("stage_advance_authorized") is not False:
        issues.append({"code": "STAGE25-ACCEPTANCE-SAFETY", "message": "Specification acceptance cannot enable production or automatically advance stages", "path": "safety"})
    return {"status": "valid" if not issues else "invalid", "stage": "STAGE-25", "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": issues, "record": record}
