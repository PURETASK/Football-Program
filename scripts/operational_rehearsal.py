#!/usr/bin/env python3
"""Run a bounded, temporary rehearsal of the deployment-readiness controls."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nfl_fidos.database_operations import backup_sqlite_database, restore_sqlite_backup
from nfl_fidos.deployment_contract import validate_deployment_contract
from nfl_fidos.migrations import apply_migrations
from nfl_fidos.operational_readiness import run_operational_readiness
from nfl_fidos.scheduled_operations import ScheduledOperationsService
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


def run_rehearsal() -> dict:
    root = Path(__file__).resolve().parents[1]
    deployment = validate_deployment_contract(path=root / "deployment" / "nfl-fidos-deployment.json")
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-operational-rehearsal-") as directory:
        workspace = Path(directory)
        database = workspace / "nfl_fidos.sqlite3"
        backup = workspace / "nfl_fidos.backup.sqlite3"
        restored = workspace / "nfl_fidos.restored.sqlite3"
        observability = workspace / "observability.jsonl"

        repository = SqliteRepository(database)
        repository.put("rehearsal_records", "REHEARSAL-001", {"id":"REHEARSAL-001", "organization_id":"ORG-REHEARSAL", "status":"temporary"}, actor="REHEARSAL", reason="operational_rehearsal")
        repository.close()
        migration = apply_migrations(database, actor="REHEARSAL")
        backup_result = backup_sqlite_database(database, backup, actor="REHEARSAL")
        restore_result = restore_sqlite_backup(backup, restored, actor="REHEARSAL")
        readiness = run_operational_readiness(
            environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"r" * 32, "NFL_FIDOS_DATABASE":str(database), "NFL_FIDOS_OBSERVABILITY_PATH":str(observability)},
            database_path=database,
        )
        tenant_repository = TenantRepository(SqliteRepository(database), organization_id="ORG-REHEARSAL", actor="REHEARSAL")
        scheduled = ScheduledOperationsService(tenant_repository, environment="validation", control_root=root).run(actor="REHEARSAL", worker_id="WORKER-REHEARSAL", execute=False, max_sources=2, max_transforms=2, retention_days=30)
        production_guard = ScheduledOperationsService(tenant_repository, environment="production", control_root=root).run(actor="REHEARSAL", worker_id="WORKER-REHEARSAL", execute=True, max_sources=2, max_transforms=2, retention_days=30)
        close = getattr(tenant_repository.repository, "close", None)
        if close:
            close()
        result = {
            "status":"passed" if deployment["status"] == "valid" and migration["status"] == "current" and backup_result.get("content_match") and restore_result.get("content_match") and readiness["status"] == "ready" and scheduled["dry_run"] and production_guard["status"] == "blocked" else "failed",
            "temporary_workspace":True,
            "deployment":deployment,
            "migration":migration,
            "backup_content_match":backup_result.get("content_match"),
            "restore_content_match":restore_result.get("content_match"),
            "readiness_status":readiness["status"],
            "scheduled_dry_run":scheduled["dry_run"],
            "production_guard_status":production_guard["status"],
            "production_guard_blocker":production_guard.get("blocker"),
            "production_implementation_allowed":False,
            "external_state_changed":False,
        }
    return result


if __name__ == "__main__":
    report = run_rehearsal()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "passed" else 1)
