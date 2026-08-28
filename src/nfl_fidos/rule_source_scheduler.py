"""Bounded freshness planning for official NFL rule sources.

This module identifies review work. It never retrieves, changes, or promotes a
rule source; a separate authorized connector and program-owner decision remain
required.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlparse


class RuleSourceScheduler:
    def plan_due(self, *, registry: dict[str, Any], now: datetime | None = None, freshness_days: int = 30, max_sources: int = 10) -> dict[str, Any]:
        if freshness_days <= 0 or max_sources <= 0:
            raise ValueError("freshness_days and max_sources must be positive")
        reference = (now or datetime.now(timezone.utc)).date()
        issues: list[str] = []
        if registry.get("jurisdiction") != "NFL":
            issues.append("registry must be NFL-scoped")
        due: list[dict[str, Any]] = []
        for source in registry.get("sources", []):
            if source.get("authority") != "official_nfl" or source.get("allowed_domain") != "operations.nfl.com":
                issues.append(f"source is outside the official NFL allowlist: {source.get('id')}")
                continue
            parsed = urlparse(source.get("uri", ""))
            if parsed.scheme != "https" or parsed.hostname != "operations.nfl.com":
                issues.append(f"source URI is not an allowlisted HTTPS endpoint: {source.get('id')}")
                continue
            retrieved = self._parse_date(source.get("retrieved_at"))
            age_days = (reference - retrieved).days if retrieved else None
            if age_days is None or age_days >= freshness_days:
                due.append({"source_id":source.get("id"), "uri":source.get("uri"), "version":source.get("version"), "retrieved_at":source.get("retrieved_at"), "age_days":age_days, "reason":"missing retrieval date" if age_days is None else "freshness window exceeded", "candidate_status":"proposed", "human_review_required":True, "promotion_allowed":False})
            if len(due) >= max_sources:
                break
        return {"id":f"RULE-SOURCE-SCHEDULE-{reference.strftime('%Y%m%d')}", "registry_id":registry.get("registry_id"), "jurisdiction":registry.get("jurisdiction"), "as_of":reference.isoformat(), "freshness_days":freshness_days, "max_sources":max_sources, "due_sources":due, "due_count":len(due), "issues":issues, "status":"blocked" if issues else "review_due" if due else "current", "human_review_required":bool(due), "promotion_allowed":False, "fetch_performed":False}

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        try:
            return date.fromisoformat(str(value)[:10]) if value else None
        except ValueError:
            return None
