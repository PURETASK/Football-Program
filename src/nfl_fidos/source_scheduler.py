"""Scheduler-ready source freshness planning and persisted batch execution."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .source_connectors import SourceConnectorService
from .tenant_repository import TenantRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SourceRefreshScheduler:
    def __init__(self, repository: TenantRepository, *, connector: SourceConnectorService | None = None):
        self.repository = repository
        self.connector = connector or SourceConnectorService(repository)

    def plan_due(self, *, now: datetime | None = None, max_sources: int = 100) -> dict[str, Any]:
        if max_sources <= 0:
            raise ValueError("max_sources must be positive")
        reference = now or _now()
        due: list[dict[str, Any]] = []
        future: list[dict[str, Any]] = []
        for source in self.connector.list_sources():
            if source.get("status") not in {"registered", "current"}:
                continue
            last = source.get("last_refresh")
            if not last:
                due_at = reference
            else:
                try:
                    refreshed = datetime.fromisoformat(last)
                    due_at = refreshed + timedelta(days=source.get("freshness_days", 1))
                except (TypeError, ValueError):
                    due_at = reference
            item = {"source_id":source.get("id"), "uri":source.get("uri"), "due_at":due_at.isoformat(), "stale":due_at <= reference}
            (due if item["stale"] else future).append(item)
        due.sort(key=lambda item: (item["due_at"], item["source_id"] or ""))
        return {"id":f"SOURCE-SCHEDULE-{reference.strftime('%Y%m%d%H%M%S%f')}", "organization_id":self.repository.organization_id, "as_of":reference.isoformat(), "max_sources":max_sources, "due_count":len(due), "selected":due[:max_sources], "deferred":due[max_sources:] + future, "status":"due" if due else "current", "destructive_action_required":False}

    def run_due(self, *, actor: str, now: datetime | None = None, max_sources: int = 100) -> dict[str, Any]:
        plan = self.plan_due(now=now, max_sources=max_sources)
        if not plan["selected"]:
            report = {**plan, "status":"current", "results":[], "refreshed_count":0, "failed_count":0, "human_review_required":False}
        else:
            batch = self.connector.refresh_all(actor=actor, stale_only=True, max_sources=max_sources)
            report = {**plan, **batch, "schedule_id":plan["id"]}
        self.repository.put("source_refresh_batches", report["id"], report, actor=actor, reason="source_refresh_batch_persisted")
        return report
