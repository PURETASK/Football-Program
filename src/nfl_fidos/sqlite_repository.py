"""SQLite adapter preserving the canonical repository contract."""

from __future__ import annotations

import json
import sqlite3
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA = """
CREATE TABLE IF NOT EXISTS canonical_records (
  collection TEXT NOT NULL,
  record_id TEXT NOT NULL,
  revision INTEGER NOT NULL,
  data_json TEXT NOT NULL,
  saved_at TEXT NOT NULL,
  saved_by TEXT NOT NULL,
  organization_id TEXT,
  PRIMARY KEY (collection, record_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  collection TEXT NOT NULL,
  record_id TEXT NOT NULL,
  revision INTEGER NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL,
  occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_events(collection, record_id, revision);
CREATE INDEX IF NOT EXISTS idx_canonical_organization ON canonical_records(organization_id);
"""


class SqliteRepository:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def put(self, collection: str, record_id: str, record: dict[str, Any], *, actor: str, reason: str) -> dict[str, Any]:
        if not collection or not record_id or not actor or not reason:
            raise ValueError("collection, record_id, actor, and reason are required")
        with self._lock:
            current = self.connection.execute(
                "SELECT revision FROM canonical_records WHERE collection = ? AND record_id = ?",
                (collection, record_id),
            ).fetchone()
            revision = (current["revision"] + 1) if current else 1
            timestamp = datetime.now(timezone.utc).isoformat()
            saved = deepcopy(record)
            saved.update({"_revision": revision, "_saved_at": timestamp, "_saved_by": actor})
            event_id = f"EVENT-{collection}-{record_id}-{revision}"
            with self.connection:
                self.connection.execute(
                    "INSERT OR REPLACE INTO canonical_records(collection, record_id, revision, data_json, saved_at, saved_by, organization_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (collection, record_id, revision, json.dumps(saved, sort_keys=True), timestamp, actor, saved.get("organization_id")),
                )
                self.connection.execute(
                    "INSERT INTO audit_events(event_id, event_type, collection, record_id, revision, actor, reason, occurred_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (event_id, "record_saved", collection, record_id, revision, actor, reason, timestamp),
                )
        return deepcopy(saved)

    def put_if_revision(self, collection: str, record_id: str, record: dict[str, Any], *, expected_revision: int | None, actor: str, reason: str) -> dict[str, Any]:
        """Atomically compare the current revision and persist the next one."""
        if not collection or not record_id or not actor or not reason:
            raise ValueError("collection, record_id, actor, and reason are required")
        with self._lock:
            # IMMEDIATE acquires the database writer lock before the revision
            # is read. This protects compare-and-swap semantics across
            # independent connections and therefore across worker processes;
            # the instance lock alone would only protect one Python object.
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                current = self.connection.execute(
                    "SELECT revision, data_json FROM canonical_records WHERE collection = ? AND record_id = ?",
                    (collection, record_id),
                ).fetchone()
                actual_revision = current["revision"] if current else None
                if actual_revision != expected_revision:
                    server_record = json.loads(current["data_json"]) if current else None
                    self.connection.rollback()
                    raise ValueError({
                        "code": "DESIGN-CONFLICT",
                        "message": "Design changed since it was loaded",
                        "expected_revision": expected_revision,
                        "actual_revision": actual_revision,
                        "server_record": server_record,
                    })
                revision = (actual_revision + 1) if actual_revision is not None else 1
                timestamp = datetime.now(timezone.utc).isoformat()
                saved = deepcopy(record)
                saved.update({"_revision": revision, "_saved_at": timestamp, "_saved_by": actor})
                event_id = f"EVENT-{collection}-{record_id}-{revision}"
                self.connection.execute(
                    "INSERT OR REPLACE INTO canonical_records(collection, record_id, revision, data_json, saved_at, saved_by, organization_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (collection, record_id, revision, json.dumps(saved, sort_keys=True), timestamp, actor, saved.get("organization_id")),
                )
                self.connection.execute(
                    "INSERT INTO audit_events(event_id, event_type, collection, record_id, revision, actor, reason, occurred_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (event_id, "record_saved", collection, record_id, revision, actor, reason, timestamp),
                )
                self.connection.commit()
                return deepcopy(saved)
            except Exception:
                if self.connection.in_transaction:
                    self.connection.rollback()
                raise

    def get(self, collection: str, record_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT data_json FROM canonical_records WHERE collection = ? AND record_id = ?",
                (collection, record_id),
            ).fetchone()
        return json.loads(row["data_json"]) if row else None

    def list(self, collection: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT data_json FROM canonical_records WHERE collection = ? ORDER BY record_id",
                (collection,),
            ).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def history(self, *, collection: str | None = None, record_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT event_id, event_type, collection, record_id, revision, actor, reason, occurred_at FROM audit_events WHERE 1=1"
        params: list[str] = []
        if collection is not None:
            query += " AND collection = ?"
            params.append(collection)
        if record_id is not None:
            query += " AND record_id = ?"
            params.append(record_id)
        query += " ORDER BY revision, event_id"
        with self._lock:
            return [dict(row) for row in self.connection.execute(query, params).fetchall()]

    def delete_where(self, predicate: Callable[[str, dict[str, Any]], bool], *, delete_events: bool = True) -> dict[str, int]:
        """Delete records selected by a caller-owned predicate.

        This is intentionally predicate-based rather than exposing a broad
        delete-by-collection operation. It is used by the fail-closed synthetic
        demo cleanup workflow and preserves unrelated tenant records.
        """
        with self._lock:
            rows = self.connection.execute("SELECT collection, record_id, data_json FROM canonical_records").fetchall()
            selected = []
            for row in rows:
                record = json.loads(row["data_json"])
                if predicate(row["collection"], record):
                    selected.append((row["collection"], row["record_id"]))
            deleted_events = 0
            with self.connection:
                for collection, record_id in selected:
                    self.connection.execute(
                        "DELETE FROM canonical_records WHERE collection = ? AND record_id = ?",
                        (collection, record_id),
                    )
                    if delete_events:
                        cursor = self.connection.execute(
                            "DELETE FROM audit_events WHERE collection = ? AND record_id = ?",
                            (collection, record_id),
                        )
                        deleted_events += cursor.rowcount
            return {"deleted_records": len(selected), "deleted_events": deleted_events}
