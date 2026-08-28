"""Organization-scoped game-plan review workspace."""

from __future__ import annotations

from typing import Any

from .tenant_repository import TenantRepository


def _records(repository: TenantRepository, collection: str) -> list[dict[str, Any]]:
    return repository.list(collection)


def build_game_plan_workspace(*, repository: TenantRepository, week: str | None = None) -> dict[str, Any]:
    plans = _records(repository, "game_plans")
    if week:
        plans = [plan for plan in plans if plan.get("week") == week or plan.get("week_context") == week]
    scouting = _records(repository, "scouting_reports")
    metrics = _records(repository, "metric_observations")
    rules = _records(repository, "rule_recommendations")
    deliveries = _records(repository, "weekly_delivery_packages")
    releases = _records(repository, "release_candidates")
    pending = [record for record in [*plans, *rules, *deliveries, *releases] if record.get("status") in {"under_review", "blocked", "pending_approval"}]
    blockers = [blocker for record in [*deliveries, *releases] for blocker in record.get("blockers", [])]
    return {
        "organization_id": repository.organization_id,
        "status": "ready" if plans else "empty",
        "week": week,
        "plans": plans,
        "scouting_reports": scouting,
        "metric_observations": metrics,
        "rule_recommendations": rules,
        "weekly_deliveries": deliveries,
        "release_candidates": releases,
        "pending_review_count": len(pending),
        "blockers": blockers,
        "evidence_summary": {"scouting_reports":len(scouting), "metric_observations":len(metrics), "rule_recommendations":len(rules)},
        "human_approval_required": bool(pending or blockers),
    }
