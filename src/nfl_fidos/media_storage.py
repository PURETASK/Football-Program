"""Atomic, provenance-preserving managed media storage primitives."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Iterable

from .media_ingestion import ALLOWED_EXTENSIONS


def copy_authorized_media(*, source_path: str | Path, storage_root: str | Path, organization_id: str, asset_id: str, allowed_source_roots: Iterable[str | Path], max_bytes: int = 20_000_000_000) -> dict[str, Any]:
    """Copy media atomically into an org/asset namespace without overwriting."""
    source = Path(source_path).resolve()
    root = Path(storage_root).resolve()
    issues: list[str] = []
    if not organization_id or not asset_id.startswith("FILM-"):
        issues.append("organization_id and FILM-* asset_id are required")
    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append("unsupported media extension")
    if not source.exists() or not source.is_file():
        issues.append("source media file does not exist")
    source_roots = [Path(value).resolve() for value in allowed_source_roots]
    if not source_roots or not any(source == allowed or allowed in source.parents for allowed in source_roots):
        issues.append("source is outside approved source roots")
    size = source.stat().st_size if source.exists() and source.is_file() else 0
    if size <= 0 or size > max_bytes:
        issues.append("source size is outside permitted bounds")
    destination = (root / organization_id / f"{asset_id}{source.suffix.lower()}").resolve()
    if root not in destination.parents:
        issues.append("destination escaped storage root")
    if destination.exists():
        issues.append("managed destination already exists")
    if issues:
        return {"status":"rejected", "source_path":str(source), "destination_path":str(destination), "issues":issues}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    hasher = hashlib.sha256()
    try:
        with source.open("rb") as source_handle, temporary.open("wb") as destination_handle:
            for chunk in iter(lambda: source_handle.read(1024 * 1024), b""):
                hasher.update(chunk)
                destination_handle.write(chunk)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
        if destination.exists():
            temporary.unlink(missing_ok=True)
            return {"status":"rejected", "source_path":str(source), "destination_path":str(destination), "issues":["managed destination appeared during copy"]}
        temporary.replace(destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        return {"status":"failed", "source_path":str(source), "destination_path":str(destination), "issues":[str(exc)]}
    return {"status":"stored", "source_path":str(source), "destination_path":str(destination), "organization_id":organization_id, "asset_id":asset_id, "size_bytes":size, "sha256":hasher.hexdigest(), "retention_action":"non_destructive_only"}
