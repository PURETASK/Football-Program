"""Validator for the Stage 0–25 requirements traceability ledger."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_traceability_ledger(ledger: dict[str, Any], *, root: str | Path | None = None) -> dict[str, Any]:
    issues: list[str] = []
    stages = ledger.get("stages", [])
    expected = {f"STAGE-{index}" for index in range(26)}
    actual = {stage.get("stage") for stage in stages}
    if actual != expected:
        issues.append("ledger must cover exactly STAGE-0 through STAGE-25")
    for stage in stages:
        for field in ("stage", "required_deliverables", "evidence", "status", "remaining"):
            if not stage.get(field):
                issues.append(f"{stage.get('stage')}: missing {field}")
    missing_evidence: list[dict[str, str]] = []
    if root is not None:
        base = Path(root)
        for stage in stages:
            for reference in stage.get("evidence", []):
                if isinstance(reference, str) and reference.startswith("EVAL-"):
                    continue
                if not isinstance(reference, str) or not (base / reference).exists():
                    missing_evidence.append({"stage":str(stage.get("stage")), "reference":str(reference)})
        if missing_evidence:
            issues.append(f"{len(missing_evidence)} evidence reference(s) are missing from the repository")
    if not ledger.get("global_remaining_work"):
        issues.append("global remaining work must be explicit")
    return {"ledger_id":ledger.get("ledger_id"), "status":"valid" if not issues else "invalid", "stage_count":len(stages), "evidence_reference_count":sum(len(stage.get("evidence", [])) for stage in stages), "missing_evidence":missing_evidence, "errors":issues}
