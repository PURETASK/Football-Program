"""Organization-scoped media catalog and bounded clip service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .media import create_film_clip, register_film_asset
from .media_ingestion import ingest_media_file
from .tenant_repository import TenantRepository
from .media_storage import copy_authorized_media


class MediaCatalogService:
    """Persist authorized assets and clips while preserving source boundaries."""

    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def register_asset(
        self, *, file_path: str | Path, asset_id: str, duration_seconds: float,
        source: dict[str, Any], captured_at: str, team_context: str,
        allowed_roots: Iterable[str | Path], actor: str, storage_root: str | Path | None = None,
    ) -> dict[str, Any]:
        allowed_roots = list(allowed_roots)
        managed = None
        ingest_path = file_path
        ingest_roots = allowed_roots
        if storage_root is not None:
            managed = copy_authorized_media(source_path=file_path, storage_root=storage_root, organization_id=self.repository.organization_id, asset_id=asset_id, allowed_source_roots=allowed_roots)
            if managed["status"] != "stored":
                return managed
            ingest_path = managed["destination_path"]
            ingest_roots = [storage_root]
        catalog = ingest_media_file(file_path=ingest_path, asset_id=asset_id, organization_id=self.repository.organization_id, source=source, captured_at=captured_at, allowed_roots=ingest_roots)
        if catalog["status"] != "registered":
            return catalog
        asset = register_film_asset(
            asset_id=asset_id, uri=catalog["uri"], duration_seconds=duration_seconds,
            source=source, captured_at=captured_at, team_context=team_context,
        )
        asset.update({
            "organization_id": self.repository.organization_id,
            "file_name": catalog["file_name"], "media_type": catalog["media_type"],
            "size_bytes": catalog["size_bytes"], "sha256": catalog["sha256"],
        })
        if managed:
            asset.update({"original_uri": Path(file_path).resolve().as_uri(), "managed_storage": managed})
        if asset["status"] == "registered":
            return self.repository.put("film_assets", asset_id, asset, actor=actor, reason="authorized_media_asset_registered")
        return asset

    def create_clip(
        self, *, clip_id: str, asset_id: str, start_seconds: float, end_seconds: float,
        team: str, opponent: str, situation: str, actor: str,
    ) -> dict[str, Any]:
        asset = self.repository.get("film_assets", asset_id)
        if asset is None:
            raise KeyError(f"Unknown film asset: {asset_id}")
        clip = create_film_clip(
            clip_id=clip_id, asset=asset, start_seconds=start_seconds, end_seconds=end_seconds,
            team=team, opponent=opponent, situation=situation,
        )
        clip["organization_id"] = self.repository.organization_id
        if clip["status"] == "ready":
            return self.repository.put("film_clips", clip_id, clip, actor=actor, reason="bounded_film_clip_created")
        return clip

    def list_assets(self) -> list[dict[str, Any]]:
        return self.repository.list("film_assets")

    def list_clips(self, *, opponent: str | None = None, team: str | None = None) -> list[dict[str, Any]]:
        clips = self.repository.list("film_clips")
        return [clip for clip in clips if (not opponent or clip.get("context", {}).get("opponent") == opponent) and (not team or clip.get("context", {}).get("team") == team)]
