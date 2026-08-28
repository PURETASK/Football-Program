"""Validation for authoritative, versioned NFL rule sources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]


def validate_rule_source_registry(registry: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    ids: set[str] = set()
    for source in registry.get("sources", []):
        source_id = source.get("id")
        if not source_id or source_id in ids:
            issues.append(f"duplicate or missing source id: {source_id}")
        ids.add(source_id)
        parsed = urlparse(source.get("uri", ""))
        if source.get("authority") != "official_nfl" or source.get("allowed_domain") != "operations.nfl.com":
            issues.append(f"source is not controlled by official NFL authority: {source_id}")
        if parsed.scheme != "https" or parsed.hostname != source.get("allowed_domain"):
            issues.append(f"source URI must be HTTPS on its allowlisted domain: {source_id}")
        if not source.get("version") or not re.fullmatch(r"\d{4}|current", str(source["version"])):
            issues.append(f"source version is invalid: {source_id}")
        if source.get("status") != "current":
            issues.append(f"source is not current: {source_id}")
        for field in ("title", "kind", "retrieved_at", "effective_date"):
            if not source.get(field):
                issues.append(f"source {source_id} lacks {field}")
    if registry.get("jurisdiction") != "NFL":
        issues.append("rule-source registry must be NFL-scoped")
    return {"registry_id": registry.get("registry_id"), "status": "valid" if not issues else "invalid", "errors": issues, "source_count": len(registry.get("sources", [])), "source_ids": sorted(ids)}


def load_authoritative_rule_sources(path: str | Path | None = None) -> dict[str, Any]:
    source_path = Path(path) if path else ROOT / "rules" / "authoritative-source-registry.json"
    with source_path.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    result = validate_rule_source_registry(registry)
    if result["status"] != "valid":
        raise ValueError("authoritative rule-source registry is invalid: " + "; ".join(result["errors"]))
    return {source["id"]: source for source in registry["sources"]}
