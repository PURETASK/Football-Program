"""Explainable, profile-driven legality linting for play-design artifacts.

This is a coach-facing authoring linter, not an officiating decision.  Each
finding carries its profile, source basis, observed value, and whether a
program-owner-approved override may be attached.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


RULE_PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "nfl": {"label": "NFL tackle football", "players_on_field": 11, "minimum_line_players": 7, "max_motion_at_snap": 1, "allow_blocking": True, "min_rush_distance_yards": None, "no_contact": False, "qb_direct_run_allowed": True, "number_based_eligibility": True, "source": {"title": "NFL Football Operations Rulebook hub", "uri": "https://operations.nfl.com/the-rules/nfl-rulebook", "rule_refs": ["Rule 5-1-1", "Rule 7-4-7", "Rule 7-4-8", "Rule 7-5-1", "Rule 8-1-5", "Rule 8-1-6"]}},
    "ncaa": {"label": "NCAA college football", "players_on_field": 11, "minimum_line_players": 7, "max_motion_at_snap": 1, "allow_blocking": True, "min_rush_distance_yards": None, "no_contact": False, "qb_direct_run_allowed": True, "number_based_eligibility": True, "source": {"title": "2025 NCAA Football Rules and Interpretations", "uri": "https://ncaaorg.s3.amazonaws.com/championships/sports/football/rules/PRMFB_RulesBook.pdf", "rule_refs": ["Rule 7-1", "Rule 7-1-5", "Rule 7-3", "Rule 7-3-3"]}},
    "high_school": {"label": "NFHS high-school tackle football", "players_on_field": 11, "minimum_line_players": 7, "max_motion_at_snap": 1, "allow_blocking": True, "min_rush_distance_yards": None, "no_contact": False, "qb_direct_run_allowed": True, "number_based_eligibility": False, "requires_local_rules": True, "source": {"title": "NFHS Football Rules and Rules Changes", "uri": "https://www.nfhs.org/sports/football/rules", "rule_refs": ["NFHS current rulebook and state adoption"]}},
    "youth": {"label": "Youth tackle football - local rules required", "players_on_field": None, "minimum_line_players": None, "max_motion_at_snap": None, "allow_blocking": None, "min_rush_distance_yards": None, "no_contact": False, "qb_direct_run_allowed": None, "number_based_eligibility": False, "requires_local_rules": True, "source": {"title": "Organization-defined youth rules profile", "uri": None, "rule_refs": ["Local league rulebook required"]}},
    "flag": {"label": "NFL FLAG 5-on-5 baseline", "players_on_field": 5, "minimum_line_players": 0, "max_motion_at_snap": 1, "allow_blocking": False, "min_rush_distance_yards": 7, "no_contact": True, "qb_direct_run_allowed": False, "number_based_eligibility": False, "requires_local_rules": True, "source": {"title": "NFL FLAG Football Rules", "uri": "https://nflflag.com/coaches/flag-football-rules", "rule_refs": ["Illegal motion", "Illegal rush", "No contact", "Forward-pass and quarterback restrictions"]}},
}


def profile_metadata(profile: str) -> dict[str, Any]:
    if profile not in RULE_PROFILE_CATALOG:
        raise KeyError(f"Unknown rule profile: {profile}")
    return {"id": profile, **RULE_PROFILE_CATALOG[profile]}


def validate_rule_profile_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Check the declarative profile file against executable legality policy."""
    contract_path = Path(path) if path else Path(__file__).resolve().parents[2] / "rules" / "play-design-rule-profiles.json"
    issues: list[str] = []
    try:
        document = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "invalid", "path": str(contract_path), "issues": [f"profile catalog unreadable: {exc}"]}
    declared = {str(item.get("id")): item for item in document.get("profiles", []) if isinstance(item, dict) and item.get("id")}
    expected_ids = set(RULE_PROFILE_CATALOG)
    if set(declared) != expected_ids:
        issues.append(f"profile ids differ: declared={sorted(declared)} executable={sorted(expected_ids)}")
    mappings = {
        "players_on_field": "players_on_field",
        "minimum_line_players": "minimum_line_players",
        "max_motion_at_snap": "max_motion_at_snap",
        "blocking_allowed": "allow_blocking",
        "minimum_rush_distance_yards": "min_rush_distance_yards",
        "number_based_eligibility": "number_based_eligibility",
    }
    for profile_id in sorted(expected_ids & set(declared)):
        executable = RULE_PROFILE_CATALOG[profile_id]
        source = declared[profile_id]
        for declared_key, executable_key in mappings.items():
            if source.get(declared_key) != executable.get(executable_key):
                issues.append(f"{profile_id}.{declared_key} differs from executable {executable_key}")
        declared_local = bool(source.get("local_adoption_required") or source.get("local_variants_required"))
        if declared_local != bool(executable.get("requires_local_rules")):
            issues.append(f"{profile_id} local-rule requirement differs")
        if not source.get("source"):
            issues.append(f"{profile_id} is missing a source")
    return {"status": "valid" if not issues else "invalid", "path": str(contract_path), "profile_count": len(declared), "issues": issues}


