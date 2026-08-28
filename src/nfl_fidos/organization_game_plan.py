"""Tenant-scoped weekly game-plan package and owner review boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .game_plan_architecture import build_weekly_game_plan


def build_organization_game_plan(*, package_id: str, organization_id: str, season: str, team_context: str, week_context: str, plan: dict[str, Any], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-GAMEPLAN-"):
        issues.append({"code": "ORG-GAMEPLAN-ID", "message": "Package id must use ORG-GAMEPLAN- prefix", "path": "id"})
    if not organization_id.startswith("ORG-") or not season or not team_context or not week_context or not compiler:
        issues.append({"code": "ORG-GAMEPLAN-METADATA", "message": "organization, season, team context, week context, and compiler are required", "path": "metadata"})
    if not plan:
        issues.append({"code": "ORG-GAMEPLAN-EMPTY", "message": "A game-plan payload is required", "path": "plan"})
    try:
        compiled = build_weekly_game_plan(plan_id=plan.get("id", ""), team_context=team_context, week_context=week_context, identity=plan.get("identity", {}), assumptions=plan.get("assumptions", []), evidence_refs=plan.get("evidence_refs", []), offense=plan.get("offense", {}), defense=plan.get("defense", {}), special_teams=plan.get("special_teams", {}), opening_script=plan.get("opening_script", []), base_calls=plan.get("base_calls", []), shot_plan=plan.get("shot_plan", []), pressure_answers=plan.get("pressure_answers", []), situational_plans=plan.get("situational_plans", []), matchups=plan.get("matchups", []), contingencies=plan.get("contingencies", []), ownership=plan.get("ownership", {}), teaching_outputs=plan.get("teaching_outputs", []), in_game_update=plan.get("in_game_update", {}))
    except (TypeError, ValueError, KeyError) as exc:
        compiled = {"status": "invalid", "issues": [{"code": "ORG-GAMEPLAN-COMPILE", "message": str(exc), "path": "plan"}]}
    if compiled.get("status") != "under_review":
        issues.extend({"code": item.get("code", "ORG-GAMEPLAN-PLAN"), "message": item.get("message", "Game plan is invalid"), "path": f"plan.{item.get('path', '')}"} for item in compiled.get("issues", []))
    return {"id": package_id, "organization_id": organization_id, "season": season, "team_context": team_context, "week_context": week_context, "plan": compiled, "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_game_plan(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-GAMEPLAN-STATE", "message": "Only an under_review game-plan package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-GAMEPLAN-ROLE", "message": "Only a program_owner may validate organization game plans", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-GAMEPLAN-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
