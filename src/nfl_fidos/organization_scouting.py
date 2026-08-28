"""Tenant-scoped opponent scouting package with source and review boundaries."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report


def build_organization_scouting_package(*, package_id: str, organization_id: str, opponent: str, season: str, source_refs: list[str], profile: dict[str, Any], reports: list[dict[str, Any]], matchups: list[dict[str, Any]], evolutions: list[dict[str, Any]], analyst: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-SCOUT-"):
        issues.append({"code": "ORG-SCOUT-ID", "message": "Package id must use ORG-SCOUT- prefix", "path": "id"})
    if not organization_id.startswith("ORG-") or not opponent or not season or not analyst:
        issues.append({"code": "ORG-SCOUT-METADATA", "message": "organization, opponent, season, and analyst are required", "path": "metadata"})
    if not source_refs:
        issues.append({"code": "ORG-SCOUT-SOURCE", "message": "source_refs are required", "path": "source_refs"})
    profile_result = build_opponent_profile(profile_id=profile.get("id", ""), opponent=opponent, season=season, schedule_context=profile.get("schedule_context", {}), roster_context=profile.get("roster_context", {}), offense=profile.get("offense", {}), defense=profile.get("defense", {}), special_teams=profile.get("special_teams", {}), sources=profile.get("sources", []))
    for issue in profile_result.get("issues", []):
        issues.append({"code": issue["code"], "message": issue["message"], "path": f"profile.{issue['path']}"})
    if profile_result.get("opponent") != opponent:
        issues.append({"code": "ORG-SCOUT-PROFILE-SCOPE", "message": "Profile opponent must match package opponent", "path": "profile.opponent"})
    report_results: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        result = build_situational_scouting_report(report_id=report.get("id", ""), opponent=opponent, situation=report.get("situation", {}), claims=report.get("claims", []), sample_size=report.get("sample_size", 0), source_refs=report.get("source_refs", []), analyst=analyst)
        report_results.append(result)
        if result["status"] != "under_review":
            issues.extend({"code": item["code"], "message": item["message"], "path": f"reports[{index}].{item['path']}"} for item in result.get("issues", []))
        if any(ref not in source_refs for ref in result.get("source_refs", [])):
            issues.append({"code": "ORG-SCOUT-SOURCE-LINK", "message": "Report source refs must be listed in package source_refs", "path": f"reports[{index}].source_refs"})
    matchup_results: list[dict[str, Any]] = []
    for index, matchup in enumerate(matchups):
        result = build_matchup_model(model_id=matchup.get("id", ""), opponent=opponent, matchups=matchup.get("matchups", []), evidence_refs=matchup.get("evidence_refs", []), context=matchup.get("context", {}), analyst=analyst)
        matchup_results.append(result)
        if result["status"] != "draft":
            issues.extend({"code": item["code"], "message": item["message"], "path": f"matchups[{index}].{item['path']}"} for item in result.get("issues", []))
    evolution_results: list[dict[str, Any]] = []
    for index, evolution in enumerate(evolutions):
        result = build_opponent_evolution(evolution_id=evolution.get("id", ""), opponent=opponent, historical_claims=evolution.get("historical_claims", []), current_claims=evolution.get("current_claims", []), evidence_refs=evolution.get("evidence_refs", []), analyst=analyst)
        evolution_results.append(result)
        if result["status"] != "under_review":
            issues.append({"code": "ORG-SCOUT-EVOLUTION", "message": "Evolution record is invalid", "path": f"evolutions[{index}]"})
    return {"id": package_id, "organization_id": organization_id, "opponent": opponent, "season": season, "source_refs": list(source_refs), "profile": profile_result, "reports": report_results, "matchups": matchup_results, "evolutions": evolution_results, "analyst": analyst, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_scouting_package(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-SCOUT-STATE", "message": "Only an under_review scouting package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-SCOUT-ROLE", "message": "Only a program_owner may validate organization scouting", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-SCOUT-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
