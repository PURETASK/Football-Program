"""Analyst-facing metric lineage and report workspace."""

from __future__ import annotations

from typing import Any

from .analytics_dictionary import build_analytics_report
from .tenant_repository import TenantRepository


class AnalyticsWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_report(self, *, report_id: str, audience: str, metric_observations: list[dict[str, Any]], context: dict[str, Any], caveats: list[str], analyst: str, actor: str) -> dict[str, Any]:
        scoped = []
        for observation in metric_observations:
            record = dict(observation)
            record["organization_id"] = self.repository.organization_id
            scoped.append(record)
        report = build_analytics_report(report_id=report_id, audience=audience, metric_observations=scoped, context=context, caveats=caveats, analyst=analyst)
        report["organization_id"] = self.repository.organization_id
        if report["status"] == "draft":
            for observation in scoped:
                self.repository.put("metric_observations", observation["id"], observation, actor=actor, reason="analytics_observation_saved")
            return self.repository.put("analytics_reports", report_id, report, actor=actor, reason="analytics_report_created")
        return report

    def workspace(self, *, situation: str | None = None) -> dict[str, Any]:
        observations = self.repository.list("metric_observations")
        reports = self.repository.list("analytics_reports")
        if situation:
            observations = [item for item in observations if item.get("context", {}).get("situation") == situation]
            reports = [item for item in reports if item.get("context", {}).get("situation") == situation]
        lineage = sum(1 for item in observations if item.get("observation_ids") or item.get("source"))
        uncertain = sum(1 for item in observations if item.get("uncertainty"))
        return {"organization_id":self.repository.organization_id, "status":"ready" if observations or reports else "empty", "situation":situation, "observations":observations, "reports":reports, "lineage_complete_count":lineage, "uncertainty_count":uncertain, "review_count":sum(1 for report in reports if report.get("status") in {"draft", "under_review"}), "human_review_required":bool(reports)}
