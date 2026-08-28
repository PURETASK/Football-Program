"""Deployment-readiness checks for configuration, control, database, and evals."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .config import load_config
from .database_operations import verify_sqlite_database
from .migrations import inspect_migrations
from .security_audit import run_security_audit
from .play_designer_quality import run_play_designer_quality_gates


def _check(check_id: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "blocker", **details}


def _writable_location(path: Path) -> tuple[bool, Path]:
    candidate = path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate.exists() and os.access(candidate, os.W_OK), candidate


def run_operational_readiness(
    *,
    environ: dict[str, str] | None = None,
    database_path: str | Path | None = None,
    run_evals: bool = True,
    eval_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an evidence-bearing readiness report; this function never changes state."""
    values = dict(os.environ if environ is None else environ)
    checks: list[dict[str, Any]] = []
    try:
        config = load_config(environ=values, require_auth_secret=True)
        checks.append(_check("runtime_config", True, {"environment": config.environment, "host": config.host, "port": config.port, "ffmpeg_binary": config.ffmpeg_binary, "ffprobe_binary": config.ffprobe_binary, "observability_path": str(config.observability_path)}))
        observability_ready, writable_location = _writable_location(config.observability_path)
        checks.append(_check("observability_sink", observability_ready, {"path":str(config.observability_path), "writable_location":str(writable_location), "parent_writable":observability_ready}))
        if config.environment == "production":
            ffmpeg_path = shutil.which(config.ffmpeg_binary)
            ffprobe_path = shutil.which(config.ffprobe_binary)
            checks.append(_check("media_tooling", bool(ffmpeg_path and ffprobe_path), {"ffmpeg": ffmpeg_path, "ffprobe": ffprobe_path, "error": "ffmpeg and ffprobe must be installed and discoverable in production" if not (ffmpeg_path and ffprobe_path) else None}))
    except (TypeError, ValueError) as exc:
        config = None
        checks.append(_check("runtime_config", False, {"error": str(exc)}))

    path = Path(database_path or (config.database_path if config else values.get("NFL_FIDOS_DATABASE", ".runtime/nfl_fidos.sqlite3"))).expanduser().resolve()
    parent = path.parent
    parent_ready = parent.exists() and os.access(parent, os.W_OK)
    checks.append(_check("database_parent", parent_ready, {"path": str(parent), "writable": parent_ready}))
    if path.exists():
        integrity = verify_sqlite_database(path)
        checks.append(_check("database_integrity", integrity.get("status") == "valid", {**integrity, "status": "pass" if integrity.get("status") == "valid" else "blocker"}))
        migrations = inspect_migrations(path)
        checks.append(_check("database_migrations", not migrations.get("pending"), migrations))
    else:
        checks.append(_check("database_integrity", False, {"path": str(path), "status": "missing", "error": "database must be provisioned and migrated"}))
        checks.append(_check("database_migrations", False, {"path": str(path), "status": "missing", "error": "database must be provisioned and migrated"}))

    if eval_result is not None:
        checks.append(_check("evaluation_suite", eval_result.get("status") == "passed", {"passed": eval_result.get("passed"), "failed": eval_result.get("failed"), "suite_id": eval_result.get("suite_id")}))
    elif run_evals:
        from .evals import run_minimum_eval_suite
        result = run_minimum_eval_suite()
        checks.append(_check("evaluation_suite", result.get("status") == "passed", {"passed": result.get("passed"), "failed": result.get("failed"), "suite_id": result.get("suite_id")}))
    else:
        checks.append(_check("evaluation_suite", False, {"status": "not_run", "error": "readiness requires a current evaluation result"}))

    root = Path(__file__).resolve().parents[2]
    control_manifest = root / "control" / "manifest.json"
    control_ok = False
    control_details: dict[str, Any] = {"path": str(control_manifest)}
    try:
        import json
        with control_manifest.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        control_ok = manifest.get("scope") == "NFL only" and manifest.get("current_stage") == "STAGE-0" and manifest.get("production_implementation_allowed") is False
        control_details.update({"scope": manifest.get("scope"), "stage": manifest.get("current_stage"), "production_implementation_allowed": manifest.get("production_implementation_allowed")})
    except (OSError, ValueError) as exc:
        control_details["error"] = str(exc)
    checks.append(_check("control_plane", control_ok, control_details))
    security = run_security_audit(root=Path(__file__).resolve().parents[2], environ=values, environment=config.environment if config else values.get("NFL_FIDOS_ENV", "local"))
    checks.append(_check("security_posture", security.get("status") == "ready", {"posture_status": security.get("status"), "checks": security.get("checks"), "control_families": security.get("control_families"), "production_implementation_allowed": security.get("production_implementation_allowed")}))
    designer_quality = run_play_designer_quality_gates(root=Path(__file__).resolve().parents[2])
    checks.append(_check("play_designer_quality", designer_quality.get("status") == "passed", {"quality_status": designer_quality.get("status"), "checks": designer_quality.get("checks"), "limitations": designer_quality.get("limitations")}))
    blockers = [check["id"] for check in checks if check["status"] != "pass"]
    return {"status": "ready" if not blockers else "blocked", "database_path": str(path), "checks": checks, "security_posture": security, "play_designer_quality": designer_quality, "blockers": blockers, "human_approval_required": "STAGE-0 owner approval" in blockers}
