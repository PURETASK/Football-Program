"""Deterministic minimum play-record compiler.

This compiler is deliberately narrow: it validates the structural invariants
that must hold before a play can enter a teaching, practice, or game-planning
workflow. It does not claim to prove a complete football play legal in every
team system; team-specific rules remain an explicit input and human authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompileIssue:
    code: str
    message: str
    path: str
    severity: str = "error"


@dataclass(frozen=True)
class CompileResult:
    valid: bool
    normalized_play: dict[str, Any]
    issues: tuple[CompileIssue, ...]


REQUIRED_ASSIGNMENT_ROLES = {"QB", "C"}
UNIT_ASSIGNMENT_ROLES = {"offense": {"QB", "C"}, "defense": {"MIKE", "DE"}, "special_teams": {"LS", "K"}}
VALID_STATUSES = {"draft", "validated", "locked", "rejected"}


def _issue(code: str, message: str, path: str, severity: str = "error") -> CompileIssue:
    return CompileIssue(code=code, message=message, path=path, severity=severity)


def compile_play(play: dict[str, Any]) -> CompileResult:
    """Validate and normalize a minimum play record without mutating input."""

    issues: list[CompileIssue] = []
    normalized = dict(play)

    required = ["id", "version", "team_context", "situation", "personnel", "formation", "assignments", "source", "status"]
    for field in required:
        if field not in play or play[field] in (None, "", []):
            issues.append(_issue("PLAY-REQUIRED", f"Missing required field: {field}", field))

    play_id = play.get("id")
    if play_id and (not isinstance(play_id, str) or not play_id.startswith("PLAY-")):
        issues.append(_issue("PLAY-ID", "Play id must start with PLAY-", "id"))

    unit = play.get("unit", "offense")
    required_roles = UNIT_ASSIGNMENT_ROLES.get(unit)
    if required_roles is None:
        issues.append(_issue("PLAY-UNIT", "Unit must be offense, defense, or special_teams", "unit"))
        required_roles = REQUIRED_ASSIGNMENT_ROLES

    situation = play.get("situation")
    if not isinstance(situation, dict):
        issues.append(_issue("PLAY-SITUATION", "Situation must be an object", "situation"))
    else:
        down = situation.get("down")
        distance = situation.get("distance")
        if not isinstance(down, int) or isinstance(down, bool) or not 1 <= down <= 4:
            issues.append(_issue("PLAY-DOWN", "Down must be an integer from 1 through 4", "situation.down"))
        if not isinstance(distance, int) or isinstance(distance, bool) or distance < 1:
            issues.append(_issue("PLAY-DISTANCE", "Distance must be a positive integer", "situation.distance"))
        if not isinstance(situation.get("field_zone"), str) or not situation.get("field_zone"):
            issues.append(_issue("PLAY-FIELD-ZONE", "Field zone is required", "situation.field_zone"))

    assignments = play.get("assignments")
    if not isinstance(assignments, list):
        issues.append(_issue("PLAY-ASSIGNMENTS", "Assignments must be a list", "assignments"))
    else:
        roles: set[str] = set()
        for index, assignment in enumerate(assignments):
            path = f"assignments[{index}]"
            if not isinstance(assignment, dict):
                issues.append(_issue("PLAY-ASSIGNMENT-SHAPE", "Assignment must be an object", path))
                continue
            role = assignment.get("role")
            action = assignment.get("assignment")
            if not isinstance(role, str) or not role:
                issues.append(_issue("PLAY-ASSIGNMENT-ROLE", "Assignment role is required", f"{path}.role"))
            elif role in roles:
                issues.append(_issue("PLAY-DUPLICATE-ROLE", f"Duplicate assignment role: {role}", f"{path}.role"))
            else:
                roles.add(role)
            if not isinstance(action, str) or not action:
                issues.append(_issue("PLAY-ASSIGNMENT-ACTION", "Assignment action is required", f"{path}.assignment"))
        missing_roles = sorted(required_roles - roles)
        if missing_roles:
            issues.append(_issue("PLAY-CORE-ROLES", f"Missing core assignment roles: {', '.join(missing_roles)}", "assignments"))

    source = play.get("source")
    if not isinstance(source, dict) or not source.get("kind") or not source.get("ref"):
        issues.append(_issue("PLAY-SOURCE", "Source kind and ref are required for provenance", "source"))

    status = play.get("status")
    if status not in VALID_STATUSES:
        issues.append(_issue("PLAY-STATUS", f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}", "status"))
    elif status in {"validated", "locked"} and issues:
        issues.append(_issue("PLAY-STATUS-CONFLICT", "A play with errors cannot be validated or locked", "status"))

    if issues:
        normalized["status"] = "rejected"
    elif status == "draft":
        normalized["status"] = "validated"

    return CompileResult(valid=not issues, normalized_play=normalized, issues=tuple(issues))
