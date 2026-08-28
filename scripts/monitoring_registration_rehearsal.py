"""Run a temporary provider-neutral monitoring registration rehearsal."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from nfl_fidos.monitoring_contract import load_monitoring_contract
from nfl_fidos.monitoring_registration import validate_monitoring_registration


def run_rehearsal() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-monitoring-") as directory:
        sink = Path(directory) / "events.jsonl"
        contract = load_monitoring_contract()
        validation = validate_monitoring_registration(contract=contract, environ={"NFL_FIDOS_MONITORING_BACKEND":"structured_jsonl","NFL_FIDOS_MONITORING_REGISTRATION_REF":"MONITORING-REG-REHEARSAL-001","NFL_FIDOS_OBSERVABILITY_PATH":str(sink)}, environment="validation")
        production = validate_monitoring_registration(contract=contract, environ={"NFL_FIDOS_MONITORING_BACKEND":"structured_jsonl","NFL_FIDOS_MONITORING_REGISTRATION_REF":"MONITORING-REG-REHEARSAL-001","NFL_FIDOS_OBSERVABILITY_PATH":str(sink)}, environment="production")
        missing_ref = validate_monitoring_registration(contract=contract, environ={"NFL_FIDOS_MONITORING_BACKEND":"structured_jsonl","NFL_FIDOS_OBSERVABILITY_PATH":str(sink)}, environment="production")
        serialized = json.dumps({"validation":validation,"production":production,"missing_ref":missing_ref})
        checks = {"contract_valid": validation.get("contract_id") == contract.get("contract_id") and validation.get("alert_count", 0) >= 4, "validation_ready": validation.get("status") == "ready", "production_metadata_ready": production.get("status") == "ready" and production.get("human_approval_required") is True, "missing_registration_fails_closed": missing_ref.get("status") == "blocked", "value_free": "credential" not in serialized.lower() and "password" not in serialized.lower()}
        return {"status":"passed" if all(checks.values()) else "failed","temporary_workspace":True,"checks":checks,"external_registration_performed":False,"external_state_changed":False,"production_implementation_allowed":False}


if __name__ == "__main__":
    result = run_rehearsal()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
