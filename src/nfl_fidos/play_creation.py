"""Professional play-creation primitives for offensive and defensive diagrams.

The module intentionally separates normalized football vocabulary from a team's
local call language.  A team may alias ``dagger`` or ``Cover 3`` however it
wants, while the stored design remains searchable and renderable.
"""

from __future__ import annotations

from typing import Any

from .play_timeline import MIN_TIMELINE_MS, validate_timeline
from .play_legality import validate_advanced_legality
from .play_assignment_graph import validate_assignment_graph


ROUTE_TYPES = {
    "vertical", "go", "fade", "seam", "post", "corner", "out", "speed_out",
    "dig", "curl", "comeback", "slant", "drag", "over", "whip", "pivot",
    "wheel", "angle", "flat", "swing", "screen", "choice", "return", "stop",
}
MOTION_TYPES = {"jet", "orbit", "fly", "zip", "yo_yo", "return", "short", "shift", "trade", "fast"}
DEFENSE_COVERAGES = {"cover_0", "cover_1", "cover_2", "cover_3", "cover_4", "cover_6", "quarters", "man", "match", "bracket", "prevent"}
ELEMENT_KINDS = {"route", "motion", "run", "block", "read", "coverage", "rush", "fit", "stunt", "rotation", "annotation"}
ARROW_STYLES = {"route", "motion", "run", "block", "read", "coverage", "rush", "fit", "stunt", "rotation", "check"}


