"""Stage 17 weekly game-plan, countermeasure, trigger, and teaching contracts."""

from __future__ import annotations

from typing import Any


SITUATIONS = {"third_down", "red_zone", "short_yardage", "goal_line", "backed_up", "two_minute", "four_minute", "opening_script", "normal"}


def validate_game_plan(plan: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ("id", "team_context", "week_context", "identity", "assumptions", "evidence_refs", "offense", "defense", "special_teams", "opening_script", "base_calls", "shot_plan", "pressure_answers", "situational_plans", "matchups", "contingencies", "ownership", "teaching_outputs", "in_game_update")
    for field in required:
        if not plan.get(field) and plan.get(field) != []:
            issues.append({"code":"GAMEPLAN-REQUIRED", "message":f"Missing game-plan field: {field}", "path":field})
    if plan.get("id") and not str(plan["id"]).startswith("GAMEPLAN-"):
        issues.append({"code":"GAMEPLAN-ID", "message":"Game-plan id must start with GAMEPLAN-", "path":"id"})
    for index, trigger in enumerate(plan.get("contingencies", [])):
        for field in ("id", "trigger", "response", "owner", "evidence_refs"):
            if not trigger.get(field):
                issues.append({"code":"GAMEPLAN-TRIGGER", "message":f"Contingency requires {field}", "path":f"contingencies[{index}].{field}"})
    for index, situation in enumerate(plan.get("situational_plans", [])):
        if situation.get("situation") not in SITUATIONS:
            issues.append({"code":"GAMEPLAN-SITUATION", "message":"Unknown situational plan", "path":f"situational_plans[{index}].situation"})
        if not situation.get("primary") or not situation.get("opponent_responses") or not situation.get("counters"):
            issues.append({"code":"GAMEPLAN-COUNTERS", "message":"Situational plan requires primary, opponent responses, and counters", "path":f"situational_plans[{index}]"})
    if not isinstance(plan.get("ownership"), dict) or not plan["ownership"].get("head_coach"):
        issues.append({"code":"GAMEPLAN-OWNERSHIP", "message":"Head-coach ownership is required", "path":"ownership"})
    if not isinstance(plan.get("teaching_outputs"), list) or not plan["teaching_outputs"]:
        issues.append({"code":"GAMEPLAN-TEACHING", "message":"Player-facing teaching outputs are required", "path":"teaching_outputs"})
    return issues


def build_weekly_game_plan(*, plan_id: str, team_context: str, week_context: str, identity: dict[str, Any], assumptions: list[str], evidence_refs: list[str], offense: dict[str, Any], defense: dict[str, Any], special_teams: dict[str, Any], opening_script: list[dict[str, Any]], base_calls: list[dict[str, Any]], shot_plan: list[dict[str, Any]], pressure_answers: list[dict[str, Any]], situational_plans: list[dict[str, Any]], matchups: list[dict[str, Any]], contingencies: list[dict[str, Any]], ownership: dict[str, Any], teaching_outputs: list[dict[str, Any]], in_game_update: dict[str, Any]) -> dict[str, Any]:
    plan = {"id":plan_id, "team_context":team_context, "week_context":week_context, "identity":identity, "assumptions":assumptions, "evidence_refs":evidence_refs, "offense":offense, "defense":defense, "special_teams":special_teams, "opening_script":opening_script, "base_calls":base_calls, "shot_plan":shot_plan, "pressure_answers":pressure_answers, "situational_plans":situational_plans, "matchups":matchups, "contingencies":contingencies, "ownership":ownership, "teaching_outputs":teaching_outputs, "in_game_update":in_game_update}
    issues = validate_game_plan(plan)
    return {**plan, "status":"invalid" if issues else "under_review", "human_decision_required":True, "issues":issues}


def build_countermeasure(*, countermeasure_id: str, threat: str, primary_response: str, opponent_counter: str, counter_counter: str, trigger: str, evidence_refs: list[str], owner: str) -> dict[str, Any]:
    issues: list[str] = []
    if not countermeasure_id.startswith("COUNTERMEASURE-") or not all((threat, primary_response, opponent_counter, counter_counter, trigger, owner)) or not evidence_refs:
        issues.append("countermeasure requires identity, threat, responses, trigger, evidence, and owner")
    return {"id":countermeasure_id, "threat":threat, "primary_response":primary_response, "opponent_counter":opponent_counter, "counter_counter":counter_counter, "trigger":trigger, "evidence_refs":evidence_refs, "owner":owner, "status":"invalid" if issues else "draft", "human_review_required":True, "issues":issues}
