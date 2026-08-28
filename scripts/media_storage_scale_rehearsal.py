"""Run a bounded temporary managed-media storage and retention rehearsal."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nfl_fidos.media_retention import plan_media_retention
from nfl_fidos.media_storage import copy_authorized_media
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


def run_rehearsal(*, assets_per_tenant: int = 4) -> dict[str, Any]:
    if assets_per_tenant <= 0 or assets_per_tenant > 1000:
        raise ValueError("assets_per_tenant must be between 1 and 1000")
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-media-storage-") as directory:
        root = Path(directory)
        source_root = root / "approved-source"
        storage_root = root / "managed-storage"
        source_root.mkdir()
        source_files: list[tuple[str, Path, str]] = []
        for tenant_index, organization_id in enumerate(("ORG-MEDIA-SCALE-A", "ORG-MEDIA-SCALE-B")):
            for item in range(assets_per_tenant):
                asset_id = f"FILM-MEDIA-SCALE-{tenant_index}-{item:04d}"
                payload = f"synthetic-media-{organization_id}-{item}".encode("utf-8")
                source = source_root / f"{asset_id}.mp4"
                source.write_bytes(payload)
                source_files.append((organization_id, source, asset_id))
        stored: list[dict[str, Any]] = []
        for organization_id, source, asset_id in source_files:
            stored.append(copy_authorized_media(source_path=source, storage_root=storage_root, organization_id=organization_id, asset_id=asset_id, allowed_source_roots=[source_root]))
        duplicate = copy_authorized_media(source_path=source_files[0][1], storage_root=storage_root, organization_id=source_files[0][0], asset_id=source_files[0][2], allowed_source_roots=[source_root])
        outside = copy_authorized_media(source_path=source_files[0][1], storage_root=storage_root, organization_id="ORG-MEDIA-SCALE-C", asset_id="FILM-MEDIA-SCALE-C-0000", allowed_source_roots=[root / "not-approved"])
        repository = JsonRepository(root / "state.json")
        tenant_reports: list[dict[str, Any]] = []
        for organization_id, source, asset_id in source_files:
            result = next(item for item in stored if item.get("asset_id") == asset_id)
            TenantRepository(repository, organization_id=organization_id, actor="MEDIA-REHEARSAL").put("film_assets", asset_id, {"id":asset_id,"organization_id":organization_id,"captured_at":"2026-08-01T00:00:00+00:00","sha256":result.get("sha256"),"managed_storage":{"destination_path":result.get("destination_path")}}, actor="MEDIA-REHEARSAL", reason="media_storage_rehearsal")
        for organization_id in ("ORG-MEDIA-SCALE-A", "ORG-MEDIA-SCALE-B"):
            tenant_reports.append(plan_media_retention(repository=TenantRepository(repository, organization_id=organization_id, actor="MEDIA-REHEARSAL"), retention_days=365, now=datetime(2026, 8, 23, tzinfo=timezone.utc)))
        expected_hash = hashlib.sha256(source_files[0][1].read_bytes()).hexdigest()
        checks = {"all_assets_stored": len(stored) == assets_per_tenant * 2 and all(item.get("status") == "stored" for item in stored), "digest_integrity": stored[0].get("sha256") == expected_hash and all(len(item.get("sha256", "")) == 64 for item in stored), "tenant_path_isolation": all(organization_id in item.get("destination_path", "") for organization_id, _, asset_id in source_files for item in stored if item.get("asset_id") == asset_id), "duplicate_rejected": duplicate.get("status") == "rejected", "source_boundary_rejected": outside.get("status") == "rejected", "retention_non_destructive": all(report.get("delete_performed") is False for report in tenant_reports)}
        return {"status":"passed" if all(checks.values()) else "failed","temporary_workspace":True,"assets_per_tenant":assets_per_tenant,"total_assets":len(stored),"checks":checks,"retention_reports":tenant_reports,"external_state_changed":False,"production_implementation_allowed":False}


def main() -> int:
    result = run_rehearsal()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
