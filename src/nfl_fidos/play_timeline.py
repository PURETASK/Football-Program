"""Canonical timing, phase, cue, and narration primitives for play designs.

The UI can animate a diagram locally, but the organization-scoped server must
store the same timeline contract so a coach, player view, export, and future
renderer all agree on when an assignment starts, develops, finishes, or
triggers a teaching cue.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_DURATION_MS = 3000
DEFAULT_ELEMENT_DURATION_MS = 1200
MIN_TIMELINE_MS = -5000
MARKER_KINDS = {"snap", "cue", "pause", "read", "rotation", "exchange", "ball", "handoff"}
EVENT_KINDS = {"ball", "handoff", "exchange", "block_exchange", "rush_exchange", "read", "rotation", "throw", "catch", "contact", "cue"}
EVENT_KIND_ALIASES = {"qb_read": "read", "coverage_rotation": "rotation", "pass": "throw", "completion": "catch"}

PHASE_TEMPLATES: dict[str, tuple[tuple[str, str, float, float], ...]] = {
    "route": (("release", "Release", 0.0, 0.18), ("stem", "Stem", 0.18, 0.48), ("break", "Break", 0.48, 0.72), ("finish", "Finish", 0.72, 1.0)),
    "motion": (("align", "Align", 0.0, 0.2), ("travel", "Travel", 0.2, 0.78), ("settle", "Settle", 0.78, 1.0)),
    "run": (("mesh", "Mesh", 0.0, 0.25), ("track", "Track", 0.25, 0.72), ("finish", "Finish", 0.72, 1.0)),
    "block": (("strike", "Strike", 0.0, 0.22), ("fit", "Fit", 0.22, 0.58), ("sustain", "Sustain", 0.58, 1.0)),
    "coverage": (("pedal", "Pedal", 0.0, 0.25), ("match", "Match", 0.25, 0.72), ("close", "Close", 0.72, 1.0)),
    "rush": (("getoff", "Get off", 0.0, 0.22), ("attack", "Attack", 0.22, 0.62), ("finish", "Finish", 0.62, 1.0)),
    "stunt": (("penetrate", "Penetrate", 0.0, 0.32), ("exchange", "Exchange", 0.32, 0.68), ("finish", "Finish", 0.68, 1.0)),
    "rotation": (("key", "Key", 0.0, 0.25), ("rotate", "Rotate", 0.25, 0.72), ("fit", "Fit", 0.72, 1.0)),
    "read": (("identify", "Identify", 0.0, 0.3), ("confirm", "Confirm", 0.3, 0.72), ("decide", "Decide", 0.72, 1.0)),
    "annotation": (("teach", "Teach", 0.0, 1.0),),
}


def _integer(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return value


def _issue(code: str, message: str, path: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": severity}


def default_phases(kind: str | None, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    """Return deterministic football teaching phases for an element."""
    template = PHASE_TEMPLATES.get(kind or "annotation", PHASE_TEMPLATES["annotation"])
    span = max(1, end_ms - start_ms)
    phases: list[dict[str, Any]] = []
    for phase_id, label, start_ratio, end_ratio in template:
        phase_start = round(start_ms + span * start_ratio)
        phase_end = max(phase_start + 1, round(start_ms + span * end_ratio))
        phases.append({"id": phase_id, "label": label, "start_ms": phase_start, "end_ms": phase_end})
    return phases


def normalize_timeline_design(design: dict[str, Any], *, default_duration_ms: int = DEFAULT_DURATION_MS) -> dict[str, Any]:
    """Return a copy with a complete, renderer-safe timeline envelope.

    Normalization is intentionally deterministic and non-authoritative: it
    fills missing phase metadata and clamps UI convenience fields, while
    validation still reports malformed input before a release can be trusted.
    """
    output = deepcopy(design)
    timeline = output.setdefault("timeline", {})
    if not isinstance(timeline, dict):
        timeline = {}
        output["timeline"] = timeline
    snap_ms = _integer(timeline.get("snap_ms"), 0)
    timeline["snap_ms"] = max(0, snap_ms or 0)
    timeline["markers"] = timeline.get("markers") if isinstance(timeline.get("markers"), list) else []
    timeline["narration"] = timeline.get("narration") if isinstance(timeline.get("narration"), list) else []
    timeline["events"] = timeline.get("events") if isinstance(timeline.get("events"), list) else []

    elements = output.get("elements") if isinstance(output.get("elements"), list) else []
    output["elements"] = elements
    maximum = max(1, default_duration_ms)
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        timing = element.get("timing") if isinstance(element.get("timing"), dict) else {}
        start = _integer(timing.get("start_ms"), _integer(element.get("start_ms"), 0)) or 0
        start = max(MIN_TIMELINE_MS, start)
        end_default = _integer(element.get("end_ms"), start + DEFAULT_ELEMENT_DURATION_MS) or start + DEFAULT_ELEMENT_DURATION_MS
        end = _integer(timing.get("end_ms"), end_default) or end_default
        end = max(start + 1, end)
        raw_phases = timing.get("phases") if isinstance(timing.get("phases"), list) else []
        phases: list[dict[str, Any]] = []
        for phase_index, raw_phase in enumerate(raw_phases or default_phases(str(element.get("kind", "annotation")), start, end)):
            if not isinstance(raw_phase, dict):
                continue
            phase_start = _integer(raw_phase.get("start_ms"), start) or start
            phase_end = _integer(raw_phase.get("end_ms"), end) or end
            phase_start = max(start, min(end - 1, phase_start))
            phase_end = max(phase_start + 1, min(end, phase_end))
            phases.append({
                **raw_phase,
                "id": str(raw_phase.get("id") or f"phase-{phase_index + 1}"),
                "label": str(raw_phase.get("label") or raw_phase.get("id") or f"Phase {phase_index + 1}"),
                "start_ms": phase_start,
                "end_ms": phase_end,
            })
        if not phases:
            phases = default_phases(str(element.get("kind", "annotation")), start, end)
        element["start_ms"] = start
        element["end_ms"] = end
        element["timing"] = {**timing, "start_ms": start, "end_ms": end, "phases": phases}
        maximum = max(maximum, end)

    duration = _integer(timeline.get("duration_ms"), maximum) or maximum
    timeline["duration_ms"] = max(maximum, duration, 1)
    for marker_index, marker in enumerate(timeline["markers"]):
        if not isinstance(marker, dict):
            continue
        marker["id"] = str(marker.get("id") or f"MARK-{marker_index + 1}")
        marker["label"] = str(marker.get("label") or f"Cue {marker_index + 1}")
        marker["kind"] = str(marker.get("kind") or "cue")
        marker_ms = _integer(marker.get("ms"), 0) or 0
        marker["ms"] = max(MIN_TIMELINE_MS, min(timeline["duration_ms"], marker_ms))
    for narration_index, cue in enumerate(timeline["narration"]):
        if not isinstance(cue, dict):
            continue
        start = _integer(cue.get("start_ms"), 0) or 0
        end = _integer(cue.get("end_ms"), start + 700) or start + 700
        start = max(MIN_TIMELINE_MS, min(timeline["duration_ms"], start))
        end = max(start + 1, min(timeline["duration_ms"], end))
        cue.update({"id": str(cue.get("id") or f"NARRATION-{narration_index + 1}"), "start_ms": start, "end_ms": end, "role": str(cue.get("role") or "coach"), "text": str(cue.get("text") or "")})
    for event_index, event in enumerate(timeline["events"]):
        if not isinstance(event, dict):
            continue
        raw_kind = str(event.get("kind") or event.get("type") or "cue")
        kind = EVENT_KIND_ALIASES.get(raw_kind, raw_kind)
        start = _integer(event.get("start_ms"), _integer(event.get("at_ms"), _integer(event.get("ms"), 0))) or 0
        start = max(MIN_TIMELINE_MS, min(timeline["duration_ms"], start))
        event.update({"id": str(event.get("id") or f"EVENT-{event_index + 1}"), "kind": kind, "start_ms": start})
        if event.get("end_ms") is not None or kind in {"ball", "handoff"}:
            end = _integer(event.get("end_ms"), start + 1) or start + 1
            event["end_ms"] = max(start + 1, min(timeline["duration_ms"], end))
    return output


def validate_timeline(design: dict[str, Any]) -> list[dict[str, str]]:
    """Validate optional timeline metadata and explain every invalid field."""
    timeline = design.get("timeline")
    if not isinstance(timeline, dict):
        return []
    issues: list[dict[str, str]] = []
    duration = timeline.get("duration_ms")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0):
        issues.append(_issue("TIMELINE-DURATION", "Timeline duration_ms must be a positive integer", "timeline.duration_ms"))
    snap = timeline.get("snap_ms")
    if snap is not None and (isinstance(snap, bool) or not isinstance(snap, int) or snap < 0):
        issues.append(_issue("TIMELINE-SNAP", "Timeline snap_ms must be a non-negative integer", "timeline.snap_ms"))
    duration_limit = duration if isinstance(duration, int) and duration > 0 else None

    markers = timeline.get("markers")
    if markers is not None:
        if not isinstance(markers, list):
            issues.append(_issue("TIMELINE-MARKERS", "Timeline markers must be a list", "timeline.markers"))
        else:
            marker_ids: set[str] = set()
            for index, marker in enumerate(markers):
                path = f"timeline.markers[{index}]"
                if not isinstance(marker, dict):
                    issues.append(_issue("TIMELINE-MARKER-SHAPE", "Timeline marker must be an object", path))
                    continue
                marker_id = marker.get("id")
                if not isinstance(marker_id, str) or not marker_id:
                    issues.append(_issue("TIMELINE-MARKER-ID", "Timeline marker id is required", f"{path}.id"))
                elif marker_id in marker_ids:
                    issues.append(_issue("TIMELINE-DUPLICATE-MARKER", f"Duplicate timeline marker id: {marker_id}", f"{path}.id"))
                marker_ids.add(marker_id)
                marker_ms = marker.get("ms")
                if isinstance(marker_ms, bool) or not isinstance(marker_ms, int) or marker_ms < MIN_TIMELINE_MS or duration_limit is not None and marker_ms > duration_limit:
                    issues.append(_issue("TIMELINE-MARKER-TIME", "Timeline marker ms must be within the supported pre-snap and timeline duration", f"{path}.ms"))
                if marker.get("kind", "cue") not in MARKER_KINDS:
                    issues.append(_issue("TIMELINE-MARKER-KIND", "Timeline marker kind is not supported", f"{path}.kind"))

    narration = timeline.get("narration")
    if narration is not None:
        if not isinstance(narration, list):
            issues.append(_issue("TIMELINE-NARRATION", "Timeline narration must be a list", "timeline.narration"))
        else:
            for index, cue in enumerate(narration):
                path = f"timeline.narration[{index}]"
                if not isinstance(cue, dict):
                    issues.append(_issue("TIMELINE-NARRATION-SHAPE", "Narration cue must be an object", path))
                    continue
                if not isinstance(cue.get("text"), str) or not cue.get("text", "").strip():
                    issues.append(_issue("TIMELINE-NARRATION-TEXT", "Narration cue text is required", f"{path}.text"))
                start = cue.get("start_ms")
                end = cue.get("end_ms")
                if isinstance(start, bool) or not isinstance(start, int) or start < MIN_TIMELINE_MS:
                    issues.append(_issue("TIMELINE-NARRATION-START", "Narration start_ms must be within the supported pre-snap window", f"{path}.start_ms"))
                if isinstance(end, bool) or not isinstance(end, int) or end <= (start if isinstance(start, int) else 0):
                    issues.append(_issue("TIMELINE-NARRATION-END", "Narration end_ms must be after start_ms", f"{path}.end_ms"))
                if duration_limit is not None and isinstance(end, int) and end > duration_limit:
                    issues.append(_issue("TIMELINE-NARRATION-BOUNDS", "Narration must finish within the timeline duration", f"{path}.end_ms"))

    elements = design.get("elements") if isinstance(design.get("elements"), list) else []
    element_ids = {element.get("id") for element in elements if isinstance(element, dict)}
    player_ids = {player.get("id") for player in design.get("players", []) if isinstance(player, dict)}
    events = timeline.get("events")
    if events is not None:
        if not isinstance(events, list):
            issues.append(_issue("TIMELINE-EVENTS", "Timeline events must be a list", "timeline.events"))
        else:
            event_ids: set[str] = set()
            for index, event in enumerate(events):
                path = f"timeline.events[{index}]"
                if not isinstance(event, dict):
                    issues.append(_issue("TIMELINE-EVENT-SHAPE", "Timeline event must be an object", path))
                    continue
                event_id = event.get("id")
                if not isinstance(event_id, str) or not event_id:
                    issues.append(_issue("TIMELINE-EVENT-ID", "Timeline event id is required", f"{path}.id"))
                elif event_id in event_ids:
                    issues.append(_issue("TIMELINE-DUPLICATE-EVENT", f"Duplicate timeline event id: {event_id}", f"{path}.id"))
                event_ids.add(event_id)
                raw_kind = str(event.get("kind") or event.get("type") or "")
                kind = EVENT_KIND_ALIASES.get(raw_kind, raw_kind)
                if kind not in EVENT_KINDS:
                    issues.append(_issue("TIMELINE-EVENT-KIND", "Timeline event kind is not supported", f"{path}.kind"))
                start = event.get("start_ms", event.get("at_ms", event.get("ms")))
                end = event.get("end_ms")
                if isinstance(start, bool) or not isinstance(start, int) or start < MIN_TIMELINE_MS or duration_limit is not None and start > duration_limit:
                    issues.append(_issue("TIMELINE-EVENT-START", "Timeline event start must be within the supported clock", f"{path}.start_ms"))
                if end is not None and (isinstance(end, bool) or not isinstance(end, int) or end <= (start if isinstance(start, int) else MIN_TIMELINE_MS - 1)):
                    issues.append(_issue("TIMELINE-EVENT-END", "Timeline event end_ms must be after its start", f"{path}.end_ms"))
                if duration_limit is not None and isinstance(end, int) and end > duration_limit:
                    issues.append(_issue("TIMELINE-EVENT-BOUNDS", "Timeline event must finish within the timeline duration", f"{path}.end_ms"))
                if event.get("element_id") is not None and event.get("element_id") not in element_ids:
                    issues.append(_issue("TIMELINE-EVENT-ELEMENT", "Timeline event references an unknown element", f"{path}.element_id"))
                for field in ("player_id", "target_player_id"):
                    if event.get(field) is not None and event.get(field) not in player_ids:
                        issues.append(_issue("TIMELINE-EVENT-PLAYER", "Timeline event references an unknown player", f"{path}.{field}"))
                if kind in {"ball", "handoff"} and not event.get("element_id"):
                    issues.append(_issue("TIMELINE-EVENT-PATH", "Ball and handoff events must reference a path element", f"{path}.element_id"))
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        path = f"elements[{index}]"
        start = element.get("start_ms")
        end = element.get("end_ms")
        timing = element.get("timing")
        if timing is not None and not isinstance(timing, dict):
            issues.append(_issue("TIMELINE-ELEMENT-TIMING", "Element timing must be an object", f"{path}.timing"))
            timing = None
        if isinstance(timing, dict):
            start = timing.get("start_ms", start)
            end = timing.get("end_ms", end)
        if start is not None and (isinstance(start, bool) or not isinstance(start, int) or start < MIN_TIMELINE_MS):
            issues.append(_issue("TIMELINE-ELEMENT-START", "Element start_ms must be within the supported pre-snap window", f"{path}.start_ms"))
        if end is not None and (isinstance(end, bool) or not isinstance(end, int) or end <= (start if isinstance(start, int) else -1)):
            issues.append(_issue("TIMELINE-ELEMENT-END", "Element end_ms must be after start_ms", f"{path}.end_ms"))
        if duration_limit is not None and isinstance(end, int) and end > duration_limit:
            issues.append(_issue("TIMELINE-ELEMENT-BOUNDS", "Element timing must finish within the timeline duration", f"{path}.end_ms"))
        phases = timing.get("phases") if isinstance(timing, dict) else None
        if phases is not None:
            if not isinstance(phases, list):
                issues.append(_issue("TIMELINE-PHASES", "Element phases must be a list", f"{path}.timing.phases"))
            else:
                phase_ids: set[str] = set()
                for phase_index, phase in enumerate(phases):
                    phase_path = f"{path}.timing.phases[{phase_index}]"
                    if not isinstance(phase, dict):
                        issues.append(_issue("TIMELINE-PHASE-SHAPE", "Element phase must be an object", phase_path))
                        continue
                    phase_id = phase.get("id")
                    if not isinstance(phase_id, str) or not phase_id:
                        issues.append(_issue("TIMELINE-PHASE-ID", "Element phase id is required", f"{phase_path}.id"))
                    elif phase_id in phase_ids:
                        issues.append(_issue("TIMELINE-DUPLICATE-PHASE", f"Duplicate phase id: {phase_id}", f"{phase_path}.id"))
                    phase_ids.add(phase_id)
                    phase_start, phase_end = phase.get("start_ms"), phase.get("end_ms")
                    if isinstance(phase_start, bool) or not isinstance(phase_start, int) or phase_start < (start if isinstance(start, int) else 0):
                        issues.append(_issue("TIMELINE-PHASE-START", "Phase start_ms is outside the element timing range", f"{phase_path}.start_ms"))
                    if isinstance(phase_end, bool) or not isinstance(phase_end, int) or phase_end <= (phase_start if isinstance(phase_start, int) else 0) or isinstance(end, int) and phase_end > end:
                        issues.append(_issue("TIMELINE-PHASE-END", "Phase end_ms is outside the element timing range", f"{phase_path}.end_ms"))
        exchange_with = element.get("exchange_with")
        if exchange_with is not None and exchange_with not in element_ids:
            issues.append(_issue("TIMELINE-EXCHANGE-REF", "Exchange target must reference an existing element", f"{path}.exchange_with"))
    return issues
