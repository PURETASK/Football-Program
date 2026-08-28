"""Stage 15 authorized opponent profile, matchup, and scouting-report contracts."""

from __future__ import annotations

from typing import Any


AUTHORIZED_SOURCE_KINDS = {"licensed_film", "team_film", "public_gamebook", "public_roster", "team_locked_data", "authorized_analytics"}
CLAIM_CLASSIFICATIONS = {"observed", "measured", "reported", "inferred", "hypothesized"}


def validate_opponent_profile(profile: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "opponent", "season", "schedule_context", "roster_context", "offense", "defense", "special_teams", "sources"):
        if not profile.get(field) and profile.get(field) != []:
            issues.append({"code":"SCOUT-PROFILE-REQUIRED", "message":f"Missing profile field: {field}", "path":field})
    if profile.get("id") and not str(profile["id"]).startswith("OPP-PROFILE-"):
        issues.append({"code":"SCOUT-PROFILE-ID", "message":"Profile id must start with OPP-PROFILE-", "path":"id"})
    for index, source in enumerate(profile.get("sources", [])):
        if source.get("kind") not in AUTHORIZED_SOURCE_KINDS:
            issues.append({"code":"SCOUT-SOURCE-AUTH", "message":"Source is not authorized for opponent intelligence", "path":f"sources[{index}].kind"})
        if not source.get("ref") or not source.get("captured_at"):
            issues.append({"code":"SCOUT-SOURCE-PROVENANCE", "message":"Source ref and capture date are required", "path":f"sources[{index}]"})
    return issues


def build_opponent_profile(*, profile_id: str, opponent: str, season: str, schedule_context: dict[str, Any], roster_context: dict[str, Any], offense: dict[str, Any], defense: dict[str, Any], special_teams: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    profile = {"id":profile_id, "opponent":opponent, "season":season, "schedule_context":schedule_context, "roster_context":roster_context, "offense":offense, "defense":defense, "special_teams":special_teams, "sources":sources}
    issues = validate_opponent_profile(profile)
    return {**profile, "status":"invalid" if issues else "draft", "issues":issues, "human_review_required":True}


def build_situational_scouting_report(*, report_id: str, opponent: str, situation: dict[str, Any], claims: list[dict[str, Any]], sample_size: int, source_refs: list[str], analyst: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not report_id.startswith("SCOUT-REPORT-") or not opponent or not situation or not claims or sample_size <= 0 or not source_refs or not analyst:
        issues.append({"code":"SCOUT-REPORT-CONTEXT", "message":"Report identity, situation, claims, sample, sources, and analyst are required", "path":"context"})
    for index, claim in enumerate(claims):
        if claim.get("classification") not in CLAIM_CLASSIFICATIONS:
            issues.append({"code":"SCOUT-CLAIM-CLASSIFICATION", "message":"Every claim requires an evidence classification", "path":f"claims[{index}].classification"})
        if not claim.get("confidence") or not claim.get("uncertainty") or not claim.get("evidence_refs"):
            issues.append({"code":"SCOUT-CLAIM-EVIDENCE", "message":"Every claim requires confidence, uncertainty, and evidence refs", "path":f"claims[{index}]"})
    return {"id":report_id, "opponent":opponent, "situation":situation, "claims":claims, "sample_size":sample_size, "source_refs":source_refs, "analyst":analyst, "limitations":["Tendencies describe the available sample and do not guarantee future behavior.", "Opponent adaptation remains a live uncertainty."], "status":"invalid" if issues else "under_review", "human_review_required":True, "issues":issues}


def build_matchup_model(*, model_id: str, opponent: str, matchups: list[dict[str, Any]], evidence_refs: list[str], context: dict[str, Any], analyst: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not model_id.startswith("MATCHUP-") or not opponent or not matchups or not evidence_refs or not context or not analyst:
        issues.append({"code":"MATCHUP-CONTEXT", "message":"Matchup identity, options, evidence, context, and analyst are required", "path":"context"})
    for index, matchup in enumerate(matchups):
        for field in ("our_role", "opponent_role", "advantage_hypothesis", "counter", "uncertainty"):
            if not matchup.get(field):
                issues.append({"code":"MATCHUP-REQUIRED", "message":f"Matchup requires {field}", "path":f"matchups[{index}].{field}"})
    return {"id":model_id, "opponent":opponent, "matchups":matchups, "evidence_refs":evidence_refs, "context":context, "analyst":analyst, "status":"invalid" if issues else "draft", "human_review_required":True, "issues":issues}


def build_opponent_evolution(*, evolution_id: str, opponent: str, historical_claims: list[dict[str, Any]], current_claims: list[dict[str, Any]], evidence_refs: list[str], analyst: str) -> dict[str, Any]:
    issues: list[str] = []
    if not evolution_id.startswith("EVOLUTION-") or not opponent or not historical_claims or not current_claims or not evidence_refs or not analyst:
        issues.append("historical/current claims, evidence, opponent, and analyst are required")
    return {"id":evolution_id, "opponent":opponent, "historical_claims":historical_claims, "current_claims":current_claims, "evidence_refs":evidence_refs, "analyst":analyst, "status":"invalid" if issues else "under_review", "adaptation_warning":"A historical tendency may intentionally change when observed by an opponent.", "issues":issues}
