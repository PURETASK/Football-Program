"""Stage 9 play-family, dependency, role-extraction, and publishing contracts."""

from __future__ import annotations

from typing import Any

from .play_compiler import compile_play


INSTALL_LEVELS = {"install", "review", "game_ready", "situational"}
APPROVAL_STATES = {"draft", "pending_approval", "approved", "rejected", "superseded"}


def validate_play_spec(play: dict[str, Any]) -> list[dict[str, str]]:
    """Validate extended play metadata in addition to compiler invariants."""
    issues: list[dict[str, str]] = []
    compiled = compile_play(play)
    issues.extend({"code": issue.code, "message": issue.message, "path": issue.path} for issue in compiled.issues)
    required = {
        "play_family_id": str, "checks": list, "situational_variants": list,
        "opponent_notes": list, "coaching_notes": list, "install_level": str,
        "dependencies": list, "approval": dict,
    }
    for field, expected in required.items():
        if field not in play:
            issues.append({"code":"PLAY-SPEC-REQUIRED", "message":f"Missing extended play field: {field}", "path":field})
        elif not isinstance(play[field], expected):
            issues.append({"code":"PLAY-SPEC-TYPE", "message":f"Extended field has wrong type: {field}", "path":field})
    if play.get("play_family_id") and not str(play["play_family_id"]).startswith("PLAY-FAM-"):
        issues.append({"code":"PLAY-FAMILY-ID", "message":"Play family id must start with PLAY-FAM-", "path":"play_family_id"})
    if play.get("install_level") not in INSTALL_LEVELS:
        issues.append({"code":"PLAY-INSTALL-LEVEL", "message":"Unknown installation level", "path":"install_level"})
    assignments = play.get("assignments", [])
    if isinstance(assignments, list):
        for index, assignment in enumerate(assignments):
            if isinstance(assignment, dict) and not assignment.get("responsibility"):
                issues.append({"code":"PLAY-RESPONSIBILITY", "message":"Assignment requires an explicit responsibility", "path":f"assignments[{index}].responsibility"})
    approval = play.get("approval", {})
    if isinstance(approval, dict) and approval.get("state") not in APPROVAL_STATES:
        issues.append({"code":"PLAY-APPROVAL-STATE", "message":"Unknown approval state", "path":"approval.state"})
    return issues


def build_play_family(*, family_id: str, name: str, unit: str, concept_ids: list[str], variants: list[str], owner: str) -> dict[str, Any]:
    if not family_id.startswith("PLAY-FAM-") or not name or unit not in {"offense", "defense", "special_teams"} or not concept_ids or not variants or not owner:
        raise ValueError({"code":"PLAY-FAMILY-INCOMPLETE", "message":"Family id, name, unit, concepts, variants, and owner are required"})
    return {"id":family_id, "name":name, "unit":unit, "concept_ids":concept_ids, "variants":variants, "owner":owner, "version":"0.1.0", "status":"draft"}


def build_extended_play(play: dict[str, Any], *, play_family_id: str, install_level: str, checks: list[dict[str, Any]], situational_variants: list[dict[str, Any]], opponent_notes: list[str], coaching_notes: list[str], dependencies: list[str], approval_state: str = "draft") -> dict[str, Any]:
    """Add the full Stage 9 metadata envelope without mutating the source play."""
    output = dict(play)
    output.update({
        "play_family_id": play_family_id, "checks": checks, "situational_variants": situational_variants,
        "opponent_notes": opponent_notes, "coaching_notes": coaching_notes, "install_level": install_level,
        "dependencies": dependencies, "approval": {"state": approval_state, "approver": None, "decision_ref": None},
    })
    issues = validate_play_spec(output)
    output["status"] = "rejected" if issues else "draft"
    output["spec_issues"] = issues
    return output


def extract_role_play_spec(play: dict[str, Any], *, role: str) -> dict[str, Any]:
    issues = validate_play_spec(play)
    if issues:
        raise ValueError({"code":"PLAY-SPEC-INVALID", "issues":issues})
    assignment = next((item for item in play["assignments"] if item.get("role") == role), None)
    if assignment is None:
        raise ValueError({"code":"PLAY-ROLE-MISSING", "role":role})
    return {
        "id": f"ROLEVIEW-{play['id']}-{role}", "play_id": play["id"], "version": play["version"],
        "role": role, "family_id": play["play_family_id"], "situation": play["situation"],
        "assignment": assignment, "checks": [check for check in play["checks"] if check.get("role") in {None, role}],
        "coaching_notes": play["coaching_notes"], "install_level": play["install_level"], "status":"renderable",
    }


def request_play_approval(play: dict[str, Any], *, requester: str, decision_ref: str) -> dict[str, Any]:
    issues = validate_play_spec(play)
    output = dict(play)
    if issues:
        output["approval"] = {"state":"rejected", "approver":None, "decision_ref":decision_ref, "requester":requester}
        output["approval_issues"] = issues
    else:
        output["approval"] = {"state":"pending_approval", "approver":None, "decision_ref":decision_ref, "requester":requester}
    return output


def approve_play(play: dict[str, Any], *, approver: str, decision_ref: str) -> dict[str, Any]:
    issues = validate_play_spec(play)
    approval = play.get("approval", {})
    output = dict(play)
    if issues or approval.get("state") != "pending_approval":
        output["approval"] = {"state":"rejected", "approver":approver, "decision_ref":decision_ref}
        output["status"] = "rejected"
        output["approval_issues"] = issues or [{"code":"PLAY-APPROVAL-PENDING", "message":"Play must be pending approval", "path":"approval.state"}]
    else:
        output["approval"] = {"state":"approved", "approver":approver, "decision_ref":decision_ref}
        output["status"] = "locked"
    return output
