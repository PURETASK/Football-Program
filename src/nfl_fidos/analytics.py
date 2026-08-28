"""Contextual football metrics with denominator and provenance preservation."""

from __future__ import annotations

from typing import Any


def build_metric_observation(
    *,
    observation_id: str,
    metric_id: str,
    numerator: float,
    denominator: float,
    team: str,
    season: str,
    situations: list[str],
    source: dict[str, str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not observation_id.startswith("METRIC-"):
        issues.append({"code": "METRIC-ID", "message": "Observation id must start with METRIC-", "path": "observation_id"})
    if not metric_id.startswith("METRIC-DEF-"):
        issues.append({"code": "METRIC-DEFINITION", "message": "Metric must reference a definition id", "path": "metric_id"})
    if numerator < 0 or denominator <= 0 or numerator > denominator:
        issues.append({"code": "METRIC-BOUNDS", "message": "Numerator must be within a positive denominator", "path": "numerator"})
    if not team or not season or not situations:
        issues.append({"code": "METRIC-CONTEXT", "message": "Team, season, and situations are required", "path": "context"})
    if not source.get("kind") or not source.get("ref"):
        issues.append({"code": "METRIC-PROVENANCE", "message": "Metric source kind and ref are required", "path": "source"})
    sample_confidence = "low" if denominator < 10 else "moderate" if denominator < 30 else "high"
    return {
        "id": observation_id,
        "metric_id": metric_id,
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
        "context": {"team": team, "season": season, "situations": situations},
        "source": source,
        "confidence": sample_confidence,
        "generalization_allowed": denominator >= 10,
        "status": "invalid" if issues else "valid",
        "issues": issues,
    }
