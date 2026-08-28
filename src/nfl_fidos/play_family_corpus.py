"""Validation for the cross-unit play-family compiler corpus."""

from __future__ import annotations

from typing import Any

from .play_compiler import compile_play


REQUIRED_UNITS = {"offense", "defense", "special_teams"}


def validate_play_family_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    plays = corpus.get("plays", [])
    seen: set[str] = set()
    units: set[str] = set()
    families: set[str] = set()
    for index, play in enumerate(plays):
        prefix = f"plays[{index}]"
        play_id = play.get("id")
        if play_id in seen:
            errors.append(f"{prefix}: duplicate id {play_id}")
        seen.add(play_id)
        unit = play.get("unit")
        units.add(unit)
        if unit not in REQUIRED_UNITS:
            errors.append(f"{prefix}: unsupported unit")
        family_id = play.get("play_family_id")
        if not isinstance(family_id, str) or not family_id.startswith("PLAY-FAM-"):
            errors.append(f"{prefix}: play_family_id must start with PLAY-FAM-")
        families.add(family_id)
        if not isinstance(play.get("red_team_checks"), list) or not play.get("red_team_checks"):
            errors.append(f"{prefix}: red_team_checks are required")
        result = compile_play(play)
        errors.extend(f"{prefix}: {issue.code}: {issue.message}" for issue in result.issues)
    errors.extend(f"missing required unit: {unit}" for unit in sorted(REQUIRED_UNITS - units))
    if not corpus.get("corpus_id") or not corpus.get("version") or not corpus.get("purpose"):
        errors.append("corpus identity and purpose are required")
    if corpus.get("status") != "validation_fixture":
        errors.append("corpus status must remain validation_fixture")
    return {"corpus_id": corpus.get("corpus_id"), "status": "valid" if not errors else "invalid", "errors": errors, "play_count": len(plays), "family_count": len(families), "units": sorted(units)}
