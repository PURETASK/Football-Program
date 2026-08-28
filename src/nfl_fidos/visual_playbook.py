"""Deterministic visual, animation, and what-if models for Stage 10."""

from __future__ import annotations

from typing import Any


FIELD_LENGTH = 120.0
FIELD_WIDTH = 53.333


def _point(point: dict[str, Any], path: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for axis, maximum in (("x", FIELD_LENGTH), ("y", FIELD_WIDTH)):
        value = point.get(axis)
        if not isinstance(value, (int, float)) or not 0 <= value <= maximum:
            issues.append({"code":"VISUAL-COORDINATE", "message":f"{axis} must be between 0 and {maximum}", "path":f"{path}.{axis}"})
    return issues


def validate_visual_play(visual: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "play_id", "source_play_version", "players", "paths", "timeline", "accessibility"):
        if field not in visual or visual[field] in (None, "", []):
            issues.append({"code":"VISUAL-REQUIRED", "message":f"Missing visual field: {field}", "path":field})
    if visual.get("id") and not visual["id"].startswith("VISUAL-"):
        issues.append({"code":"VISUAL-ID", "message":"Visual id must start with VISUAL-", "path":"id"})
    player_ids: set[str] = set()
    for index, player in enumerate(visual.get("players", [])):
        path = f"players[{index}]"
        if not player.get("id") or not player.get("role"):
            issues.append({"code":"VISUAL-PLAYER", "message":"Player requires id and role", "path":path})
        if player.get("id") in player_ids:
            issues.append({"code":"VISUAL-DUPLICATE", "message":"Duplicate player id", "path":path})
        player_ids.add(player.get("id"))
        issues.extend(_point(player.get("position", {}), f"{path}.position"))
    for index, path_record in enumerate(visual.get("paths", [])):
        path = f"paths[{index}]"
        if path_record.get("player_id") not in player_ids:
            issues.append({"code":"VISUAL-PATH-PLAYER", "message":"Path references unknown player", "path":path})
        points = path_record.get("points", [])
        if not isinstance(points, list) or len(points) < 2:
            issues.append({"code":"VISUAL-PATH", "message":"Path requires at least two points", "path":f"{path}.points"})
        for point_index, point in enumerate(points):
            issues.extend(_point(point, f"{path}.points[{point_index}]"))
    timeline = visual.get("timeline", [])
    times = [event.get("time_ms") for event in timeline if isinstance(event, dict)]
    if any(not isinstance(time, (int, float)) or time < 0 for time in times) or times != sorted(times):
        issues.append({"code":"VISUAL-TIMELINE", "message":"Timeline times must be non-negative and ordered", "path":"timeline"})
    if not isinstance(visual.get("accessibility"), list) or not visual["accessibility"]:
        issues.append({"code":"VISUAL-ACCESSIBILITY", "message":"Text-equivalent accessibility metadata is required", "path":"accessibility"})
    return issues


def build_visual_play(*, visual_id: str, play: dict[str, Any], players: list[dict[str, Any]], paths: list[dict[str, Any]], timeline: list[dict[str, Any]], role_views: list[str], accessibility: list[str]) -> dict[str, Any]:
    output = {
        "id": visual_id, "play_id": play.get("id"), "source_play_version": play.get("version"),
        "players": players, "paths": paths, "timeline": timeline, "role_views": role_views,
        "accessibility": accessibility, "overlays": {"offense": True, "defense": False},
        "interactions": ["isolate_assignment", "advance_read", "toggle_overlay", "apply_what_if", "reset"],
    }
    issues = validate_visual_play(output)
    output["status"] = "invalid" if issues else "renderable"
    output["issues"] = issues
    return output


def build_animation_timeline(*, timeline_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    times = [event.get("time_ms") for event in events]
    issues = [] if times == sorted(times) and all(isinstance(time, (int, float)) and time >= 0 for time in times) else [{"code":"TIMELINE-ORDER", "message":"Events must have ordered non-negative time_ms values", "path":"events"}]
    return {"id":timeline_id, "events":events, "status":"valid" if not issues else "invalid", "issues":issues, "seek_safe":not bool(issues)}


def simulate_what_if(*, simulation_id: str, canonical_visual: dict[str, Any], adjustment: dict[str, Any], requester_role: str) -> dict[str, Any]:
    """Return a separate scenario; never mutate or silently replace canonical play data."""
    if canonical_visual.get("status") != "renderable" or not adjustment.get("type"):
        return {"id":simulation_id, "status":"rejected", "reason":"renderable canonical visual and adjustment type are required"}
    return {
        "id":simulation_id, "source_visual_id":canonical_visual["id"], "adjustment":adjustment,
        "requester_role":requester_role, "status":"scenario_ready", "human_review_required":True,
        "canonical_unchanged":True, "overlay_mode":"what_if",
    }
