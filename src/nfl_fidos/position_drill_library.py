"""Validation and lookup for the position-family NFL drill corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .drill_library import validate_drill


POSITION_FAMILIES = {"QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "ST", "SPEC"}
MINIMUM_DRILLS_PER_POSITION = 2


def validate_position_drill_library(library: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not str(library.get("library_id", "")).startswith("POSITION-DRILL-LIBRARIES-"):
        errors.append({"code":"POSITION-LIBRARY-ID", "message":"library_id must use the controlled prefix", "path":"library_id"})
    dimensions = set(library.get("mastery_dimensions", []))
    required_dimensions = {"technical", "tactical", "cognitive_recognition", "communication_team_integration", "situational_execution"}
    if not required_dimensions.issubset(dimensions):
        errors.append({"code":"POSITION-LIBRARY-DIMENSIONS", "message":"library must cover all required mastery dimensions", "path":"mastery_dimensions"})
    positions = library.get("positions", [])
    by_position = {entry.get("position"): entry for entry in positions if isinstance(entry, dict)}
    missing = sorted(POSITION_FAMILIES - set(by_position))
    if missing:
        errors.append({"code":"POSITION-LIBRARY-COVERAGE", "message":f"Missing position families: {missing}", "path":"positions"})
    duplicate = len(by_position) != len(positions)
    if duplicate:
        errors.append({"code":"POSITION-LIBRARY-DUPLICATE", "message":"Position families must be unique", "path":"positions"})
    drill_count = 0
    for entry in positions:
        position = entry.get("position")
        drills = entry.get("drills", [])
        if not drills:
            errors.append({"code":"POSITION-LIBRARY-EMPTY", "message":f"Position family {position} has no drills", "path":f"positions.{position}.drills"})
        elif len(drills) < MINIMUM_DRILLS_PER_POSITION:
            errors.append({"code":"POSITION-LIBRARY-DEPTH", "message":f"Position family {position} must contain at least {MINIMUM_DRILLS_PER_POSITION} drills", "path":f"positions.{position}.drills"})
        for index, drill in enumerate(drills):
            drill_count += 1
            issues = validate_drill(drill)
            errors.extend({"code":"POSITION-DRILL", "message":issue["message"], "path":f"positions.{position}.drills[{index}].{issue['path']}"} for issue in issues)
            if drill.get("position") != position:
                errors.append({"code":"POSITION-DRILL-LINK", "message":"Drill position must match its library family", "path":f"positions.{position}.drills[{index}].position"})
    return {"library_id":library.get("library_id"), "status":"valid" if not errors else "invalid", "errors":errors, "position_count":len(by_position), "drill_count":drill_count, "positions":sorted(by_position)}


def load_position_drill_library(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else Path(__file__).resolve().parents[2] / "development" / "position-drill-libraries.json"
    return json.loads(source.read_text(encoding="utf-8"))
