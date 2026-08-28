"""Validation for the controlled NFL analytics definition corpus."""

from __future__ import annotations

from typing import Any


REQUIRED_RECORD_FIELDS = (
    "metric_id", "domain", "numerator_definition", "denominator_definition",
    "uncertainty_method", "lineage_fields", "interpretation_guard",
)
REQUIRED_DOMAINS = {"offense", "defense", "special_teams", "player", "play", "drive", "game_plan"}


def validate_analytics_corpus(corpus: dict[str, Any], dictionary: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    records = corpus.get("records", [])
    definitions = {item.get("id") for item in dictionary.get("metrics", [])}
    seen: set[str] = set()
    domains: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        for field in REQUIRED_RECORD_FIELDS:
            if not record.get(field):
                errors.append(f"{prefix}: missing {field}")
        metric_id = record.get("metric_id")
        if metric_id in seen:
            errors.append(f"{prefix}: duplicate metric_id {metric_id}")
        seen.add(metric_id)
        if metric_id not in definitions:
            errors.append(f"{prefix}: metric_id is not present in dictionary: {metric_id}")
        domains.add(record.get("domain"))
        if record.get("uncertainty_method") not in {"wilson_95_percent", "bootstrap_95_percent", "qualitative_review"}:
            errors.append(f"{prefix}: unsupported uncertainty method")
        if not isinstance(record.get("lineage_fields"), list) or len(record["lineage_fields"]) < 2:
            errors.append(f"{prefix}: at least two lineage fields are required")
    missing_domains = sorted(REQUIRED_DOMAINS - domains)
    errors.extend(f"missing required domain: {domain}" for domain in missing_domains)
    if not corpus.get("corpus_id") or not corpus.get("version") or not corpus.get("purpose"):
        errors.append("corpus identity and purpose are required")
    return {
        "corpus_id": corpus.get("corpus_id"),
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "record_count": len(records),
        "domains": sorted(domains),
        "definition_coverage": len(seen & definitions) / len(definitions) if definitions else 0.0,
    }
