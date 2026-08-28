"""Versioned SQLite migrations with dry-run, snapshot, and rollback controls."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .sqlite_repository import SCHEMA


LATEST_SCHEMA_VERSION = 1


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def inspect_migrations(path: str | Path) -> dict[str, Any]:
    database = Path(path)
    if not database.exists():
        return {"path": str(database), "exists": False, "version": 0, "latest_version": LATEST_SCHEMA_VERSION, "pending": [LATEST_SCHEMA_VERSION]}
    connection = sqlite3.connect(database)
    try:
        connection.executescript(SCHEMA)
        connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)")
        row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
        version = int(row[0])
        return {"path": str(database), "exists": True, "version": version, "latest_version": LATEST_SCHEMA_VERSION, "pending": list(range(version + 1, LATEST_SCHEMA_VERSION + 1))}
    finally:
        connection.close()


def apply_migrations(path: str | Path, *, dry_run: bool = False, snapshot_path: str | Path | None = None, actor: str = "migration-runner") -> dict[str, Any]:
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    before = inspect_migrations(database)
    if dry_run:
        return {**before, "dry_run": True, "status": "planned" if before["pending"] else "current"}
    if snapshot_path and database.exists():
        snapshot = Path(snapshot_path)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(database, snapshot)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(SCHEMA)
        connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)")
        current = int(connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0])
        if current < 1:
            if "organization_id" not in _columns(connection, "canonical_records"):
                connection.execute("ALTER TABLE canonical_records ADD COLUMN organization_id TEXT")
            rows = connection.execute("SELECT collection, record_id, data_json FROM canonical_records").fetchall()
            for row in rows:
                try:
                    organization_id = json.loads(row["data_json"]).get("organization_id")
                except (TypeError, json.JSONDecodeError):
                    organization_id = None
                connection.execute("UPDATE canonical_records SET organization_id = ? WHERE collection = ? AND record_id = ?", (organization_id, row["collection"], row["record_id"]))
            connection.execute("CREATE INDEX IF NOT EXISTS idx_canonical_organization ON canonical_records(organization_id)")
            connection.execute("INSERT INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)", (1, datetime.now(timezone.utc).isoformat(), f"{actor}: add organization scope and index"))
        connection.commit()
        return {**inspect_migrations(database), "dry_run": False, "status": "current", "snapshot": str(snapshot_path) if snapshot_path else None}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def rollback_snapshot(path: str | Path, snapshot_path: str | Path) -> dict[str, Any]:
    database = Path(path)
    snapshot = Path(snapshot_path)
    if not snapshot.exists():
        raise FileNotFoundError(f"Snapshot does not exist: {snapshot}")
    shutil.copy2(snapshot, database)
    return {"status": "rolled_back", "path": str(database), "snapshot": str(snapshot)}
