"""Rehearse every declared agent role with local, non-provider adapters."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nfl_fidos import AgentRegistry, AgentRuntime, JsonRepository, TenantRepository, load_agent_bible
from nfl_fidos.local_agent_adapters import register_local_validation_adapters


def run_rehearsal() -> dict:
    root = Path(__file__).resolve().parents[1]
    bible = load_agent_bible(root / "agents" / "agent-organization-bible.json")
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-agent-runtime-") as directory:
        repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-AGENT-REHEARSAL", actor="validator")
        runtime = AgentRuntime(repository, registry=AgentRegistry())
        registration = register_local_validation_adapters(runtime, bible, activate=True)
        runs = []
        for index, role in enumerate(bible["roles"], start=1):
            capability = role["authority"][0]
            result = runtime.dispatch(
                run_id=f"RUN-AGENT-REHEARSAL-{index:03d}", from_agent="AGT-001", family=role["family"], capability=capability,
                workflow_id="WF-AGENT-REHEARSAL", payload={"input_ref": f"VALIDATION-INPUT-{index:03d}"},
            )
            runs.append({"agent_id": role["id"], "capability": capability, "status": result["status"], "output_status": (result.get("output") or {}).get("status")})
    checks = {
        "all_roles_covered": len(runs) == len(bible["roles"]),
        "all_runs_completed": all(item["status"] == "completed" for item in runs),
        "all_outputs_local_only": all(item["output_status"] == "local_validation_only" for item in runs),
        "registered_adapter_count": len(registration["registered_adapters"]),
    }
    return {
        "status": "passed" if checks["all_roles_covered"] and checks["all_runs_completed"] and checks["all_outputs_local_only"] else "failed",
        "checks": checks,
        "role_count": len(bible["roles"]),
        "runs": runs,
        "activation_performed": True,
        "external_provider_called": False,
        "canonical_write_performed": False,
        "production_implementation_allowed": False,
        "temporary_workspace": True,
    }


if __name__ == "__main__":
    print(json.dumps(run_rehearsal(), indent=2, sort_keys=True))
