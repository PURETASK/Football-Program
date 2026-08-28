"""Run a bounded local observability failure/recovery rehearsal."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nfl_fidos.deployment_contract import validate_deployment_contract
from nfl_fidos.monitoring_contract import load_monitoring_contract
from nfl_fidos.observability import ObservabilityRecorder
from nfl_fidos.observability_sink import export_events


def run_rehearsal() -> dict:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-incident-") as directory:
        recorder = ObservabilityRecorder(Path(directory) / "events.jsonl")
        recorder.record(operation="rehearsal.failure", status="error", actor="REHEARSAL", organization_id="ORG-REHEARSAL", duration_ms=4.2, error_code="SIMULATED_FAILURE", source_refs=["INCIDENT-REHEARSAL"])
        recorder.record(operation="rehearsal.recovery", status="ok", actor="REHEARSAL", organization_id="ORG-REHEARSAL", duration_ms=3.1, source_refs=["INCIDENT-REHEARSAL"])
        events = recorder.read()
        exported = []
        export_report = export_events(events, sink=exported.append, max_events=10)
        deployment = validate_deployment_contract(path=root / "deployment" / "nfl-fidos-deployment.json")
        monitoring = load_monitoring_contract()
        return {"status":"passed" if len(events) == 2 and export_report["status"] == "completed" and deployment["status"] == "valid" and monitoring["status"] == "design_only" else "failed", "simulated_failure_recorded": events[0]["error_code"] == "SIMULATED_FAILURE", "recovery_recorded": events[1]["status"] == "ok", "export":export_report, "rollback_contract_valid":deployment["status"] == "valid", "production_disabled":deployment["production_implementation_allowed"] is False, "events_are_temporary":True}


if __name__ == "__main__":
    result = run_rehearsal()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
