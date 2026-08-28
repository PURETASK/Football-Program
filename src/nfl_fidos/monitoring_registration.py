"""Non-activating monitoring backend registration and health evidence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .monitoring_contract import validate_monitoring_contract


def validate_monitoring_registration(*, contract: dict[str, Any], environ: dict[str, str] | None = None, environment: str = "local") -> dict[str, Any]:
    values = os.environ if environ is None else environ
    issues: list[str] = []
    contract_result = validate_monitoring_contract(contract)
    if contract_result["status"] != "valid":
        issues.extend(contract_result["issues"])
    backend = values.get("NFL_FIDOS_MONITORING_BACKEND", "structured_jsonl").strip()
    registration_ref = values.get("NFL_FIDOS_MONITORING_REGISTRATION_REF", "").strip()
    path_value = values.get("NFL_FIDOS_OBSERVABILITY_PATH", "").strip()
    if backend != "structured_jsonl":
        issues.append("only the provider-neutral structured_jsonl backend is currently supported")
    if environment == "production" and not registration_ref.startswith("MONITORING-REG-"):
        issues.append("production monitoring requires a MONITORING-REG-* deployment registration reference")
    if registration_ref and not registration_ref.startswith("MONITORING-REG-"):
        issues.append("monitoring registration reference must start with MONITORING-REG-")
    if not path_value:
        issues.append("NFL_FIDOS_OBSERVABILITY_PATH is required")
    path = Path(path_value).expanduser().resolve() if path_value else None
    parent = path.parent if path else None
    parent_writable = bool(parent and parent.exists() and os.access(parent, os.W_OK))
    if path and not parent_writable:
        issues.append("observability sink parent must exist and be writable")
    alert_ids = {item.get("id") for item in contract.get("alerts", [])}
    return {"status":"ready" if not issues else "blocked", "environment":environment, "backend":backend, "registration_ref":registration_ref or None, "sink_path":str(path) if path else None, "sink_parent_writable":parent_writable, "alert_count":len(alert_ids), "contract_id":contract.get("contract_id"), "issues":issues, "external_registration_performed":False, "external_state_changed":False, "human_approval_required":environment == "production"}
