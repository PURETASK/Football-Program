"""Role-aware organization summary for operator workspaces."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .source_connectors import SourceConnectorService
from .tenant_repository import TenantRepository
from .organization_population_readiness import build_organization_population_readiness


ROLE_SECTIONS = {
    "player": ["today", "inbox", "roster", "playbook", "film", "collaboration"],
    "coach_staff": ["today", "inbox", "roster", "playbook", "film", "practice", "scouting", "analytics", "game_plan", "delivery", "collaboration"],
    "analyst": ["today", "inbox", "roster", "film", "scouting", "analytics", "scheme", "delivery", "collaboration"],
    "program_owner": ["today", "inbox", "roster", "playbook", "film", "practice", "scouting", "analytics", "game_plan", "governance", "delivery", "collaboration"],
    "validator": ["today", "inbox", "governance", "collaboration"],
    "performance_staff": ["today", "inbox", "practice", "delivery", "collaboration"],
}


def build_operator_summary(*, repository: TenantRepository, role: str, stage: str, work_package: str, eval_result: dict[str, Any], season: str | None = None) -> dict[str, Any]:
    counts: dict[str, int] = {}
    pending = 0
    for collection in (
        "plays", "play_designs", "film_assets", "film_clips", "film_observations", "film_playlists",
        "film_quiz_attempts", "scouting_reports", "analytics_reports", "metric_observations",
        "knowledge_claims", "game_plans", "practice_plans", "drills", "player_assignments",
        "mastery_records", "release_records", "media_processing_jobs", "knowledge_sources",
        "roster_players", "depth_charts", "personnel_packages",
    ):
        records = repository.list(collection)
        counts[collection] = len(records)
        pending += sum(1 for record in records if record.get("status") in {"draft", "under_review", "needs_review", "blocked", "retryable"})
    counts["audit_events"] = len(repository.history())
    job_counts = Counter(job.get("status") for job in repository.list("media_processing_jobs"))
    stale_sources = sum(1 for source in SourceConnectorService(repository).list_sources() if source.get("stale"))
    population_readiness = None
    if role in {"program_owner", "validator"}:
        if not season:
            organization_records = repository.list("organizations")
            season = next((record.get("season") for record in sorted(organization_records, key=lambda item: item.get("created_at") or item.get("_saved_at") or "", reverse=True) if record.get("season")), "unknown")
        population_readiness = build_organization_population_readiness(tenant=repository, organization_id=repository.organization_id, season=season)
    return {
        "organization_id": repository.organization_id,
        "role": role,
        "allowed_sections": ROLE_SECTIONS.get(role, ["today"]),
        "stage": stage,
        "work_package": work_package,
        "eval": {"status": eval_result.get("status"), "passed": eval_result.get("passed"), "failed": eval_result.get("failed")},
        "record_counts": counts,
        "pending_review_count": pending,
        "media_job_counts": dict(job_counts),
        "stale_source_count": stale_sources,
        "organization_population": population_readiness,
        "approval_boundary": "human approval required for locked or high-impact artifacts",
    }
