"""Explicit, non-destructive media-retention scan execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .media_retention import plan_media_retention
from .tenant_repository import TenantRepository


class MediaRetentionScheduler:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def run_scan(self, *, actor: str, retention_days: int = 365, now: datetime | None = None) -> dict[str, Any]:
        report = plan_media_retention(repository=self.repository, retention_days=retention_days, now=now)
        scan_id = f"MEDIA-RETENTION-SCAN-{(now or datetime.now(timezone.utc)).strftime('%Y%m%d%H%M%S%f')}"
        persisted = {**report, "id":scan_id, "scan_type":"retention_review", "destructive_action_executed":False, "human_approval_required":report["human_approval_required"]}
        self.repository.put("media_retention_runs", scan_id, persisted, actor=actor, reason="media_retention_scan_persisted")
        return persisted
