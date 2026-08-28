"""Run a temporary provider-neutral secret-manager mount rehearsal."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from nfl_fidos.config import resolve_auth_secret
from nfl_fidos.secret_manager import inspect_secret_manager_mount
from nfl_fidos.secret_source import inspect_secret_source


def run_rehearsal() -> dict[str, Any]:
    synthetic_secret = "synthetic-secret-for-rehearsal-0123456789"
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-secret-manager-") as directory:
        mount = Path(directory) / "nfl-fidos-auth"
        mount.write_text(synthetic_secret, encoding="utf-8")
        environ = {"NFL_FIDOS_ENV":"production","NFL_FIDOS_SECRET_PROVIDER":"approved_secret_manager_mount","NFL_FIDOS_SECRET_MANAGER_NAME":"nfl-fidos-auth","NFL_FIDOS_SECRET_VERSION":"rehearsal-v1","NFL_FIDOS_SECRET_MANAGER_FILE":str(mount)}
        valid = inspect_secret_manager_mount(environ=environ, environment="production")
        source = inspect_secret_source(environ=environ, environment="production", require_external_source=True)
        resolved = resolve_auth_secret(environ=environ)
        invalid_env = {**environ, "NFL_FIDOS_SECRET_MANAGER_FILE":str(Path(directory) / "missing")}
        invalid = inspect_secret_manager_mount(environ=invalid_env, environment="production")
        serialized = json.dumps({"valid":valid,"source":source,"invalid":invalid})
        checks = {"valid_mount": valid.get("status") == "valid", "production_external_source": source.get("status") == "valid" and source.get("source_type") == "approved_secret_manager_mount", "resolution_matches_mount": resolved == synthetic_secret, "value_redacted": synthetic_secret not in serialized and valid.get("value_exposed") is False and source.get("value_exposed") is False, "missing_mount_fails_closed": invalid.get("status") == "invalid"}
        return {"status":"passed" if all(checks.values()) else "failed","temporary_workspace":True,"checks":checks,"value_exposed":False,"external_provider_called":False,"external_state_changed":False,"production_implementation_allowed":False}


if __name__ == "__main__":
    result = run_rehearsal()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
