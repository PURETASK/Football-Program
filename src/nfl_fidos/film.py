"""Film tagging and self-scout primitives with source-linked observations."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_film_tag(
    *,
    tag_id: str,
    film_asset_id: str,
    tag: str,
    team: str,
    opponent: str,
    situation: str,
    source_ref: str,
    confidence: str = "moderate",
    clip_id: str | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not tag_id.startswith("FILM-TAG-"):
        issues.append({"code": "FILM-TAG-ID", "message": "Tag id must start with FILM-TAG-", "path": "tag_id"})
    if not film_asset_id.startswith("FILM-"):
        issues.append({"code": "FILM-ASSET-ID", "message": "Film asset id must start with FILM-", "path": "film_asset_id"})
    if not tag or not team or not opponent or not situation or not source_ref:
        issues.append({"code": "FILM-TAG-CONTEXT", "message": "Tag, teams, situation, and source are required", "path": "context"})
    if confidence not in {"low", "moderate", "high"}:
        issues.append({"code": "FILM-CONFIDENCE", "message": "Unknown confidence", "path": "confidence"})
    if clip_id is not None and not clip_id.startswith("CLIP-"):
        issues.append({"code": "FILM-CLIP-ID", "message": "Clip id must start with CLIP-", "path": "clip_id"})
    return {
        "id": tag_id,
        "film_asset_id": film_asset_id,
        "tag": tag,
        "context": {"team": team, "opponent": opponent, "situation": situation},
        "source": {"kind": "film_asset", "ref": source_ref},
        "clip_id": clip_id,
        "confidence": confidence,
        "status": "invalid" if issues else "valid",
        "issues": issues,
    }


def build_self_scout_report(*, report_id: str, team: str, tags: list[dict[str, Any]]) -> dict[str, Any]:
    valid_tags = [tag for tag in tags if tag.get("status") == "valid" and tag.get("context", {}).get("team") == team]
    distribution = Counter(tag["tag"] for tag in valid_tags)
    return {
        "id": report_id,
        "capability_id": "CAP-015",
        "workflow_id": "WF-002",
        "team": team,
        "sample_size": len(valid_tags),
        "tag_distribution": dict(distribution),
        "source_tag_ids": [tag["id"] for tag in valid_tags],
        "limitations": ["Self-scout summaries describe tagged observations and require staff interpretation."],
        "status": "draft",
    }
