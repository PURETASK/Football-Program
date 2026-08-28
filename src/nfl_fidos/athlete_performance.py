"""Structured athlete-performance observations without medical inference."""

from __future__ import annotations

from typing import Any


BOUNDARIES = [
    "This is performance support, not a medical assessment.",
    "A performance signal does not establish injury, illness, or treatment need.",
    "Qualified performance and medical staff own health-related decisions.",
]


def build_performance_observation(
    *,
    observation_id: str,
    athlete_id: str,
    session_type: str,
    duration_minutes: int,
    repetitions: int,
    quality_score: float,
    season_phase: str,
    position: str,
    source: dict[str, str],
    health_signal: bool = False,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not observation_id.startswith("PERF-OBS-"):
        issues.append({"code": "PERF-OBS-ID", "message": "Observation id must start with PERF-OBS-", "path": "observation_id"})
    if not athlete_id or not session_type or duration_minutes <= 0 or repetitions <= 0:
        issues.append({"code": "PERF-OBS-WORKLOAD", "message": "Athlete, session, duration, and repetitions are required and positive", "path": "workload"})
    if quality_score < 0 or quality_score > 1:
        issues.append({"code": "PERF-OBS-QUALITY", "message": "Quality score must be between 0 and 1", "path": "quality_score"})
    if not season_phase or not position or not source.get("kind") or not source.get("ref"):
        issues.append({"code": "PERF-OBS-CONTEXT", "message": "Season phase, position, and source are required", "path": "context"})
    return {
        "id": observation_id, "athlete_id": athlete_id, "session_type": session_type,
        "workload": {"duration_minutes": duration_minutes, "repetitions": repetitions},
        "quality_score": quality_score, "context": {"season_phase": season_phase, "position": position},
        "source": source, "health_signal": health_signal,
        "status": "rejected" if issues else "valid", "issues": issues,
    }


def build_readiness_summary(*, summary_id: str, athlete_id: str, observations: list[dict[str, Any]], signals: list[str]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    valid = [item for item in observations if item.get("status") == "valid" and item.get("athlete_id") == athlete_id]
    if not summary_id.startswith("READINESS-"):
        issues.append({"code": "READINESS-ID", "message": "Readiness id must start with READINESS-", "path": "summary_id"})
    if not athlete_id or not valid:
        issues.append({"code": "READINESS-OBSERVATIONS", "message": "At least one valid athlete observation is required", "path": "observations"})
    health_signal = any(item.get("health_signal") for item in valid)
    if health_signal:
        signals = [*signals, "health-related signal requires qualified staff review"]
    confidence = "low" if len(valid) < 3 else "moderate" if len(valid) < 7 else "high"
    return {
        "id": summary_id, "athlete_id": athlete_id, "observation_ids": [item["id"] for item in valid],
        "signals": signals, "confidence": confidence,
        "staff_review_required": bool(issues or health_signal or confidence != "high"),
        "boundaries": BOUNDARIES, "status": "requires_staff_review" if (issues or health_signal or confidence != "high") else "draft",
        "issues": issues,
    }
