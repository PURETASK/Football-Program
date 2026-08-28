"""Provider-neutral bounded export of structured observability events."""

from __future__ import annotations

from typing import Any, Callable, Iterable


EventSink = Callable[[dict[str, Any]], None]


def export_events(events: Iterable[dict[str, Any]], *, sink: EventSink, max_events: int = 1000) -> dict[str, Any]:
    if max_events <= 0:
        raise ValueError("max_events must be positive")
    selected_events = list(events)[:max_events]
    exported = 0
    failures: list[dict[str, str]] = []
    for event in selected_events:
        try:
            sink(event)
            exported += 1
        except Exception as exc:  # sink failures are evidence, not silent success
            failures.append({"event_id":str(event.get("event_id", "unknown")), "error":type(exc).__name__})
    return {"status":"completed" if not failures else "partial_failure", "selected":len(selected_events), "exported":exported, "failed":len(failures), "failures":failures}
