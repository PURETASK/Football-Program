"""Validation of source-linked team terminology usage fixtures."""

from __future__ import annotations

from typing import Any

from .ontology import OntologyResolver


REQUIRED_FIELDS = ("id", "team_id", "phrase", "expected_term_id", "source_ref")


def validate_team_usage_corpus(corpus: dict[str, Any], *, resolver: OntologyResolver | None = None) -> dict[str, Any]:
    resolver = resolver or OntologyResolver()
    errors: list[str] = []
    seen: set[str] = set()
    records = corpus.get("records", [])
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        for field in REQUIRED_FIELDS:
            if not record.get(field):
                errors.append(f"{prefix}: missing {field}")
        record_id = record.get("id")
        if record_id in seen:
            errors.append(f"{prefix}: duplicate id {record_id}")
        seen.add(record_id)
        if record.get("team_id") and not str(record["team_id"]).startswith("TEAM-"):
            errors.append(f"{prefix}: team_id must start with TEAM-")
        expected = record.get("expected_term_id")
        if expected not in resolver.terms:
            errors.append(f"{prefix}: expected term is unknown: {expected}")
        if record.get("phrase"):
            result = resolver.resolve(record["phrase"])
            if result.get("status") != "resolved":
                errors.append(f"{prefix}: phrase is {result.get('status')}")
            elif result.get("term_id") != expected:
                errors.append(f"{prefix}: phrase resolves to {result.get('term_id')}, expected {expected}")
    if not corpus.get("corpus_id") or not corpus.get("version") or not corpus.get("purpose"):
        errors.append("corpus identity and purpose are required")
    return {"corpus_id": corpus.get("corpus_id"), "status": "valid" if not errors else "invalid", "errors": errors, "record_count": len(records), "team_count": len({record.get("team_id") for record in records})}
