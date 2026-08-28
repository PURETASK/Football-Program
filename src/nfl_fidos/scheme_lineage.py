"""Validation for source-linked scheme-family lineage fixtures."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = ("id", "family_id", "unit", "team_id", "source_ref", "evidence_type", "lineage_level", "confidence", "review_status")


def validate_scheme_lineage_corpus(corpus: dict[str, Any], scheme_bible: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    families = {family.get("id"): family for family in scheme_bible.get("families", [])}
    records = corpus.get("records", [])
    seen: set[str] = set()
    covered: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        for field in REQUIRED_FIELDS:
            if not record.get(field):
                errors.append(f"{prefix}: missing {field}")
        record_id = record.get("id")
        if record_id in seen:
            errors.append(f"{prefix}: duplicate id {record_id}")
        seen.add(record_id)
        family_id = record.get("family_id")
        family = families.get(family_id)
        if not family:
            errors.append(f"{prefix}: unknown family_id {family_id}")
        else:
            covered.add(family_id)
            if record.get("unit") != family.get("unit"):
                errors.append(f"{prefix}: unit does not match scheme family")
        if record.get("team_id") and not str(record["team_id"]).startswith("TEAM-"):
            errors.append(f"{prefix}: team_id must start with TEAM-")
        if record.get("source_ref") and not str(record["source_ref"]).startswith("VALIDATION-"):
            errors.append(f"{prefix}: fixture source_ref must be explicitly labeled VALIDATION-")
        if record.get("review_status") != "review_required":
            errors.append(f"{prefix}: lineage fixtures must remain review_required")
    missing = sorted(set(families) - covered)
    errors.extend(f"missing lineage fixture for family: {family_id}" for family_id in missing)
    if not corpus.get("corpus_id") or not corpus.get("version") or not corpus.get("purpose"):
        errors.append("corpus identity and purpose are required")
    if corpus.get("status") != "validation_fixture":
        errors.append("corpus status must remain validation_fixture")
    return {"corpus_id": corpus.get("corpus_id"), "status": "valid" if not errors else "invalid", "errors": errors, "record_count": len(records), "family_count": len(covered), "unit_counts": {"offense": sum(1 for record in records if record.get("unit") == "offense"), "defense": sum(1 for record in records if record.get("unit") == "defense")}}
