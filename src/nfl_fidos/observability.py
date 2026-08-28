"""Structured runtime evidence for operations, governance, and audit review."""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from .security_controls import redact_sensitive


REQUIRED_FIELDS = {"event_id", "request_id", "actor", "organization_id", "operation", "status", "duration_ms", "error_code", "source_refs"}


class ObservabilityRecorder:
    def __init__(self, path: str | Path, *, sink: Callable[[dict[str, Any]], None] | None = None):
        self.path = Path(path)
        self.sink = sink

    def record(self, *, operation: str, status: str, actor: str, organization_id: str, duration_ms: float, error_code: str | None = None, source_refs: list[str] | None = None, request_id: str | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        event: dict[str, Any] = {
            "event_id": f"OBS-{uuid.uuid4().hex}", "request_id": request_id or f"REQ-{uuid.uuid4().hex}",
            "actor": actor, "organization_id": organization_id, "operation": operation, "status": status,
            "duration_ms": round(max(0.0, float(duration_ms)), 3), "error_code": error_code, "source_refs": source_refs or [],
        }
        if extra:
            event.update(redact_sensitive(extra))
        event = redact_sensitive(event)
        missing = REQUIRED_FIELDS - set(event)
        if missing:
            raise ValueError(f"Observability event missing fields: {sorted(missing)}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        if self.sink is not None:
            self.sink(event)
        return event

    @contextmanager
    def span(self, *, operation: str, actor: str, organization_id: str, source_refs: list[str] | None = None, request_id: str | None = None) -> Iterator[dict[str, Any]]:
        started = time.perf_counter()
        result: dict[str, Any] = {"status": "ok", "error_code": None}
        try:
            yield result
        except Exception as exc:
            result.update({"status": "error", "error_code": type(exc).__name__})
            raise
        finally:
            self.record(operation=operation, status=result["status"], actor=actor, organization_id=organization_id, duration_ms=(time.perf_counter() - started) * 1000, error_code=result["error_code"], source_refs=source_refs, request_id=request_id)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
