"""Value-free inspection of configured authentication secret sources."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .secret_manager import inspect_secret_manager_mount


def inspect_secret_source(*, environ: dict[str, str] | None = None, environment: str = "local", require_external_source: bool = False) -> dict[str, Any]:
    values = os.environ if environ is None else environ
    if values.get("NFL_FIDOS_SECRET_PROVIDER", "").strip() or values.get("NFL_FIDOS_SECRET_MANAGER_FILE", "").strip():
        manager = inspect_secret_manager_mount(environ=values, environment=environment)
        return manager
    file_ref = values.get("NFL_FIDOS_AUTH_SECRET_FILE", "").strip()
    inline = values.get("NFL_FIDOS_AUTH_SECRET", "")
    source_type = "mounted_file" if file_ref else "environment_value" if inline else "missing"
    issues: list[str] = []
    metadata: dict[str, Any] = {"source_type": source_type, "configured": bool(file_ref or inline), "value_exposed": False, "environment": environment}
    if file_ref:
        path = Path(file_ref).expanduser().resolve()
        metadata.update({"reference": str(path), "readable": path.is_file() and os.access(path, os.R_OK)})
        if not metadata["readable"]:
            issues.append("configured secret file is not readable")
        else:
            try:
                secret = path.read_text(encoding="utf-8").strip()
                metadata["length"] = len(secret)
                if not secret:
                    issues.append("configured secret file is empty")
            except OSError:
                issues.append("configured secret file could not be read")
    elif inline:
        metadata["length"] = len(inline)
    else:
        issues.append("authentication secret source is not configured")
    if environment == "production" and metadata.get("length", 0) < 32:
        issues.append("production authentication secret must contain at least 32 characters")
    if require_external_source and source_type not in {"mounted_file", "approved_secret_manager_mount"}:
        issues.append("production preflight requires a mounted external secret source")
    return {**metadata, "status": "valid" if not issues else "invalid", "issues": issues}
