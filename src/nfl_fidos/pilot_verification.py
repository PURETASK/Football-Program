"""Aggregated, human-moderated pilot usability evidence."""

from __future__ import annotations

from statistics import mean, median
from typing import Any


REQUIRED_PILOT_ROLES = {"program_owner", "coach_staff", "analyst", "player"}


def summarize_pilot_feedback(*, organization_id: str, feedback: list[dict[str, Any]]) -> dict[str, Any]:
    scoped = [item for item in feedback if item.get("organization_id") == organization_id]
    roles = {item.get("user_role") for item in scoped if item.get("user_role")}
    outcomes = {outcome: sum(1 for item in scoped if item.get("outcome") == outcome) for outcome in ("completed", "partially_completed", "blocked")}
    durations = [float(item["duration_seconds"]) for item in scoped if isinstance(item.get("duration_seconds"), (int, float)) and float(item["duration_seconds"]) >= 0]
    satisfaction = [float(item["satisfaction_score"]) for item in scoped if isinstance(item.get("satisfaction_score"), (int, float))]
    accessibility_count = sum(1 for item in scoped if item.get("accessibility_issue") is True)
    severity_counts = {severity: sum(1 for item in scoped if item.get("severity") == severity) for severity in ("note", "minor", "major", "critical")}
    missing_roles = sorted(REQUIRED_PILOT_ROLES - roles)
    return {
        "organization_id": organization_id,
        "feedback_count": len(scoped),
        "session_count": len({item.get("session_id") for item in scoped if item.get("session_id")}),
        "task_count": len({item.get("task_id") for item in scoped if item.get("task_id")}),
        "roles_observed": sorted(roles),
        "missing_pilot_roles": missing_roles,
        "outcomes": outcomes,
        "completion_rate": round(outcomes["completed"] / len(scoped), 3) if scoped else 0.0,
        "duration_seconds": {"sample_count": len(durations), "mean": round(mean(durations), 3) if durations else None, "median": round(median(durations), 3) if durations else None},
        "satisfaction": {"sample_count": len(satisfaction), "mean": round(mean(satisfaction), 3) if satisfaction else None},
        "accessibility_issue_count": accessibility_count,
        "severity_counts": severity_counts,
        "moderation_required": True,
        "pilot_validation_complete": False,
        "status": "ready_for_moderator_review" if scoped and not missing_roles else "blocked",
        "blockers": (["feedback is required"] if not scoped else []) + ([f"pilot role coverage is incomplete: {missing_roles}"] if missing_roles else []),
        "production_implementation_allowed": False,
        "external_state_changed": False,
    }
