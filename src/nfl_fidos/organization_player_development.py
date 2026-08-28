"""Tenant-scoped player development plans and mastery evidence boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .development import build_development_plan, build_mastery_record


def build_organization_player_development(*, package_id: str, organization_id: str, team_context: str, season: str, players: list[dict[str, Any]], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-PLAYER-DEV-"):
        issues.append({"code": "ORG-PLAYER-DEV-ID", "message": "Package id must use ORG-PLAYER-DEV- prefix", "path": "id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "ORG-PLAYER-DEV-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not team_context or not season or not compiler:
        issues.append({"code": "ORG-PLAYER-DEV-METADATA", "message": "team_context, season, and compiler are required", "path": "metadata"})
    if not players:
        issues.append({"code": "ORG-PLAYER-DEV-EMPTY", "message": "At least one player record is required", "path": "players"})
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, player in enumerate(players):
        player_id = player.get("player_id", "")
        if not player_id.startswith("PLAYER-"):
            issues.append({"code": "ORG-PLAYER-DEV-PLAYER", "message": "player_id must use PLAYER- prefix", "path": f"players[{index}].player_id"})
        if player_id in seen:
            issues.append({"code": "ORG-PLAYER-DEV-DUPLICATE", "message": "Duplicate player_id", "path": f"players[{index}].player_id"})
        seen.add(player_id)
        try:
            plan = build_development_plan(plan_id=player.get("plan_id", f"IDP-{player_id.removeprefix('PLAYER-')}"), learner_id=player_id, learner_type="player", objectives=player.get("objectives", []), owner=player.get("owner", compiler), review_cadence=player.get("review_cadence", "weekly"))
        except (TypeError, ValueError, KeyError) as exc:
            plan = {"status": "invalid", "issues": [{"code": "ORG-PLAYER-DEV-PLAN", "message": str(exc), "path": f"players[{index}].objectives"}]}
        mastery_records: list[dict[str, Any]] = []
        for mastery_index, mastery in enumerate(player.get("mastery_records", [])):
            record = build_mastery_record(record_id=mastery.get("record_id", f"MASTERY-{player_id.removeprefix('PLAYER-')}-{mastery_index + 1:03d}"), learner_id=player_id, capability_id=mastery.get("capability_id", ""), current_level=mastery.get("current_level", ""), target_level=mastery.get("target_level", ""), evidence=mastery.get("evidence", []), next_actions=mastery.get("next_actions", []))
            mastery_records.append(record)
            if record["status"] == "invalid":
                issues.extend({"code": item["code"], "message": item["message"], "path": f"players[{index}].mastery_records[{mastery_index}].{item['path']}"} for item in record.get("issues", []))
        if plan.get("status") == "under_review":
            issues.extend({"code": item["code"], "message": item["message"], "path": f"players[{index}].{item['path']}"} for item in plan.get("issues", []))
        elif plan.get("status") == "invalid":
            issues.append({"code": "ORG-PLAYER-DEV-PLAN", "message": "Player development plan is invalid", "path": f"players[{index}].plan"})
        records.append({"player_id": player_id, "position": player.get("position", ""), "plan": plan, "mastery_records": mastery_records, "privacy_boundary": "player can read own development only; staff review required for team-level interpretation"})
    return {"id": package_id, "organization_id": organization_id, "team_context": team_context, "season": season, "players": records, "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_player_development(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-PLAYER-DEV-STATE", "message": "Only an under_review package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-PLAYER-DEV-ROLE", "message": "Only a program_owner may validate player development", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-PLAYER-DEV-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
