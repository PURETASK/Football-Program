"""Operational SQLite backup, integrity, restore, and retention primitives."""

from __future__ import annotations

import sqlite3
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def fingerprint_sqlite_database(path: str | Path) -> str:
    database = Path(path).resolve()
    digest = hashlib.sha256()
    connection = sqlite3.connect(database)
    try:
        for statement in connection.iterdump():
            digest.update(statement.encode("utf-8"))
            digest.update(b"\n")
    finally:
        connection.close()
    return digest.hexdigest()


def verify_sqlite_database(path: str | Path) -> dict[str, Any]:
    database = Path(path).resolve()
    if not database.exists() or not database.is_file():
        return {"path": str(database), "status": "invalid", "error": "database does not exist"}
    connection = sqlite3.connect(database)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        journal = connection.execute("PRAGMA journal_mode").fetchone()[0]
        return {"path": str(database), "status": "valid" if result == "ok" else "invalid", "integrity_check": result, "journal_mode": journal}
    finally:
        connection.close()


def backup_sqlite_database(source: str | Path, destination: str | Path, *, actor: str = "backup-runner") -> dict[str, Any]:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise ValueError("backup destination must differ from source database")
    source_check = verify_sqlite_database(source_path)
    if source_check["status"] != "valid":
        raise ValueError("source database failed integrity verification")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination_path.with_suffix(destination_path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    source_connection = sqlite3.connect(source_path)
    destination_connection = sqlite3.connect(temporary)
    try:
        source_connection.backup(destination_connection)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()
    temporary.replace(destination_path)
    check = verify_sqlite_database(destination_path)
    source_fingerprint = fingerprint_sqlite_database(source_path)
    destination_fingerprint = fingerprint_sqlite_database(destination_path)
    return {"status": "created" if check["status"] == "valid" else "invalid", "source": str(source_path), "destination": str(destination_path), "actor": actor, "created_at": datetime.now(timezone.utc).isoformat(), "source_sha256": source_fingerprint, "destination_sha256": destination_fingerprint, "content_match": source_fingerprint == destination_fingerprint, "verification": check}


def restore_sqlite_backup(backup: str | Path, destination: str | Path, *, actor: str = "restore-runner") -> dict[str, Any]:
    backup_path = Path(backup).resolve()
    destination_path = Path(destination).resolve()
    if backup_path == destination_path:
        raise ValueError("restore destination must differ from backup")
    check = verify_sqlite_database(backup_path)
    if check["status"] != "valid":
        raise ValueError("backup failed integrity verification")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination_path.with_suffix(destination_path.suffix + ".restore.tmp")
    if temporary.exists():
        temporary.unlink()
    shutil.copy2(backup_path, temporary)
    restored = verify_sqlite_database(temporary)
    if restored["status"] != "valid":
        temporary.unlink(missing_ok=True)
        raise ValueError("restored database failed integrity verification")
    temporary.replace(destination_path)
    backup_fingerprint = fingerprint_sqlite_database(backup_path)
    destination_fingerprint = fingerprint_sqlite_database(destination_path)
    return {"status": "restored", "backup": str(backup_path), "destination": str(destination_path), "actor": actor, "backup_sha256": backup_fingerprint, "destination_sha256": destination_fingerprint, "content_match": backup_fingerprint == destination_fingerprint, "verification": verify_sqlite_database(destination_path)}


def plan_backup_retention(directory: str | Path, *, keep: int = 7) -> dict[str, Any]:
    if keep <= 0:
        raise ValueError("keep must be positive")
    root = Path(directory).resolve()
    backups = sorted((path for path in root.glob("*.sqlite*") if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True)
    return {"directory": str(root), "keep": keep, "retained": [str(path) for path in backups[:keep]], "candidates": [str(path) for path in backups[keep:]], "destructive_action_required": True}