def _issue(code: str, message: str, path: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": severity}


def normalize_term(term: str) -> str:
    """Create a stable lookup key without changing the displayed call word."""
    return "_".join(term.strip().lower().replace("/", " ").replace("-", " ").split())


def validate_play_design(design: dict[str, Any]) -> list[dict[str, str]]:
    """Validate a full play-design envelope and return deterministic issues.

    This is a structural and teaching-model validator, not a substitute for a
    league rulebook, an organization's terminology, or coach approval.
    """
    issues: list[dict[str, str]] = []
    for field in ("id", "version", "unit", "personnel", "formation", "players", "elements", "timeline"):
        if field not in design or design[field] in (None, "", []):
            issues.append(_issue("DESIGN-REQUIRED", f"Missing required design field: {field}", field))
    if design.get("unit") not in {"offense", "defense", "special_teams"}:
        issues.append(_issue("DESIGN-UNIT", "Unit must be offense, defense, or special_teams", "unit"))
    if not isinstance(design.get("players"), list):
        issues.append(_issue("DESIGN-PLAYERS", "Players must be a list", "players"))
    else:
        ids: set[str] = set()
        for i, player in enumerate(design["players"]):
            path = f"players[{i}]"
            if not isinstance(player, dict):
                issues.append(_issue("DESIGN-PLAYER-SHAPE", "Player must be an object", path))
                continue
            player_id = player.get("id")
            if not isinstance(player_id, str) or not player_id:
                issues.append(_issue("DESIGN-PLAYER-ID", "Player id is required", f"{path}.id"))
            elif player_id in ids:
                issues.append(_issue("DESIGN-DUPLICATE-PLAYER", f"Duplicate player id: {player_id}", f"{path}.id"))
            else:
                ids.add(player_id)
            if not isinstance(player.get("position"), str) or not player.get("position"):
                issues.append(_issue("DESIGN-PLAYER-POSITION", "Player position is required", f"{path}.position"))
            _validate_point(player.get("start"), f"{path}.start", issues)
        if len(design["players"]) != 11:
            issues.append(_issue("DESIGN-PLAYER-COUNT", "A full-field tackle design must contain 11 players", "players"))

    elements = design.get("elements")
    if not isinstance(elements, list):
        issues.append(_issue("DESIGN-ELEMENTS", "Elements must be a list", "elements"))
    else:
        for i, element in enumerate(elements):
            path = f"elements[{i}]"
            if not isinstance(element, dict):
                issues.append(_issue("DESIGN-ELEMENT-SHAPE", "Element must be an object", path))
                continue
            kind = element.get("kind")
            if kind not in ELEMENT_KINDS:
                issues.append(_issue("DESIGN-ELEMENT-KIND", f"Unsupported element kind: {kind}", f"{path}.kind"))
            if element.get("player_id") and isinstance(design.get("players"), list) and element["player_id"] not in {p.get("id") for p in design["players"] if isinstance(p, dict)}:
                issues.append(_issue("DESIGN-PLAYER-REF", "Element references an unknown player", f"{path}.player_id"))
            if kind in {"route", "motion"}:
                vocabulary = ROUTE_TYPES if kind == "route" else MOTION_TYPES
                term = normalize_term(str(element.get("type", "")))
                if term not in vocabulary:
                    issues.append(_issue("DESIGN-VOCABULARY", f"Unsupported {kind} type: {element.get('type')}", f"{path}.type"))
            if kind == "coverage" and normalize_term(str(element.get("coverage", ""))) not in DEFENSE_COVERAGES:
                issues.append(_issue("DESIGN-COVERAGE", "Coverage must use a normalized coverage key", f"{path}.coverage"))
            if kind in {"route", "motion", "run", "block", "coverage", "rush", "fit", "stunt", "rotation"}:
                points = element.get("points")
                if not isinstance(points, list) or len(points) < 2:
                    issues.append(_issue("DESIGN-PATH", "Movement elements require at least two points", f"{path}.points"))
                else:
                    for j, point in enumerate(points):
                        _validate_point(point, f"{path}.points[{j}]", issues)
                branches = element.get("branches")
                if branches is not None:
                    if not isinstance(branches, list):
                        issues.append(_issue("DESIGN-BRANCHES", "Alternate paths must be a list", f"{path}.branches"))
                    else:
                        for branch_index, branch in enumerate(branches):
                            branch_path = f"{path}.branches[{branch_index}]"
                            if not isinstance(branch, dict):
                                issues.append(_issue("DESIGN-BRANCH-SHAPE", "Alternate path must be an object", branch_path))
                                continue
                            branch_points = branch.get("points")
                            if not isinstance(branch_points, list) or len(branch_points) < 2:
                                issues.append(_issue("DESIGN-BRANCH-PATH", "Alternate paths require at least two points", f"{branch_path}.points"))
                            else:
                                for point_index, point in enumerate(branch_points):
                                    _validate_point(point, f"{branch_path}.points[{point_index}]", issues)
                if element.get("arrow_style") not in ARROW_STYLES:
                    issues.append(_issue("DESIGN-ARROW", "Movement elements require a canonical arrow style", f"{path}.arrow_style"))
    timeline = design.get("timeline")
    if not isinstance(timeline, dict) or not isinstance(timeline.get("snap_ms"), int) or timeline.get("snap_ms") < 0:
        issues.append(_issue("DESIGN-TIMELINE", "Timeline requires a non-negative integer snap_ms", "timeline.snap_ms"))
    if design.get("unit") == "defense":
        if not design.get("front"):
            issues.append(_issue("DEFENSE-FRONT", "Defense designs require a front/alignment package", "front"))
        if not design.get("coverage"):
            issues.append(_issue("DEFENSE-COVERAGE", "Defense designs require a coverage package", "coverage"))
    if design.get("unit") == "offense" and not design.get("concept"):
        issues.append(_issue("OFFENSE-CONCEPT", "Offense designs require a concept name", "concept"))
    issues.extend(validate_timeline(design))
    issues.extend(validate_assignment_graph(design))
    return issues


RULE_PROFILES = {"nfl", "ncaa", "high_school", "youth", "flag"}


def validate_legality(design: dict[str, Any], *, rule_profile: str | None = None) -> list[dict[str, str]]:
    """Run rule-aware lint checks without claiming to replace officiating."""
    issues: list[dict[str, str]] = []
    profile = rule_profile or design.get("rule_profile", "nfl")
    if profile not in RULE_PROFILES:
        issues.append(_issue("LEGALITY-RULE-PROFILE", "Unknown rule profile", "rule_profile"))
    if design.get("unit") == "offense":
        alignments = [player.get("alignment", {}) for player in design.get("players", []) if isinstance(player, dict)]
        explicit_line = [item for item in alignments if isinstance(item, dict) and item.get("on_line") is True]
        if explicit_line and len(explicit_line) < 7:
            issues.append(_issue("LEGALITY-LINE-COUNT", "Offensive alignment declares fewer than seven players on the line", "players", "error"))
        if explicit_line and len(explicit_line) >= 7:
            eligible_ends = [item for item in alignments if isinstance(item, dict) and item.get("on_line") is True and item.get("eligible") is True]
            if len(eligible_ends) < 2:
                issues.append(_issue("LEGALITY-ELIGIBLE-ENDS", "Explicit offensive alignment needs eligible receivers at both ends", "players", "error"))
        for index, element in enumerate(design.get("elements", [])):
            if not isinstance(element, dict) or element.get("kind") != "motion":
                continue
            if element.get("snap_direction") in {"toward_los", "forward"}:
                issues.append(_issue("LEGALITY-MOTION-DIRECTION", "Motion cannot be moving toward the line of scrimmage at the snap", f"elements[{index}].snap_direction", "error"))
            if element.get("requires_reset") is True and element.get("reset_complete") is not True:
                issues.append(_issue("LEGALITY-MOTION-RESET", "Motion element requires a completed reset before the snap", f"elements[{index}].reset_complete", "error"))
            if element.get("snap_ms") is None:
                issues.append(_issue("LEGALITY-MOTION-TIMING", "Motion needs an explicit snap-relative timing value", f"elements[{index}].snap_ms", "warning"))
    if design.get("unit") == "defense":
        kinds = {element.get("kind") for element in design.get("elements", []) if isinstance(element, dict)}
        if "coverage" not in kinds:
            issues.append(_issue("LEGALITY-COVERAGE-LAYER", "Defense package has no explicit coverage responsibility layer", "elements", "warning"))
        if not (kinds & {"rush", "stunt"}):
            issues.append(_issue("LEGALITY-RUSH-LAYER", "Defense package has no explicit rush or stunt layer", "elements", "warning"))
    seen: set[str] = set()
    for index, element in enumerate(design.get("elements", [])):
        if not isinstance(element, dict):
            continue
        element_id = element.get("id")
        if element_id in seen:
            issues.append(_issue("LEGALITY-DUPLICATE-ELEMENT", f"Duplicate element id: {element_id}", f"elements[{index}].id", "error"))
        elif element_id:
            seen.add(element_id)
        start_ms = element.get("start_ms")
        if start_ms is not None and (isinstance(start_ms, bool) or not isinstance(start_ms, int) or start_ms < MIN_TIMELINE_MS):
            issues.append(_issue("LEGALITY-TIMELINE", "Element start_ms must be within the supported 5-second pre-snap window", f"elements[{index}].start_ms", "error"))
    issues.extend(validate_advanced_legality(design, rule_profile=profile))
    return issues


def _validate_point(point: Any, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(point, dict) or not isinstance(point.get("x"), (int, float)) or not isinstance(point.get("y"), (int, float)):
        issues.append(_issue("DESIGN-POINT", "Point requires numeric x and y coordinates", path))
        return
    if not 0 <= point["x"] <= 100 or not 0 <= point["y"] <= 53.33:
        issues.append(_issue("DESIGN-BOUNDS", "Point is outside the normalized 100 x 53.33 field", path))
