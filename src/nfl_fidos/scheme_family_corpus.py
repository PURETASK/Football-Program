"""Validation for the representative offensive and defensive scheme corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "unit", "name", "identity", "components", "personnel_fit", "strengths", "weaknesses", "counters", "counter_counters", "adaptation_logic", "installation_requirements", "nuance")


def validate_scheme_family_corpus(bible: dict[str, Any], *, minimum_per_unit: int = 4) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    families = bible.get("families", [])
    seen: set[str] = set()
    counts = {"offense":0, "defense":0}
    for index, family in enumerate(families):
        family_id = family.get("id", f"index-{index}")
        if family_id in seen:
            errors.append({"code":"SCHEME-FAMILY-DUPLICATE", "message":f"Duplicate family id: {family_id}", "path":f"families[{index}].id"})
        seen.add(family_id)
        unit = family.get("unit")
        if unit not in counts:
            errors.append({"code":"SCHEME-FAMILY-UNIT", "message":f"Unsupported unit: {unit}", "path":f"families[{index}].unit"})
            continue
        counts[unit] += 1
        for field in REQUIRED_FIELDS:
            if not family.get(field):
                errors.append({"code":"SCHEME-FAMILY-FIELD", "message":f"Missing {field}", "path":f"families[{index}].{field}"})
        if len(family.get("counters", [])) < 2 or len(family.get("counter_counters", [])) < 2:
            errors.append({"code":"SCHEME-FAMILY-COUNTERS", "message":"Each family requires multiple counters and counter-counters", "path":f"families[{index}]"})
    for unit, count in counts.items():
        if count < minimum_per_unit:
            errors.append({"code":"SCHEME-FAMILY-COVERAGE", "message":f"{unit} requires at least {minimum_per_unit} families", "path":"families"})
    return {"status":"valid" if not errors else "invalid", "errors":errors, "family_count":len(families), "unit_counts":counts, "family_ids":sorted(seen)}


def load_scheme_family_corpus(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else Path(__file__).resolve().parents[2] / "scheme" / "scheme-bible.json"
    return json.loads(source.read_text(encoding="utf-8"))
