"""Small versioned JSON repository for canonical records and audit events.

This is a local foundation, not a replacement for the Stage 21 production
database. It provides deterministic semantics that a later database adapter
must preserve: append-only events, record revisions, and explicit actors.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class JsonRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._state = {"records": {}, "events": []}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                self._state = json.load(handle)
        self._state.setdefault("records", {})
        self._state.setdefault("events", [])

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f"{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._state, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def put(self, collection: str, record_id: str, record: dict[str, Any], *, actor: str, reason: str) -> dict[str, Any]:
        """Persist a record through the repository's serialized write boundary."""
        with self._lock:
            return self._put_unlocked(collection, record_id, record, actor=actor, reason=reason)

    def _put_unlocked(self, collection: str, record_id: str, record: dict[str, Any], *, actor: str, reason: str) -> dict[str, Any]:
        if not collection or not record_id or not actor or not reason:
            raise ValueError("collection, record_id, actor, and reason are required")
        records = self._state["records"].setdefault(collection, {})
        previous = records.get(record_id)
        revision = (previous.get("_revision", 0) + 1) if previous else 1
        saved = deepcopy(record)
        saved.update({"_revision": revision, "_saved_at": datetime.now(timezone.utc).isoformat(), "_saved_by": actor})
        records[record_id] = saved
        self._state["events"].append({
            "event_id": f"EVENT-{len(self._state['events']) + 1:06d}",
            "type": "record_saved",
            "collection": collection,
            "record_id": record_id,
            "revision": revision,
            "actor": actor,
            "reason": reason,
            "at": saved["_saved_at"],
        })
        self._persist()
        return deepcopy(saved)

    def put_if_revision(self, collection: str, record_id: str, record: dict[str, Any], *, expected_revision: int | None, actor: str, reason: str) -> dict[str, Any]:
        """Atomically write only when the record is still at ``expected_revision``.

        The compare-and-swap boundary is intentionally inside the repository
        lock.  Play Designer clients can therefore safely use this primitive
        for concurrent edits instead of relying on a check followed by a
        separate write.
        """
        if not collection or not record_id or not actor or not reason:
            raise ValueError("collection, record_id, actor, and reason are required")
        with self._lock:
            records = self._state["records"].setdefault(collection, {})
            previous = records.get(record_id)
            actual_revision = previous.get("_revision") if previous else None
            if actual_revision != expected_revision:
                raise ValueError({
                    "code": "DESIGN-CONFLICT",
                    "message": "Design changed since it was loaded",
                    "expected_revision": expected_revision,
                    "actual_revision": actual_revision,
                    "server_record": deepcopy(previous) if previous else None,
                })
            revision = (previous.get("_revision", 0) + 1) if previous else 1
            saved = deepcopy(record)
            saved.update({"_revision": revision, "_saved_at": datetime.now(timezone.utc).isoformat(), "_saved_by": actor})
            records[record_id] = saved
            self._state["events"].append({
                "event_id": f"EVENT-{len(self._state['events']) + 1:06d}",
                "type": "record_saved",
                "collection": collection,
                "record_id": record_id,
                "revision": revision,
                "actor": actor,
                "reason": reason,
                "at": saved["_saved_at"],
            })
            self._persist()
            return deepcopy(saved)

    def get(self, collection: str, record_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._state["records"].get(collection, {}).get(record_id)
            return deepcopy(record) if record is not None else None

    def list(self, collection: str) -> list[dict[str, Any]]:
        with self._lock:
            return [deepcopy(record) for record in self._state["records"].get(collection, {}).values()]

    def history(self, *, collection: str | None = None, record_id: str | None = None) -> list[dict[str, Any]]:
        events = self._state["events"]
        if collection is not None:
            events = [event for event in events if event.get("collection") == collection]
        if record_id is not None:
            events = [event for event in events if event.get("record_id") == record_id]
        return deepcopy(events)

    def delete_where(self, predicate: Callable[[str, dict[str, Any]], bool], *, delete_events: bool = True) -> dict[str, int]:
        """Delete records selected by a caller-owned predicate.

        This narrow primitive exists for explicitly scoped maintenance such as
        removing synthetic demo fixtures. Callers must provide the complete
        selection predicate; no wildcard or collection-wide delete is exposed.
        Matching audit events are removed only for deleted record identities.
        """
        selected: set[tuple[str, str]] = set()
        for collection, records in self._state["records"].items():
            for record_id, record in records.items():
                if predicate(collection, record):
                    selected.add((collection, record_id))
        for collection, record_id in selected:
            self._state["records"].get(collection, {}).pop(record_id, None)
        deleted_events = 0
        if delete_events and selected:
            kept_events = []
            for event in self._state["events"]:
                identity = (event.get("collection"), event.get("record_id"))
                if identity in selected:
                    deleted_events += 1
                else:
                    kept_events.append(event)
            self._state["events"] = kept_events
        if selected:
            self._persist()
        return {"deleted_records": len(selected), "deleted_events": deleted_events}
