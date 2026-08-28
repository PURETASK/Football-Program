"""Run a bounded, temporary backup/restore validation drill."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nfl_fidos.database_operations import backup_sqlite_database, restore_sqlite_backup, verify_sqlite_database
from nfl_fidos.sqlite_repository import SqliteRepository


def run_drill() -> dict:
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-db-drill-") as directory:
        root = Path(directory)
        source = root / "source.sqlite3"
        backup = root / "backup.sqlite3"
        restored = root / "restored.sqlite3"
        repository = SqliteRepository(source)
        repository.put("drill_records", "DRILL-001", {"id":"DRILL-001", "organization_id":"ORG-DRILL", "value":"preserved"}, actor="DRILL", reason="backup_restore_drill")
        repository.close()
        created = backup_sqlite_database(source, backup, actor="DRILL")
        restored_report = restore_sqlite_backup(backup, restored, actor="DRILL")
        result = {"read_only_to_workspace": True, "source_integrity": verify_sqlite_database(source), "backup": created, "restore": restored_report, "status": "passed" if created.get("content_match") and restored_report.get("content_match") else "failed"}
    return result


if __name__ == "__main__":
    result = run_drill()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
