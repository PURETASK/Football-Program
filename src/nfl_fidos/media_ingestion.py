"""Authorized local media ingestion catalog with integrity and tenancy metadata."""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Iterable


ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
AUTHORIZED_SOURCE_KINDS = {"licensed_film", "team_film", "public_gamebook", "authorized_media"}


def ingest_media_file(
    *, file_path: str | Path, asset_id: str, organization_id: str, source: dict[str, Any],
    captured_at: str, allowed_roots: Iterable[str | Path] = (), max_bytes: int = 20_000_000_000,
) -> dict[str, Any]:
    """Catalog a media file without copying or executing it.

    The caller must provide an explicit authorized source and allowed storage
    roots. The resulting digest makes later clip references reproducible.
    """
    issues: list[dict[str, str]] = []
    path = Path(file_path).resolve()
    if not asset_id.startswith("FILM-"):
        issues.append({"code":"MEDIA-ASSET-ID", "message":"Asset id must start with FILM-", "path":"asset_id"})
    if not organization_id:
        issues.append({"code":"MEDIA-TENANT", "message":"Organization scope is required", "path":"organization_id"})
    if source.get("kind") not in AUTHORIZED_SOURCE_KINDS or not source.get("ref"):
        issues.append({"code":"MEDIA-SOURCE-AUTH", "message":"Media source must be authorized and cited", "path":"source"})
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append({"code":"MEDIA-FORMAT", "message":"Unsupported media format", "path":"file_path"})
    if not path.exists() or not path.is_file():
        issues.append({"code":"MEDIA-MISSING", "message":"Media file does not exist", "path":"file_path"})
    roots = [Path(root).resolve() for root in allowed_roots]
    if roots and not any(path == root or root in path.parents for root in roots):
        issues.append({"code":"MEDIA-ROOT", "message":"Media file is outside an approved storage root", "path":"file_path"})
    size = path.stat().st_size if path.exists() and path.is_file() else 0
    if size <= 0 or size > max_bytes:
        issues.append({"code":"MEDIA-SIZE", "message":"Media file size is outside permitted bounds", "path":"file_path"})
    digest = None
    if not issues:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
    return {
        "id": asset_id, "organization_id": organization_id, "uri": path.as_uri(),
        "file_name": path.name, "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size_bytes": size, "sha256": digest, "source": source, "captured_at": captured_at,
        "status": "registered" if not issues else "rejected", "issues": issues,
    }
