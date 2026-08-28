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
    services_list = contract.get("services", [])
    if not isinstance(services_list, list) or not services_list:
        issues.append("services must be a non-empty list")
        services_list = []
    service_ids = {service.get("id") for service in services_list if isinstance(service, dict)}
    if len(service_ids) != len(services_list):
        issues.append("service IDs must be unique and every service must be an object")
    for required in {"SERVICE-API", "SERVICE-MEDIA-WORKER", "SERVICE-SCHEDULER"}:
        if required not in service_ids:
            issues.append(f"missing required service: {required}")
    storage = contract.get("storage", [])
    secrets = contract.get("secrets", [])
    if not storage or not secrets:
        issues.append("storage and secret contracts are required")
    storage_mounts: set[str] = set()
    if not isinstance(storage, list):
        issues.append("storage contract must be a list")
        storage = []
    for volume in storage:
        if not isinstance(volume, dict) or not volume.get("name") or not volume.get("mount") or not volume.get("purpose"):
            issues.append("storage entries require name, mount, and purpose metadata")
            continue
        mount = volume["mount"]
        if mount in storage_mounts:
            issues.append(f"storage mount must be unique: {mount}")
        storage_mounts.add(mount)
        if not isinstance(mount, str) or not mount.startswith("/"):
            issues.append(f"storage mount must be an absolute path: {mount}")
    services = {service.get("id"): service for service in services_list if isinstance(service, dict)}
    api = services.get("SERVICE-API", {})
    if api.get("health_path") != "/health" or not isinstance(api.get("port"), int) or api.get("port", 0) <= 0 or api.get("port", 0) > 65535:
        issues.append("API service must declare a port and /health endpoint")
    for service_id, service in services.items():
        if not isinstance(service.get("name"), str) or not service.get("name"):
            issues.append(f"service must declare a name: {service_id}")
        if not isinstance(service.get("image"), str) or not service.get("image"):
            issues.append(f"service must declare an image: {service_id}")
        if not isinstance(service.get("command"), list) or not service.get("command"):
            issues.append(f"service must declare a bounded command: {service_id}")
    worker = services.get("SERVICE-MEDIA-WORKER", {})
    if worker and (worker.get("bounded") is not True or worker.get("replicas") != 0):
        issues.append("media worker must be bounded and disabled by default")
    scheduler = services.get("SERVICE-SCHEDULER", {})
    if scheduler and (scheduler.get("dry_run_default") is not True or scheduler.get("replicas") != 0):
        issues.append("scheduler must default to dry-run and zero replicas")
    environment = contract.get("environment_contract", {})
    if not isinstance(environment, dict):
        issues.append("environment_contract must be an object")
        environment = {}
    for key in ("NFL_FIDOS_ENV", "NFL_FIDOS_DATABASE", "NFL_FIDOS_OBSERVABILITY_PATH"):
        if not environment.get(key):
            issues.append(f"environment contract missing {key}")
    if environment.get("NFL_FIDOS_ENV") != "production":
        issues.append("deployment environment contract must explicitly describe production")
    if environment.get("NFL_FIDOS_HOST") != "0.0.0.0":
        issues.append("production deployment must bind the API to 0.0.0.0")
    if not isinstance(environment.get("NFL_FIDOS_PORT"), int) or not 1 <= environment.get("NFL_FIDOS_PORT", 0) <= 65535:
        issues.append("production environment must declare a valid integer NFL_FIDOS_PORT")
    if api.get("port") and environment.get("NFL_FIDOS_PORT") and api.get("port") != environment.get("NFL_FIDOS_PORT"):
        issues.append("API service port must match NFL_FIDOS_PORT")
    if contract.get("rollout", {}).get("approval_required") != "STAGE-0 owner approval":
        issues.append("rollout must require Stage 0 owner approval")
    if not contract.get("rollout", {}).get("rollback"):
        issues.append("rollback procedure is required")
    if not isinstance(secrets, list):
        issues.append("secret contract must be a list")
        secrets = []
    secret_names: set[str] = set()
    for secret in secrets:
        if not isinstance(secret, dict):
            issues.append("secret contract entries must be objects")
            continue
        if not secret.get("name") or not secret.get("source") or "required" not in secret:
            issues.append("secret contract entries require name, source, and required metadata")
        if secret.get("name") in secret_names:
            issues.append(f"secret names must be unique: {secret.get('name')}")
        secret_names.add(secret.get("name"))
        if secret.get("source") not in {"approved_secret_manager_mount", "mounted_file", "environment_value"}:
            issues.append("secret contract source must identify an approved reference type")
        if any(key.lower() in {"value", "secret", "token", "credential"} for key in secret):
            issues.append("secret contract must contain references, never secret values")
    rollout = contract.get("rollout", {})
    if not isinstance(rollout, dict) or rollout.get("feature_flags_default_off") is not True:
        issues.append("rollout must default feature flags off")
    if contract.get("production_implementation_allowed") is not False:
        issues.append("design contract must not enable production implementation")
    return {"status":"valid" if not issues else "invalid", "path":str(contract_path), "deployment_id":contract.get("deployment_id"), "service_count":len(contract.get("services", [])), "issues":issues, "production_implementation_allowed":contract.get("production_implementation_allowed")}