def _finding(code: str, message: str, path: str, *, profile: str, source: dict[str, Any], severity: str = "warning", observed: Any = None, expected: Any = None, overrideable: bool = True) -> dict[str, Any]:
    return {"code": code, "message": message, "path": path, "severity": severity, "rule_profile": profile, "rule_basis": source.get("rule_refs", []), "source": source, "observed": observed, "expected": expected, "overrideable": overrideable, "explanation": f"Observed {observed!r}; expected {expected!r} under the {profile} profile." if expected is not None else message}


def _point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        return float(value.get("x")), float(value.get("y"))
    except (TypeError, ValueError):
        return None


def _number(value: Any, default: float) -> float:
    """Convert timeline/rule inputs without allowing malformed authoring data to crash linting."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return min(a[0], c[0]) - 1e-6 <= b[0] <= max(a[0], c[0]) + 1e-6 and min(a[1], c[1]) - 1e-6 <= b[1] <= max(a[1], c[1]) + 1e-6


def _segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    first = _orientation(a, b, c)
    second = _orientation(a, b, d)
    third = _orientation(c, d, a)
    fourth = _orientation(c, d, b)
    if ((first > 0 and second < 0) or (first < 0 and second > 0)) and ((third > 0 and fourth < 0) or (third < 0 and fourth > 0)):
        return True
    return (abs(first) < 1e-6 and _on_segment(a, c, b)) or (abs(second) < 1e-6 and _on_segment(a, d, b)) or (abs(third) < 1e-6 and _on_segment(c, a, d)) or (abs(fourth) < 1e-6 and _on_segment(c, b, d))


def _path_intersects(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> bool:
    first_points = [_point(item) for item in first]
    second_points = [_point(item) for item in second]
    if any(item is None for item in first_points + second_points):
        return False
    for first_index in range(1, len(first_points)):
        for second_index in range(1, len(second_points)):
            if _segments_intersect(first_points[first_index - 1], first_points[first_index], second_points[second_index - 1], second_points[second_index]):
                return True
    return False


def _segment_intersection_point(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> tuple[float, float] | None:
    """Return a deterministic intersection point for two intersecting segments."""
    denominator = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(denominator) < 1e-9:
        # Collinear/overlapping corridors have no unique crossing point. Use
        # the midpoint of the overlapping bounding box as a stable marker.
        x_min = max(min(a[0], b[0]), min(c[0], d[0]))
        x_max = min(max(a[0], b[0]), max(c[0], d[0]))
        y_min = max(min(a[1], b[1]), min(c[1], d[1]))
        y_max = min(max(a[1], b[1]), max(c[1], d[1]))
        if x_min <= x_max and y_min <= y_max:
            return ((x_min + x_max) / 2, (y_min + y_max) / 2)
        return None
    first_factor = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / denominator
    return (a[0] + first_factor * (b[0] - a[0]), a[1] + first_factor * (b[1] - a[1]))


def _path_collision_corridors(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe every geometric crossing for coach-facing diagnostics."""
    first_points = [_point(item) for item in first]
    second_points = [_point(item) for item in second]
    if any(item is None for item in first_points + second_points):
        return []
    corridors: list[dict[str, Any]] = []
    for first_index in range(1, len(first_points)):
        for second_index in range(1, len(second_points)):
            a, b = first_points[first_index - 1], first_points[first_index]
            c, d = second_points[second_index - 1], second_points[second_index]
            if not _segments_intersect(a, b, c, d):
                continue
            point = _segment_intersection_point(a, b, c, d)
            if point is None:
                continue
            corridors.append({
                "point": {"x": round(point[0], 3), "y": round(point[1], 3)},
                "first_segment": first_index - 1,
                "second_segment": second_index - 1,
            })
    return corridors


