"""Stage 16 metric dictionary, calculation, quality, and report contracts."""

from __future__ import annotations

import math
from typing import Any


REQUIRED_FIELDS = ("id", "name", "unit", "definition", "required_data", "formula", "context_dimensions", "caveats", "validation_method", "consumers")


def validate_metric_definition(definition: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in REQUIRED_FIELDS:
        if not definition.get(field):
            issues.append({"code":"METRIC-DEF-REQUIRED", "message":f"Missing metric definition field: {field}", "path":field})
    if definition.get("id") and not str(definition["id"]).startswith("METRIC-DEF-"):
        issues.append({"code":"METRIC-DEF-ID", "message":"Metric definition id must start with METRIC-DEF-", "path":"id"})
    for field in ("required_data", "context_dimensions", "caveats", "consumers"):
        if field in definition and (not isinstance(definition[field], list) or not definition[field]):
            issues.append({"code":"METRIC-DEF-LIST", "message":f"Metric definition list must be non-empty: {field}", "path":field})
    return issues


def validate_metrics_dictionary(dictionary: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    ids: set[str] = set()
    for definition in dictionary.get("metrics", []):
        if definition.get("id") in ids:
            issues.append(f"duplicate metric definition: {definition.get('id')}")
        ids.add(definition.get("id"))
        issues.extend(f"{definition.get('id')}: {issue['message']}" for issue in validate_metric_definition(definition))
    if not dictionary.get("quality_rules"):
        issues.append("quality rules are required")
    return {"dictionary_id":dictionary.get("dictionary_id"), "status":"valid" if not issues else "invalid", "errors":issues, "metric_count":len(dictionary.get("metrics", []))}


def _wilson_interval(successes: float, trials: float, z: float = 1.96) -> tuple[float, float]:
    rate = successes / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    spread = z * math.sqrt((rate * (1 - rate) / trials) + (z * z / (4 * trials * trials))) / denominator
    return max(0.0, center - spread), min(1.0, center + spread)


def calculate_metric(*, definition: dict[str, Any], numerator: int, denominator: int, context: dict[str, Any], source: dict[str, Any], observation_ids: list[str]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    issues.extend(validate_metric_definition(definition))
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        issues.append({"code":"METRIC-CALC-BOUNDS", "message":"Numerator must be between zero and a positive denominator", "path":"numerator"})
    if not context or not source.get("kind") or not source.get("ref") or not observation_ids:
        issues.append({"code":"METRIC-CALC-LINEAGE", "message":"Context, source, and observation IDs are required", "path":"lineage"})
    rate = numerator / denominator if denominator > 0 else None
    interval = _wilson_interval(numerator, denominator) if denominator > 0 else (None, None)
    confidence = "low" if denominator < 10 else "moderate" if denominator < 30 else "high"
    return {"id":f"METRIC-OBS-{definition.get('id','UNKNOWN').removeprefix('METRIC-DEF-')}", "metric_id":definition.get("id"), "numerator":numerator, "denominator":denominator, "rate":rate, "confidence":confidence, "uncertainty":{"method":"wilson_95_percent","interval":interval}, "context":context, "source":source, "observation_ids":observation_ids, "generalization_allowed":denominator >= 10, "status":"invalid" if issues else "valid", "issues":issues}


def build_analytics_report(*, report_id: str, audience: str, metric_observations: list[dict[str, Any]], context: dict[str, Any], caveats: list[str], analyst: str) -> dict[str, Any]:
    issues: list[str] = []
    if not report_id.startswith("ANALYTICS-REPORT-") or not audience or not metric_observations or not context or not caveats or not analyst:
        issues.append("report identity, audience, observations, context, caveats, and analyst are required")
    invalid = [observation.get("id") for observation in metric_observations if observation.get("status") != "valid"]
    if invalid:
        issues.append(f"report contains invalid observations: {invalid}")
    return {"id":report_id, "audience":audience, "metric_observation_ids":[item.get("id") for item in metric_observations], "context":context, "caveats":caveats, "analyst":analyst, "status":"invalid" if issues else "draft", "role_specific_interpretation_required":True, "issues":issues}
