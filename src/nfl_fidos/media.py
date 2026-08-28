"""Film asset and time-bounded clip ingestion primitives."""

from __future__ import annotations

from typing import Any


def register_film_asset(
    *,
    asset_id: str,
    uri: str,
    duration_seconds: float,
    source: dict[str, str],
    captured_at: str,
    team_context: str,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not asset_id.startswith("FILM-"):
        issues.append({"code": "FILM-ASSET-ID", "message": "Asset id must start with FILM-", "path": "asset_id"})
    if not uri:
        issues.append({"code": "FILM-ASSET-URI", "message": "Asset URI is required", "path": "uri"})
    if duration_seconds <= 0:
        issues.append({"code": "FILM-ASSET-DURATION", "message": "Duration must be positive", "path": "duration_seconds"})
    if not source.get("kind") or not source.get("ref") or not captured_at or not team_context:
        issues.append({"code": "FILM-ASSET-PROVENANCE", "message": "Source, timestamp, and team context are required", "path": "provenance"})
    return {
        "id": asset_id, "uri": uri, "duration_seconds": duration_seconds, "source": source,
        "captured_at": captured_at, "team_context": team_context,
        "status": "rejected" if issues else "registered", "issues": issues,
    }


def create_film_clip(
    *,
    clip_id: str,
    asset: dict[str, Any],
    start_seconds: float,
    end_seconds: float,
    team: str,
    opponent: str,
    situation: str,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not clip_id.startswith("CLIP-"):
        issues.append({"code": "CLIP-ID", "message": "Clip id must start with CLIP-", "path": "clip_id"})
    if asset.get("status") not in {"registered", "ready"}:
        issues.append({"code": "CLIP-ASSET", "message": "Clip asset must be registered or ready", "path": "asset.status"})
    duration = asset.get("duration_seconds", 0)
    if start_seconds < 0 or end_seconds <= start_seconds or end_seconds > duration:
        issues.append({"code": "CLIP-RANGE", "message": "Clip range must be within the asset duration", "path": "time_range"})
    if not team or not opponent or not situation:
        issues.append({"code": "CLIP-CONTEXT", "message": "Team, opponent, and situation are required", "path": "context"})
    return {
        "id": clip_id, "asset_id": asset.get("id"), "start_seconds": start_seconds, "end_seconds": end_seconds,
        "context": {"team": team, "opponent": opponent, "situation": situation},
        "source": {"kind": "film_asset", "ref": asset.get("id")},
        "status": "rejected" if issues else "ready", "issues": issues,
    }
