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
BLOCKING_PRIMITIVES = {"base", "reach", "down", "pull", "trap", "wrap", "fold", "combo", "climb", "scoop", "insert", "arc", "screen_release"}
PROTECTION_MODES = {"man", "full_slide", "half_slide_left", "half_slide_right", "scan", "screen"}
TARGETED_BLOCKING_PRIMITIVES = {"pull", "trap", "wrap", "fold", "insert", "arc"}
ROUTE_FAMILIES = {"quick", "dropback", "intermediate", "vertical", "screen", "crossing", "sight"}
ROUTE_BREAKS = {"none", "speed_out", "comeback", "curl", "dig", "over", "post", "corner", "whip", "choice", "option"}
ROUTE_FINISHES = {"vertical", "inside", "outside", "settle", "runaway"}
ROUTE_OPTION_RULES = {"none", "leverage", "safety", "coverage", "sight"}


def _issue(code: str, message: str, path: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "message": message, "path": path, "severity": severity}


def normalize_term(term: str) -> str:
    """Create a stable lookup key without changing the displayed call word."""
    return "_".join(term.strip().lower().replace("/", " ").replace("-", " ").split())


def _validate_route_semantics(element: dict[str, Any], path: str, issues: list[dict[str, str]]) -> None:
    for field, allowed in (("route_family", ROUTE_FAMILIES), ("break_type", ROUTE_BREAKS), ("finish_direction", ROUTE_FINISHES), ("option_rule", ROUTE_OPTION_RULES)):
        value = element.get(field)
        if value is not None and value not in allowed:
            issues.append(_issue("DESIGN-ROUTE-SEMANTIC", f"Unsupported route {field}: {value}", f"{path}.{field}"))
    for field in ("stem_depth_yards", "break_depth_yards"):
        value = element.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value > 60):
            issues.append(_issue("DESIGN-ROUTE-DEPTH", f"Route {field} must be a number from 0 through 60", f"{path}.{field}"))
    if element.get("break_depth_yards") is not None and element.get("break_type") in {None, "none"}:
        issues.append(_issue("DESIGN-ROUTE-BREAK-CONTEXT", "Break depth is declared without a route break type", f"{path}.break_type", "warning"))


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
        # The structural envelope follows the selected game format.  Keep the
        # traditional 11-player default, but do not reject a valid 5-on-5
        # flag design before the profile-aware legality pass can evaluate it.
        rule_profile = design.get("rule_profile", "nfl")
        expected_players = 5 if rule_profile == "flag" else 11
        if rule_profile == "youth" and isinstance(design.get("players_on_field"), int) and design["players_on_field"] > 0:
            expected_players = design["players_on_field"]
        if len(design["players"]) != expected_players:
            issues.append(_issue("DESIGN-PLAYER-COUNT", f"The selected rule profile requires {expected_players} players in the design", "players"))

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
            if kind == "route":
                _validate_route_semantics(element, path, issues)
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
                            for field in ("id", "label", "condition"):
                                if not isinstance(branch.get(field), str) or not branch.get(field, "").strip():
                                    issues.append(_issue("DESIGN-BRANCH-REQUIRED", f"Alternate path requires a non-empty {field}", f"{branch_path}.{field}"))
                            branch_ids = [item.get("id") for item in branches[:branch_index] if isinstance(item, dict) and isinstance(item.get("id"), str)]
                            if branch.get("id") in branch_ids:
                                issues.append(_issue("DESIGN-BRANCH-ID-DUPLICATE", f"Duplicate alternate path id: {branch.get('id')}", f"{branch_path}.id"))
                            branch_points = branch.get("points")
                            if not isinstance(branch_points, list) or len(branch_points) < 2:
                                issues.append(_issue("DESIGN-BRANCH-PATH", "Alternate paths require at least two points", f"{branch_path}.points"))
                            else:
                                for point_index, point in enumerate(branch_points):
                                    _validate_point(point, f"{branch_path}.points[{point_index}]", issues)
                            if kind == "route":
                                _validate_route_semantics(branch, branch_path, issues)
                if element.get("arrow_style") not in ARROW_STYLES:
                    issues.append(_issue("DESIGN-ARROW", "Movement elements require a canonical arrow style", f"{path}.arrow_style"))
            if design.get("unit") == "offense" and kind in {"block", "run"}:
                primitive = element.get("blocking_primitive")
                if primitive is not None and primitive not in BLOCKING_PRIMITIVES:
                    issues.append(_issue("DESIGN-BLOCK-PRIMITIVE", f"Unsupported blocking primitive: {primitive}", f"{path}.blocking_primitive"))
                target_id = element.get("block_target_element_id") or element.get("target_element_id")
                partner_id = element.get("block_partner_element_id")
                element_ids = {candidate.get("id") for candidate in elements if isinstance(candidate, dict) and candidate.get("id")}
                if target_id and target_id not in element_ids:
                    issues.append(_issue("DESIGN-BLOCK-TARGET-REF", "Blocking target does not reference an assignment in this play", f"{path}.block_target_element_id"))
                if target_id == element.get("id"):
                    issues.append(_issue("DESIGN-BLOCK-SELF", "A block cannot target itself", f"{path}.block_target_element_id"))
                if partner_id and partner_id not in element_ids:
                    issues.append(_issue("DESIGN-BLOCK-PARTNER-REF", "Blocking partner does not reference an assignment in this play", f"{path}.block_partner_element_id"))
                if partner_id == element.get("id"):
                    issues.append(_issue("DESIGN-BLOCK-PARTNER-SELF", "A block cannot partner with itself", f"{path}.block_partner_element_id"))
                if primitive in TARGETED_BLOCKING_PRIMITIVES and not target_id:
                    issues.append(_issue("DESIGN-BLOCK-TARGET", f"{primitive} blocking requires an explicit target assignment", f"{path}.block_target_element_id"))
                if primitive == "combo" and not partner_id:
                    issues.append(_issue("DESIGN-COMBO-PARTNER", "Combo blocking requires a second blocker partner", f"{path}.block_partner_element_id"))
                if primitive == "combo" and not target_id:
                    issues.append(_issue("DESIGN-COMBO-TARGET", "Combo blocking requires an explicit second-level target", f"{path}.block_target_element_id"))
                protection_mode = element.get("protection_mode")
                if protection_mode is not None and protection_mode not in PROTECTION_MODES:
                    issues.append(_issue("DESIGN-PROTECTION-MODE", f"Unsupported protection mode: {protection_mode}", f"{path}.protection_mode"))
                if protection_mode and protection_mode != "screen" and not element.get("protection_target_element_id"):
                    issues.append(_issue("DESIGN-PROTECTION-TARGET", "Protection mode requires an explicit threat or protected target", f"{path}.protection_target_element_id", "warning"))
                protection_target = element.get("protection_target_element_id")
                if protection_target and protection_target not in element_ids:
                    issues.append(_issue("DESIGN-PROTECTION-TARGET-REF", "Protection target does not reference an assignment in this play", f"{path}.protection_target_element_id"))
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
        # Flag has no tackle-football seven-player line requirement.  Its
        # profile-specific constraints are enforced by advanced legality.
        if profile != "flag" and explicit_line and len(explicit_line) < 7:
            issues.append(_issue("LEGALITY-LINE-COUNT", "Offensive alignment declares fewer than seven players on the line", "players", "error"))
        if profile != "flag" and explicit_line and len(explicit_line) >= 7:
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
