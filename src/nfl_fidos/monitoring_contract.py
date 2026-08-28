"""Validation for the provider-neutral monitoring and incident contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"event_id", "request_id", "actor", "organization_id", "operation", "status", "duration_ms", "error_code", "source_refs"}
REQUIRED_ALERTS = {"ALERT-ERROR-RATE", "ALERT-READINESS-BLOCKER", "ALERT-AUTH-FAILURE", "ALERT-BACKUP-MISMATCH"}


def validate_monitoring_contract(contract: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if contract.get("scope") != "NFL only":
        issues.append("monitoring contract must be NFL-scoped")
    if contract.get("provider_neutral") is not True:
        issues.append("monitoring contract must remain provider-neutral")
    if not REQUIRED_FIELDS.issubset(set(contract.get("event_fields", []))):
        issues.append("event_fields do not cover the observability contract")
    alert_ids = {alert.get("id") for alert in contract.get("alerts", [])}
    missing_alerts = REQUIRED_ALERTS - alert_ids
    if missing_alerts:
        issues.append(f"missing required alerts: {sorted(missing_alerts)}")
    if not contract.get("sinks"):
        issues.append("at least one structured sink is required")
    for sink in contract.get("sinks", []):
        if sink.get("kind") != "structured_jsonl" or not sink.get("path_env") or sink.get("registration") != "deployment_owner_required":
            issues.append(f"sink is not a bounded registered structured sink: {sink.get('id')}")
    retention = contract.get("retention", {})
    if retention.get("deletion_requires_approval") is not True or retention.get("event_days", 0) <= 0 or retention.get("incident_days", 0) <= 0:
        issues.append("retention must be positive and deletion must require approval")
    return {"contract_id": contract.get("contract_id"), "status":"valid" if not issues else "invalid", "issues":issues, "alert_count":len(alert_ids), "provider_neutral":contract.get("provider_neutral")}


def load_monitoring_contract(path: str | Path | None = None) -> dict[str, Any]:
    root = Path(path) if path else Path(__file__).resolve().parents[2] / "monitoring" / "observability-contract.json"
    contract = json.loads(root.read_text(encoding="utf-8"))
    result = validate_monitoring_contract(contract)
    if result["status"] != "valid":
        raise ValueError("monitoring contract invalid: " + "; ".join(result["issues"]))
    return contract
