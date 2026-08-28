"""Compose non-activating deployment and environment readiness evidence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .deployment_preflight import run_deployment_preflight
from .monitoring_contract import load_monitoring_contract
from .monitoring_registration import validate_monitoring_registration
from .operational_readiness import run_operational_readiness
from .scheduler_registration import load_scheduler_registration, validate_scheduler_registration


def run_deployment_environment_readiness(
    *,
    contract_path: str | Path,
    control_root: str | Path,
    environ: dict[str, str] | None = None,
    database_path: str | Path | None = None,
    run_evals: bool = True,
    eval_result: dict[str, Any] | None = None,
    environment: str | None = None,
) -> dict[str, Any]:
    """Return a composed readiness report; never deploys, registers, or activates anything."""
    values = dict(os.environ if environ is None else environ)
    requested_environment = environment or values.get("NFL_FIDOS_ENV", "local")
    deployment = run_deployment_preflight(
        contract_path=contract_path,
        control_root=control_root,
        environ=values,
        environment=requested_environment,
    )
    operational = run_operational_readiness(
        environ=values,
        database_path=database_path,
        run_evals=run_evals,
        eval_result=eval_result,
    )
    scheduler = validate_scheduler_registration(
        registration=load_scheduler_registration(),
        environ=values,
        environment=requested_environment,
    )
    monitoring = validate_monitoring_registration(
        contract=load_monitoring_contract(),
        environ=values,
        environment=requested_environment,
    )
    blockers: list[str] = []
    for name, result in (("deployment_preflight", deployment), ("operational_readiness", operational), ("scheduler_registration", scheduler), ("monitoring_registration", monitoring)):
        if result.get("status") != "ready":
            blockers.append(name)
    return {
        "status": "ready" if not blockers else "blocked",
        "environment": requested_environment,
        "deployment_preflight": deployment,
        "operational_readiness": operational,
        "scheduler_registration": scheduler,
        "monitoring_registration": monitoring,
        "blockers": blockers,
        "activation_performed": False,
        "external_state_changed": False,
        "human_approval_required": requested_environment == "production",
    }