def _timing_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_timing = first.get("timing", {}) if isinstance(first.get("timing"), dict) else {}
    second_timing = second.get("timing", {}) if isinstance(second.get("timing"), dict) else {}
    first_start, first_end = _number(first_timing.get("start_ms", first.get("start_ms", 0)), 0), _number(first_timing.get("end_ms", first.get("end_ms", 999999)), 999999)
    second_start, second_end = _number(second_timing.get("start_ms", second.get("start_ms", 0)), 0), _number(second_timing.get("end_ms", second.get("end_ms", 999999)), 999999)
    return max(first_start, second_start) <= min(first_end, second_end)


def _effective_profile_configuration(design: dict[str, Any], profile: str, source: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply validated organization/local constraints to profiles that require adoption rules."""
    configuration = deepcopy(RULE_PROFILE_CATALOG[profile])
    overrides = design.get("local_rule_constraints")
    if overrides is None:
        return configuration
    if not isinstance(overrides, dict):
        issues.append(_finding("LEGALITY-LOCAL-CONSTRAINTS", "Local rule constraints must be an object keyed by supported profile fields.", "local_rule_constraints", profile=profile, source=source, severity="error", observed=type(overrides).__name__, expected="object"))
        return configuration
    allowed = {"players_on_field", "minimum_line_players", "max_motion_at_snap", "allow_blocking", "min_rush_distance_yards", "qb_direct_run_allowed", "number_based_eligibility"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        issues.append(_finding("LEGALITY-LOCAL-CONSTRAINT-FIELD", "Local rule constraints contain unsupported fields.", "local_rule_constraints", profile=profile, source=source, severity="error", observed=unknown, expected=sorted(allowed)))
    for key in sorted(set(overrides) & allowed):
        value = overrides[key]
        if key in {"allow_blocking", "qb_direct_run_allowed", "number_based_eligibility"}:
            if not isinstance(value, bool):
                issues.append(_finding("LEGALITY-LOCAL-CONSTRAINT-TYPE", f"Local constraint {key} must be boolean.", f"local_rule_constraints.{key}", profile=profile, source=source, severity="error", observed=value, expected="boolean"))
                continue
        elif value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            issues.append(_finding("LEGALITY-LOCAL-CONSTRAINT-TYPE", f"Local constraint {key} must be a non-negative integer or null.", f"local_rule_constraints.{key}", profile=profile, source=source, severity="error", observed=value, expected="non-negative integer or null"))
            continue
        configuration[key] = value
    if configuration.get("requires_local_rules") and not design.get("local_rule_source_ref"):
        issues.append(_finding("LEGALITY-LOCAL-RULE-SOURCE", "This profile has local adoption variants; provide the adopting league, state, or organization rulebook reference before final validation.", "local_rule_source_ref", profile=profile, source=source, severity="warning", expected="approved local rule source", observed=None))
    return configuration


def validate_advanced_legality(design: dict[str, Any], *, rule_profile: str | None = None) -> list[dict[str, Any]]:
    profile = rule_profile or design.get("rule_profile", "nfl")
    if profile not in RULE_PROFILE_CATALOG:
        source = {"title": "Unknown profile", "uri": None, "rule_refs": []}
        return [_finding("LEGALITY-PROFILE-UNKNOWN", "Rule profile is not in the controlled profile catalog.", "rule_profile", profile=profile, source=source, severity="error", expected=sorted(RULE_PROFILE_CATALOG), observed=profile, overrideable=False)]
    configuration = RULE_PROFILE_CATALOG[profile]
    source = configuration["source"]
    issues: list[dict[str, Any]] = []
    configuration = _effective_profile_configuration(design, profile, source, issues)
    players = [item for item in design.get("players", []) if isinstance(item, dict)]
    elements = [item for item in design.get("elements", []) if isinstance(item, dict)]
    explicit_field_count = design.get("players_on_field")
    if explicit_field_count is None and profile == "flag":
        issues.append(_finding("LEGALITY-FLAG-FIELD-COUNT-UNDECLARED", "Flag profile needs an explicit players_on_field value before final validation.", "players_on_field", profile=profile, source=source, severity="warning", expected=5, observed=None))
    elif explicit_field_count is not None and configuration["players_on_field"] is not None and explicit_field_count != configuration["players_on_field"]:
        issues.append(_finding("LEGALITY-FIELD-COUNT", "Declared on-field count does not match the selected rule profile.", "players_on_field", profile=profile, source=source, severity="error", expected=configuration["players_on_field"], observed=explicit_field_count, overrideable=False))
    if profile != "flag" and configuration["players_on_field"] is not None and len(players) != configuration["players_on_field"]:
        issues.append(_finding("LEGALITY-PLAYER-COUNT", "Tackle profile requires the configured number of players in the formation.", "players", profile=profile, source=source, severity="error", expected=configuration["players_on_field"], observed=len(players), overrideable=False))
    if profile == "flag" and len(players) != configuration["players_on_field"]:
        issues.append(_finding("LEGALITY-FLAG-PLAYER-COUNT", "The selected flag profile requires the configured number of players in the formation.", "players", profile=profile, source=source, severity="error", expected=configuration["players_on_field"], observed=len(players), overrideable=False))
    alignments = [item.get("alignment", {}) for item in players if isinstance(item.get("alignment"), dict)]
    explicit_line = [item for item in alignments if item.get("on_line") is True]
    if explicit_line and configuration["minimum_line_players"] is not None and len(explicit_line) < configuration["minimum_line_players"]:
        issues.append(_finding("LEGALITY-FORMATION-LINE", "Formation declares too few players on the line of scrimmage.", "players[].alignment.on_line", profile=profile, source=source, severity="error", expected=f">={configuration['minimum_line_players']}", observed=len(explicit_line)))
    if explicit_line:
        line_eligible = [item for item in explicit_line if item.get("eligible") is True]
        if len(line_eligible) < 2 and profile != "flag":
            issues.append(_finding("LEGALITY-FORMATION-ELIGIBILITY", "Explicit tackle formation needs eligible ends represented on the line.", "players[].alignment.eligible", profile=profile, source=source, severity="error", expected=">=2 eligible ends", observed=len(line_eligible)))
        line_players = [player for player in players if isinstance(player.get("alignment"), dict) and player["alignment"].get("on_line") is True]
        if design.get("unit", "offense") == "offense" and len(line_players) >= 2:
            ordered_line = sorted(line_players, key=lambda player: _point(player.get("start")) or (50, 0))
            end_players = [ordered_line[0], ordered_line[-1]]
            if any(item.get("alignment", {}).get("eligible") is not True for item in end_players):
                issues.append(_finding("LEGALITY-FORMATION-END-ELIGIBILITY", "The outermost declared line players must be eligible ends for a legal tackle formation.", "players[].alignment.eligible", profile=profile, source=source, severity="error", observed=[item.get("id") or item.get("position") for item in end_players], expected="both line ends eligible"))
        if configuration.get("number_based_eligibility") and design.get("unit", "offense") == "offense":
            for index, player in enumerate(players):
                alignment = player.get("alignment", {}) if isinstance(player.get("alignment"), dict) else {}
                number = alignment.get("number")
                if alignment.get("eligible") is True and isinstance(number, int) and 50 <= number <= 79 and alignment.get("reported_eligible") is not True:
                    issues.append(_finding("LEGALITY-ELIGIBLE-NUMBER", "A player wearing a number in the ineligible range is marked eligible without an explicit reported-eligible exception.", f"players[{index}].alignment.reported_eligible", profile=profile, source=source, severity="error", observed={"number": number, "eligible": True}, expected="reported_eligible=true or an eligible number"))
        numbers = [item.get("number") for item in alignments if item.get("number") is not None]
        if len(numbers) != len(set(numbers)):
            issues.append(_finding("LEGALITY-NUMBER-CONFLICT", "Two explicitly numbered players share a jersey number in the formation model.", "players[].alignment.number", profile=profile, source=source, severity="error", observed=numbers, expected="unique numbers", overrideable=False))
    declared_alignment = design.get("formation_constraints")
    if isinstance(declared_alignment, dict) and alignments:
        alignment_counts = {
            "on_line_count": sum(1 for item in alignments if item.get("on_line") is True),
            "eligible_count": sum(1 for item in alignments if item.get("eligible") is True),
            "backfield_count": sum(1 for item in alignments if item.get("backfield") is True or item.get("on_line") is False),
        }
        for field, observed in alignment_counts.items():
            expected = declared_alignment.get(field)
            if isinstance(expected, int) and observed != expected:
                issues.append(_finding("LEGALITY-FORMATION-DECLARATION", "Declared formation alignment counts do not match the player alignment model.", f"formation_constraints.{field}", profile=profile, source=source, severity="error", observed=observed, expected=expected, overrideable=False))
    starts: dict[tuple[int, int], list[str]] = {}
    for player in players:
        start = _point(player.get("start"))
        if start is None:
            continue
        key = (round(start[0] * 4), round(start[1] * 4))
        starts.setdefault(key, []).append(str(player.get("id") or player.get("position")))
    for key, ids in starts.items():
        if len(ids) > 1:
            issues.append(_finding("LEGALITY-ALIGNMENT-COLLISION", "Two players occupy the same starting landmark.", "players[].start", profile=profile, source=source, severity="error", observed=ids, expected="one player per landmark"))

    motions = [item for item in elements if item.get("kind") == "motion"]
    snap_motions = [item for item in motions if item.get("at_snap", item.get("active_at_snap", True)) is True]
    if configuration["max_motion_at_snap"] is not None and len(snap_motions) > configuration["max_motion_at_snap"]:
        issues.append(_finding("LEGALITY-MOTION-COUNT", "Too many players are declared in motion at the snap.", "elements[kind=motion]", profile=profile, source=source, severity="error", expected=f"<={configuration['max_motion_at_snap']}", observed=len(snap_motions)))
    for index, motion in enumerate(motions):
        if motion.get("player_id") and not any(player.get("id") == motion.get("player_id") for player in players):
            issues.append(_finding("LEGALITY-MOTION-PLAYER-REF", "Motion references a player who is not present in the formation.", f"elements[{index}].player_id", profile=profile, source=source, severity="error", observed=motion.get("player_id"), expected="player id present in players", overrideable=False))
        if motion.get("snap_direction") in {"toward_los", "forward"}:
            issues.append(_finding("LEGALITY-MOTION-FORWARD", "Motion path is declared moving toward the line at the snap.", f"elements[{index}].snap_direction", profile=profile, source=source, severity="error", observed=motion.get("snap_direction"), expected="lateral or away from line"))
        if motion.get("requires_reset") is True and motion.get("reset_complete") is not True:
            issues.append(_finding("LEGALITY-MOTION-RESET", "Motion requires a completed reset before the snap but reset_complete is false.", f"elements[{index}].reset_complete", profile=profile, source=source, severity="error", observed=motion.get("reset_complete"), expected=True))
        if motion.get("snap_ms") is None:
            issues.append(_finding("LEGALITY-MOTION-SNAP-TIME", "Motion is missing an explicit snap-relative time.", f"elements[{index}].snap_ms", profile=profile, source=source, severity="warning", expected="integer milliseconds", observed=None))
        motion_timing = motion.get("timing", {}) if isinstance(motion.get("timing"), dict) else {}
        motion_start = _number(motion_timing.get("start_ms", motion.get("start_ms", 0)), 0)
        motion_end = _number(motion_timing.get("end_ms", motion.get("end_ms", motion_start)), motion_start)
        if motion_end < motion_start:
            issues.append(_finding("LEGALITY-MOTION-TIMING", "Motion end timing occurs before its start timing.", f"elements[{index}].timing", profile=profile, source=source, severity="error", observed={"start_ms": motion_start, "end_ms": motion_end}, expected="end_ms >= start_ms"))

    if configuration["allow_blocking"] is False:
        for index, element in enumerate(elements):
            if element.get("kind") in {"block", "stunt", "fit"} or element.get("assignment_type") in {"block", "screen", "contact"}:
                issues.append(_finding("LEGALITY-FLAG-CONTACT", "Blocking, stunts, and contact assignments are not legal in the selected flag profile.", f"elements[{index}]", profile=profile, source=source, severity="error", observed=element.get("kind"), expected="non-contact assignment", overrideable=False))
            if element.get("kind") == "rush" and element.get("rush_distance_yards") is not None:
                rush_distance = _number(element.get("rush_distance_yards"), -1)
                if rush_distance < float(configuration["min_rush_distance_yards"]):
                    issues.append(_finding("LEGALITY-FLAG-RUSH-DISTANCE", "Declared flag rusher is inside the minimum rush distance or has a malformed distance value.", f"elements[{index}].rush_distance_yards", profile=profile, source=source, severity="error", observed=element.get("rush_distance_yards"), expected=f">={configuration['min_rush_distance_yards']} yards", overrideable=False))
            if element.get("kind") == "run" and not configuration.get("qb_direct_run_allowed", True) and any(player.get("id") == element.get("player_id") and str(player.get("position", "")).upper() in {"QB", "QUARTERBACK"} for player in players):
                code = "LEGALITY-FLAG-QB-RUN" if profile == "flag" else "LEGALITY-QB-DIRECT-RUN"
                issues.append(_finding(code, "The selected rule profile does not allow the quarterback to be the direct runner in this play model.", f"elements[{index}].player_id", profile=profile, source=source, severity="error", observed=element.get("player_id"), expected="handoff, pitch, or forward pass", overrideable=False))

    for index, first in enumerate(elements):
        for second_index in range(index + 1, len(elements)):
            second = elements[second_index]
            if first.get("player_id") and first.get("player_id") == second.get("player_id") and _timing_overlap(first, second) and first.get("exclusive_assignment") and second.get("exclusive_assignment"):
                issues.append(_finding("LEGALITY-ASSIGNMENT-CONFLICT", "One player has overlapping exclusive assignments.", f"elements[{index}].player_id", profile=profile, source=source, severity="error", observed=[first.get("id"), second.get("id")], expected="non-overlapping exclusive assignments"))
            corridors = _path_collision_corridors(first.get("points", []), second.get("points", [])) if first.get("kind") == second.get("kind") == "route" and _timing_overlap(first, second) else []
            if design.get("route_collision_policy") == "error" and corridors:
                issues.append(_finding("LEGALITY-ROUTE-COLLISION", "Two route paths intersect during overlapping timing windows.", f"elements[{index}].points", profile=profile, source=source, severity="error", observed={"routes": [first.get("id"), second.get("id")], "corridors": corridors}, expected="separated route corridors"))
            elif corridors:
                intentional = first.get("collision_intent") == second.get("collision_intent") == "intentional"
                first_note = str(first.get("collision_note", "")).strip()
                second_note = str(second.get("collision_note", "")).strip()
                if intentional and first_note and second_note:
                    message = "Two route paths intersect during overlapping timing windows; the crossing is marked intentional and documented by both route owners."
                    expected = "documented intentional crossing"
                else:
                    message = "Two route paths intersect during overlapping timing windows; confirm whether the crossing is intentional and document both assignments."
                    expected = "separated route corridors or documented intentional crossing"
                    if intentional:
                        issues.append(_finding("LEGALITY-ROUTE-CROSSING-EXPLANATION", "Both routes are marked intentional, but each route must include a crossing explanation before approval.", f"elements[{index}].collision_note", profile=profile, source=source, severity="warning", observed={"first": bool(first_note), "second": bool(second_note)}, expected="non-empty collision_note on both routes"))
                issues.append(_finding("LEGALITY-ROUTE-COLLISION", message, f"elements[{index}].points", profile=profile, source=source, severity="warning", observed={"routes": [first.get("id"), second.get("id")], "corridors": corridors, "intentional": intentional, "documented": bool(first_note and second_note)}, expected=expected))

    protections = [item for item in elements if item.get("kind") == "block" or item.get("assignment_type") in {"block", "protection", "combo"}]
    protection_keys: dict[str, list[str]] = {}
    for item in protections:
        key = item.get("gap") or item.get("landmark") or item.get("protection_target")
        if key:
            protection_keys.setdefault(str(key), []).append(str(item.get("id") or item.get("player_id")))
    for key, ids in protection_keys.items():
        if len(ids) > 1 and not any(item.get("combo_with") for item in protections if str(item.get("gap") or item.get("landmark") or item.get("protection_target")) == key):
            issues.append(_finding("LEGALITY-PROTECTION-CONFLICT", "Multiple blockers claim the same protection landmark without a declared combination.", "elements[].gap", profile=profile, source=source, severity="error", observed={key: ids}, expected="one owner or explicit combo assignment"))

    coverage = [item for item in elements if item.get("kind") == "coverage"]
    declared_zones = design.get("coverage_zones") if isinstance(design.get("coverage_zones"), list) else []
    assigned_zones = {str(item.get("zone") or item.get("responsibility") or item.get("coverage_zone")) for item in coverage if item.get("zone") or item.get("responsibility") or item.get("coverage_zone")}
    missing_zones = [str(zone) for zone in declared_zones if str(zone) not in assigned_zones]
    if missing_zones:
        issues.append(_finding("LEGALITY-COVERAGE-GAP", "Declared coverage zones have no assignment owner.", "coverage_zones", profile=profile, source=source, severity="error", observed=missing_zones, expected="every declared zone assigned"))
    fits = [item for item in elements if item.get("kind") in {"fit", "coverage"} and (item.get("gap") or item.get("fit_gap"))]
    fit_keys: dict[str, list[str]] = {}
    for item in fits:
        key = str(item.get("gap") or item.get("fit_gap"))
        fit_keys.setdefault(key, []).append(str(item.get("id") or item.get("player_id")))
    for key, ids in fit_keys.items():
        responsibilities = {str(item.get("responsibility")) for item in fits if str(item.get("gap") or item.get("fit_gap")) == key and item.get("responsibility")}
        if len(ids) > 1 and len(responsibilities) > 1:
            issues.append(_finding("LEGALITY-FIT-CONFLICT", "Multiple defensive assignments claim one fit gap with conflicting responsibilities.", "elements[].gap", profile=profile, source=source, severity="error", observed={key: ids}, expected="one coordinated fit responsibility"))

    # Semantic authoring lint keeps the defensive call teachable even when the
    # geometry itself is valid. These are warnings by design: team terminology
    # and exchange conventions vary, while the server still owns hard rule
    # enforcement and owner-approved overrides.
    if design.get("unit") == "defense":
        for index, element in enumerate(elements):
            kind = str(element.get("kind") or "")
            path = f"elements[{index}]"
            if kind == "fit" and (element.get("gap") or element.get("fit_gap")) and not element.get("fit_rule"):
                issues.append(_finding("LEGALITY-FIT-RULE-UNDECLARED", "A defensive fit declares a gap but does not declare its spill, box, force, or cutback rule.", f"{path}.fit_rule", profile=profile, source=source, severity="warning", observed=None, expected="declared fit rule"))
            if kind == "coverage" and not (element.get("zone") or element.get("coverage_zone") or element.get("responsibility")):
                issues.append(_finding("LEGALITY-COVERAGE-RESPONSIBILITY-UNDECLARED", "A coverage assignment has no zone or responsibility for the teaching and coverage audit views.", f"{path}.zone", profile=profile, source=source, severity="warning", observed=None, expected="zone, coverage_zone, or responsibility"))
            if kind in {"rush", "stunt"} and not (element.get("rush_lane") or element.get("gap") or element.get("landmark")):
                issues.append(_finding("LEGALITY-RUSH-LANE-UNDECLARED", "A rush assignment has no declared rush lane, gap, or landmark.", f"{path}.rush_lane", profile=profile, source=source, severity="warning", observed=None, expected="rush lane, gap, or landmark"))
            if kind == "stunt" and not (element.get("exchange_with") or element.get("target_element_id") or element.get("stunt")):
                issues.append(_finding("LEGALITY-STUNT-EXCHANGE-UNDECLARED", "A stunt is drawn without a partner exchange or named stunt family.", f"{path}.exchange_with", profile=profile, source=source, severity="warning", observed=None, expected="exchange_with, target_element_id, or stunt family"))
            if kind == "rotation" and not (element.get("zone") or element.get("rotation") or element.get("responsibility")):
                issues.append(_finding("LEGALITY-ROTATION-TARGET-UNDECLARED", "A rotation assignment has no destination zone or rotation responsibility.", f"{path}.zone", profile=profile, source=source, severity="warning", observed=None, expected="zone, rotation, or responsibility"))
    if design.get("personnel_constraints") and isinstance(design["personnel_constraints"], dict):
        for field, expected in design["personnel_constraints"].items():
            observed = sum(1 for player in players if player.get("position") == field or player.get("role") == field)
            if isinstance(expected, int) and observed != expected:
                issues.append(_finding("LEGALITY-PERSONNEL-CONSTRAINT", "Declared personnel count does not match the formation players.", f"personnel_constraints.{field}", profile=profile, source=source, severity="error", observed=observed, expected=expected))
    return issues
