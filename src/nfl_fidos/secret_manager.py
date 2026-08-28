"""Provider-neutral secret-manager mount adapter with value-free evidence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


PROVIDER_ENV = "NFL_FIDOS_SECRET_PROVIDER"
MOUNT_ENV = "NFL_FIDOS_SECRET_MANAGER_FILE"
NAME_ENV = "NFL_FIDOS_SECRET_MANAGER_NAME"
VERSION_ENV = "NFL_FIDOS_SECRET_VERSION"


def inspect_secret_manager_mount(*, environ: dict[str, str] | None = None, environment: str = "local") -> dict[str, Any]:
    values = os.environ if environ is None else environ
    provider = values.get(PROVIDER_ENV, "").strip()
    mount_ref = values.get(MOUNT_ENV, "").strip() or values.get("NFL_FIDOS_AUTH_SECRET_FILE", "").strip()
    name = values.get(NAME_ENV, "").strip()
    version = values.get(VERSION_ENV, "").strip()
    issues: list[str] = []
    configured = bool(provider or mount_ref or name or version)
    if not configured:
        return {"status":"not_configured", "configured":False, "value_exposed":False, "environment":environment, "source_type":"none", "issues":[]}
    if provider != "approved_secret_manager_mount":
        issues.append("NFL_FIDOS_SECRET_PROVIDER must be approved_secret_manager_mount")
    if not mount_ref:
        issues.append("secret-manager mount file is required")
    if not name:
        issues.append("secret-manager name is required")
    if not version:
        issues.append("secret-manager version is required")
    path = Path(mount_ref).expanduser().resolve() if mount_ref else None
    readable = bool(path and path.is_file() and os.access(path, os.R_OK))
    if mount_ref and not readable:
        issues.append("secret-manager mount file is not readable")
    length = 0
    if readable:
        try:
            length = len(path.read_text(encoding="utf-8").strip())
        except OSError:
            issues.append("secret-manager mount file could not be read")
    if length == 0 and readable:
        issues.append("secret-manager mount file is empty")
    if environment == "production" and length < 32:
        issues.append("production authentication secret must contain at least 32 characters")
    return {"status":"valid" if not issues else "invalid", "configured":True, "value_exposed":False, "environment":environment, "source_type":"approved_secret_manager_mount", "manager_name":name, "version":version, "mount_reference":str(path) if path else None, "readable":readable, "length":length, "issues":issues}


def resolve_secret_manager_mount(*, environ: dict[str, str] | None = None) -> str:
    values = os.environ if environ is None else environ
    report = inspect_secret_manager_mount(environ=values, environment=values.get("NFL_FIDOS_ENV", "local"))
    if report["status"] != "valid":
        raise ValueError("secret-manager mount is not valid: " + "; ".join(report["issues"]))
    path = Path(report["mount_reference"])
    return path.read_text(encoding="utf-8").strip()
