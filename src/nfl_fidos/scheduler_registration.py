"""Provider-neutral scheduler registration validation without external writes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ALLOWED_OPERATIONS = {"source_refresh", "media_retention_scan", "media_transform_batch"}


def load_scheduler_registration(path: str | Path | None = None) -> dict[str, Any]:
    registration_path = Path(path) if path else Path(__file__).resolve().parents[2] / "operations" / "scheduler-registration.json"
    return json.loads(registration_path.read_text(encoding="utf-8"))


def validate_scheduler_registration(*, registration: dict[str, Any], environ: dict[str, str] | None = None, environment: str = "local") -> dict[str, Any]:
    values = os.environ if environ is None else environ
    issues: list[str] = []
    if registration.get("scope") != "NFL only":
        issues.append("scheduler registration must be NFL-scoped")
    if registration.get("provider_neutral") is not True:
        issues.append("scheduler registration must remain provider-neutral")
    if registration.get("dry_run_default") is not True:
        issues.append("scheduler registration must default to dry-run")
    if registration.get("external_registration_required") is not True:
        issues.append("external registration must remain an explicit deployment step")
    jobs = registration.get("jobs", [])
    if not jobs:
        issues.append("at least one scheduler job is required")
    job_ids: set[str] = set()
    for job in jobs:
        job_id = job.get("id")
        if not isinstance(job_id, str) or not job_id.startswith("SCHEDULER-JOB-") or job_id in job_ids:
            issues.append(f"invalid or duplicate scheduler job id: {job_id}")
        job_ids.add(job_id)
        if job.get("operation") not in ALLOWED_OPERATIONS:
            issues.append(f"unsupported scheduler operation: {job.get('operation')}")
        if not job.get("schedule"):
            issues.append(f"scheduler job has no schedule: {job_id}")
        if job.get("entrypoint") != "scripts/scheduled_operations.py":
            issues.append(f"scheduler job entrypoint is not bounded: {job_id}")
    bounds = registration.get("bounds", {})
    for key in ("max_sources", "max_transforms", "retention_days"):
        if not isinstance(bounds.get(key), int) or bounds[key] <= 0:
            issues.append(f"scheduler bound must be a positive integer: {key}")
    provider = values.get("NFL_FIDOS_SCHEDULER_PROVIDER", "provider_neutral").strip()
    registration_ref = values.get("NFL_FIDOS_SCHEDULER_REGISTRATION_REF", "").strip()
    if provider != "provider_neutral":
        issues.append("only the provider-neutral scheduler boundary is currently supported")
    if registration_ref and not registration_ref.startswith("SCHEDULER-REG-"):
        issues.append("scheduler registration reference must start with SCHEDULER-REG-")
    if environment == "production" and not registration_ref:
        issues.append("production scheduler deployment requires a SCHEDULER-REG-* registration reference")
    return {
        "status": "ready" if not issues else "blocked",
        "environment": environment,
        "provider": provider,
        "registration_id": registration.get("registration_id"),
        "registration_ref": registration_ref or None,
        "job_count": len(job_ids),
        "bounds": bounds,
        "dry_run_default": registration.get("dry_run_default"),
        "external_registration_performed": False,
        "external_state_changed": False,
        "human_approval_required": environment == "production",
        "issues": issues,
    }
