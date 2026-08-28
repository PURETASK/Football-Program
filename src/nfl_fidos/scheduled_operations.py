"""Safe external-scheduler contract for bounded NFL FIDOS operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .media_retention import plan_media_retention
from .media_jobs import SCHEDULED_MEDIA_OPERATIONS
from .media_retention_scheduler import MediaRetentionScheduler
from .media_transform_orchestrator import MediaTransformOrchestrator
from .source_scheduler import SourceRefreshScheduler
from .tenant_repository import TenantRepository


class ScheduledOperationsService:
    def __init__(self, repository: TenantRepository, *, environment: str = "local", control_root: str | Path | None = None):
        self.repository = repository
        self.environment = environment
        self.control_root = Path(control_root) if control_root else Path(__file__).resolve().parents[2]

    def _production_allowed(self) -> bool:
        try:
            manifest = json.loads((self.control_root / "control" / "manifest.json").read_text(encoding="utf-8"))
            return bool(manifest.get("production_implementation_allowed"))
        except (OSError, ValueError):
            return False

    def plan(self, *, now: datetime | None = None, max_sources: int = 100, max_transforms: int = 10, retention_days: int = 365) -> dict[str, Any]:
        if max_sources <= 0 or max_transforms <= 0 or retention_days <= 0:
            raise ValueError("operation bounds must be positive")
        reference = now or datetime.now(timezone.utc)
        source_plan = SourceRefreshScheduler(self.repository).plan_due(now=reference, max_sources=max_sources)
        retention_plan = plan_media_retention(repository=self.repository, retention_days=retention_days, now=reference)
        queued_transforms = [job for job in self.repository.list("media_processing_jobs") if job.get("status") in {"queued", "retryable"} and job.get("operation") in SCHEDULED_MEDIA_OPERATIONS]
        return {"id":f"SCHEDULED-OPS-{reference.strftime('%Y%m%d%H%M%S%f')}", "organization_id":self.repository.organization_id, "environment":self.environment, "as_of":reference.isoformat(), "source_plan":source_plan, "retention_status":retention_plan["status"], "retention_candidates":len(retention_plan["candidates"]), "retention_unknown":len(retention_plan["unknown"]), "queued_transform_count":len(queued_transforms), "transform_selected_count":min(len(queued_transforms), max_transforms), "max_sources":max_sources, "max_transforms":max_transforms, "retention_days":retention_days, "destructive_action_required":False, "dry_run":True}

    def run(self, *, actor: str, worker_id: str, execute: bool = False, now: datetime | None = None, max_sources: int = 100, max_transforms: int = 10, retention_days: int = 365, allowed_roots: list[str] | None = None) -> dict[str, Any]:
        plan = self.plan(now=now, max_sources=max_sources, max_transforms=max_transforms, retention_days=retention_days)
        if not execute:
            return plan
        if self.environment == "production" and not self._production_allowed():
            return {**plan, "status":"blocked", "blocker":"production implementation is disabled by the Stage 0 control gate", "dry_run":False}
        source = SourceRefreshScheduler(self.repository).run_due(actor=actor, now=now, max_sources=max_sources)
        retention = MediaRetentionScheduler(self.repository).run_scan(actor=actor, retention_days=retention_days, now=now)
        transforms = MediaTransformOrchestrator(self.repository).run_batch(actor=actor, worker_id=worker_id, max_jobs=max_transforms, allowed_roots=allowed_roots or [])
        return {**plan, "status":"completed" if source.get("status") in {"completed", "current"} and transforms.get("status") == "completed" else "partial_failure", "source":source, "retention":retention, "transforms":transforms, "dry_run":False}
