"""Bounded facility/staff availability validation for practice planning."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _time(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
    except ValueError:
        return None


def plan_practice_resources(*, organization_id: str, practice_id: str, schedule: dict[str, Any], availability: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    if not organization_id.startswith("ORG-") or not practice_id.startswith("PRACTICE-"):
        errors.append("organization_id and practice_id must use controlled prefixes")
    if not schedule.get("schedule_id", "").startswith("PRACTICE-SCHEDULE-"):
        errors.append("schedule_id must start with PRACTICE-SCHEDULE-")
    periods = schedule.get("periods", [])
    if not periods:
        errors.append("at least one scheduled period is required")
    windows: list[dict[str, Any]] = []
    for index, period in enumerate(periods):
        start, end = _time(period.get("start")), _time(period.get("end"))
        if not period.get("period_id") or start is None or end is None or end <= start:
            errors.append(f"periods[{index}] requires a valid period_id and increasing start/end")
            continue
        resources = period.get("resource_ids", [])
        if not resources:
            errors.append(f"periods[{index}] requires resource_ids")
        windows.append({"period_id":period["period_id"], "start":start, "end":end, "resource_ids":resources})
    availability_map: dict[str, list[tuple[datetime, datetime]]] = {}
    for index, window in enumerate(availability):
        if window.get("organization_id") != organization_id:
            errors.append(f"availability[{index}] organization scope mismatch")
        start, end = _time(window.get("available_from")), _time(window.get("available_to"))
        if not window.get("resource_id") or start is None or end is None or end <= start:
            errors.append(f"availability[{index}] requires a valid resource_id and increasing available_from/available_to")
            continue
        availability_map.setdefault(window["resource_id"], []).append((start, end))
    conflicts: list[dict[str, Any]] = []
    for index, left in enumerate(windows):
        for right in windows[index + 1:]:
            shared = sorted(set(left["resource_ids"]) & set(right["resource_ids"]))
            if shared and left["start"] < right["end"] and right["start"] < left["end"]:
                conflicts.append({"type":"scheduled_overlap", "period_ids":[left["period_id"], right["period_id"]], "resource_ids":shared})
        for resource_id in left["resource_ids"]:
            supported = any(start <= left["start"] and end >= left["end"] for start, end in availability_map.get(resource_id, []))
            if not supported:
                conflicts.append({"type":"resource_unavailable", "period_id":left["period_id"], "resource_id":resource_id})
    return {"schedule_id":schedule.get("schedule_id"), "organization_id":organization_id, "practice_id":practice_id, "status":"blocked" if errors or conflicts else "ready", "errors":errors, "conflicts":conflicts, "scheduled_period_count":len(windows), "resource_count":len(availability_map), "human_review_required":True, "external_calendar_mutation":False}
