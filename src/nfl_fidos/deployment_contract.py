"""Validation for the non-deploying NFL FIDOS environment topology contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def validate_deployment_contract(*, path: str | Path) -> dict[str, Any]:
    contract_path = Path(path)
    issues: list[str] = []
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status":"invalid", "path":str(contract_path), "issues":[str(exc)]}
    if not contract.get("deployment_id", "").startswith("DEPLOY-"):
        issues.append("deployment_id must start with DEPLOY-")
    if contract.get("scope") != "NFL only":
        issues.append("deployment scope must remain NFL only")
    if contract.get("status") not in {"design_only", "approved"}:
        issues.append("deployment status is invalid")
    service_ids = {service.get("id") for service in contract.get("services", [])}
    for required in {"SERVICE-API", "SERVICE-MEDIA-WORKER", "SERVICE-SCHEDULER"}:
        if required not in service_ids:
            issues.append(f"missing required service: {required}")
    if not contract.get("storage") or not contract.get("secrets"):
        issues.append("storage and secret contracts are required")
    services = {service.get("id"): service for service in contract.get("services", [])}
    api = services.get("SERVICE-API", {})
    if api.get("health_path") != "/health" or not api.get("port"):
        issues.append("API service must declare a port and /health endpoint")
    worker = services.get("SERVICE-MEDIA-WORKER", {})
    if worker and (worker.get("bounded") is not True or worker.get("replicas") != 0):
        issues.append("media worker must be bounded and disabled by default")
    scheduler = services.get("SERVICE-SCHEDULER", {})
    if scheduler and (scheduler.get("dry_run_default") is not True or scheduler.get("replicas") != 0):
        issues.append("scheduler must default to dry-run and zero replicas")
    environment = contract.get("environment_contract", {})
    for key in ("NFL_FIDOS_ENV", "NFL_FIDOS_DATABASE", "NFL_FIDOS_OBSERVABILITY_PATH"):
        if not environment.get(key):
            issues.append(f"environment contract missing {key}")
    if contract.get("rollout", {}).get("approval_required") != "STAGE-0 owner approval":
        issues.append("rollout must require Stage 0 owner approval")
    if not contract.get("rollout", {}).get("rollback"):
        issues.append("rollback procedure is required")
    for secret in contract.get("secrets", []):
        if not secret.get("name") or not secret.get("source") or "required" not in secret:
            issues.append("secret contract entries require name, source, and required metadata")
        if secret.get("source") not in {"approved_secret_manager_mount", "mounted_file", "environment_value"}:
            issues.append("secret contract source must identify an approved reference type")
        if any(key.lower() in {"value", "secret", "token", "credential"} for key in secret):
            issues.append("secret contract must contain references, never secret values")
    if contract.get("production_implementation_allowed") is not False:
        issues.append("design contract must not enable production implementation")
    return {"status":"valid" if not issues else "invalid", "path":str(contract_path), "deployment_id":contract.get("deployment_id"), "service_count":len(contract.get("services", [])), "issues":issues, "production_implementation_allowed":contract.get("production_implementation_allowed")}
