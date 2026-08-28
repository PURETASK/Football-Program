"""Run a bounded local authorized-media pipeline rehearsal."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.media_service import MediaCatalogService
from nfl_fidos.media_worker import process_media_job
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


def run_smoke() -> dict:
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-media-") as directory:
        root = Path(directory)
        source_root = root / "authorized-source"
        storage_root = root / "managed-storage"
        source_root.mkdir()
        source = source_root / "game.mp4"
        source.write_bytes(b"authorized media fixture")
        repository = JsonRepository(root / "state.json")
        tenant = TenantRepository(repository, organization_id="ORG-MEDIA-SMOKE", actor="ANALYST")
        catalog = MediaCatalogService(tenant)
        asset = catalog.register_asset(file_path=source, asset_id="FILM-SMOKE-001", duration_seconds=12.5, source={"kind":"team_film", "ref":"SOURCE-SMOKE-001"}, captured_at="2026-08-23T00:00:00Z", team_context="self", allowed_roots=[source_root], storage_root=storage_root, actor="ANALYST")
        managed = asset.get("managed_storage", {})
        jobs = MediaProcessingJobService(tenant)
        jobs.create_job(job_id="MEDIA-JOB-SMOKE-001", asset_id="FILM-SMOKE-001", operation="probe", payload={"file_path":managed.get("destination_path", ""), "allowed_roots":[str(storage_root)]}, requested_by="ANALYST")
        completed = process_media_job(repository=tenant, job_id="MEDIA-JOB-SMOKE-001", worker_id="WORKER-SMOKE", allowed_roots=[str(storage_root)], runner=lambda arguments: (0, '{"format":{"duration":"12.5","format_name":"mov,mp4"}}', ""))
        other_tenant = TenantRepository(repository, organization_id="ORG-OTHER", actor="ANALYST")
        return {"status":"passed" if asset.get("status") == "registered" and managed.get("status") == "stored" and completed.get("status") == "completed" and not MediaCatalogService(other_tenant).list_assets() else "failed", "asset_registered":asset.get("status") == "registered", "managed_storage":managed.get("status") == "stored", "worker_completed":completed.get("status") == "completed", "cross_tenant_isolation":not MediaCatalogService(other_tenant).list_assets(), "temporary_workspace":True}


if __name__ == "__main__":
    result = run_smoke()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
