"""Non-activating deployment preflight combining contract, secret, and gate evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .deployment_contract import validate_deployment_contract
from .secret_source import inspect_secret_source


def run_deployment_preflight(*, contract_path: str | Path, control_root: str | Path, environ: dict[str, str], environment: str | None = None) -> dict[str, Any]:
    root = Path(control_root).resolve()
    contract = validate_deployment_contract(path=contract_path)
    requested_environment = environment or environ.get("NFL_FIDOS_ENV", "local")
    secret = inspect_secret_source(environ=environ, environment=requested_environment, require_external_source=requested_environment == "production")
    control_path = root / "control" / "manifest.json"
    control_issues: list[str] = []
    control: dict[str, Any] = {}
    try:
        control = json.loads(control_path.read_text(encoding="utf-8"))
        if control.get("scope") != "NFL only":
            control_issues.append("control scope must remain NFL only")
        if control.get("production_implementation_allowed") is not False:
            control_issues.append("production implementation must remain disabled during preflight")
        if requested_environment == "production" and control.get("production_implementation_allowed") is not True:
            control_issues.append("production preflight is blocked by the Stage 0 control gate")
    except (OSError, ValueError) as exc:
        control_issues.append(f"control manifest unavailable: {exc}")
    blockers = []
    if contract.get("status") != "valid":
        blockers.append("deployment_contract")
    if secret.get("status") != "valid":
        blockers.append("secret_source")
    if control_issues:
        blockers.append("control_plane")
    return {"status": "ready" if not blockers else "blocked", "environment": requested_environment, "deployment_contract": contract, "secret_source": secret, "control_plane": {"path": str(control_path), "stage": control.get("current_stage"), "issues": control_issues, "production_implementation_allowed": control.get("production_implementation_allowed")}, "blockers": blockers, "activation_performed": False}
