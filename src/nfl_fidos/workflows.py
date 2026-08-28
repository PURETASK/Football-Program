"""Composition of the Master Plan's core football workflows."""

from __future__ import annotations

from typing import Any

from .game_plan import build_game_plan_options
from .player_learning import build_player_lesson
from .practice import build_practice_plan
from .scheme import build_scheme


def run_player_development_loop(
    *,
    run_id: str,
    play: dict[str, Any],
    learner_role: str,
    drills: list[dict[str, Any]],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    """Assess -> teach -> practice -> evaluate -> adapt, leaving adaptation human-reviewed."""
    if not run_id.startswith("RUN-"):
        raise ValueError({"code": "WORKFLOW-ID", "message": "Run id must start with RUN-"})
    if not assessment:
        raise ValueError({"code": "WORKFLOW-ASSESSMENT", "message": "Assessment is required"})
    try:
        lesson = build_player_lesson(play, learner_role)
        practice = build_practice_plan(
            plan_id=f"PRACTICE-{run_id.removeprefix('RUN-')}", team_context=play["team_context"],
            objective=lesson["objective"], drills=drills,
        )
    except (KeyError, ValueError) as error:
        return {"id": run_id, "workflow_id": "WF-001", "status": "blocked", "inputs": [play.get("id"), learner_role], "outputs": [], "review_required": True, "issues": [str(error)]}
    return {
        "id": run_id, "workflow_id": "WF-001", "status": "ready_for_review",
        "inputs": [play["id"], learner_role, assessment],
        "outputs": [lesson, practice, {"type": "evaluation", "assessment": assessment}],
        "review_required": True,
        "adaptation": {"status": "pending_coach_review", "reason": "Progression changes require human authority."},
    }


def run_weekly_team_loop(
    *,
    run_id: str,
    team_context: str,
    self_scout: dict[str, Any],
    opponent_scout: dict[str, Any],
    practice_plan: dict[str, Any],
    game_plan: dict[str, Any],
) -> dict[str, Any]:
    required = [self_scout, opponent_scout, practice_plan, game_plan]
    if not run_id.startswith("RUN-"):
        raise ValueError({"code": "WORKFLOW-ID", "message": "Run id must start with RUN-"})
    if not team_context or any(not item for item in required):
        return {"id": run_id, "workflow_id": "WF-002", "status": "blocked", "inputs": [team_context], "outputs": [], "review_required": True, "issues": [{"code": "WEEKLY-INPUTS", "message": "Team context and all weekly loop inputs are required"}]}
    statuses = [item.get("status") for item in required]
    if any(status in {"rejected", "invalid"} for status in statuses):
        return {"id": run_id, "workflow_id": "WF-002", "status": "blocked", "inputs": statuses, "outputs": [], "review_required": True, "issues": [{"code": "WEEKLY-INVALID-INPUT", "message": "Weekly loop cannot proceed with invalid inputs"}]}
    return {
        "id": run_id, "workflow_id": "WF-002", "status": "ready_for_review",
        "inputs": [team_context, self_scout, opponent_scout, practice_plan, game_plan],
        "outputs": [{"type": "weekly_packet", "team_context": team_context, "sections": ["self_scout", "opponent_scout", "practice", "game_plan"]}],
        "review_required": True,
        "decision": "Staff must approve the final weekly packet before lock.",
    }


def run_scheme_selection(*, run_id: str, candidate_schemes: list[dict[str, Any]], problem: str, evidence_refs: list[str]) -> dict[str, Any]:
    if not run_id.startswith("RUN-") or not problem or not evidence_refs or not candidate_schemes:
        raise ValueError({"code": "SCHEME-SELECTION-INPUT", "message": "Run id, problem, evidence, and candidates are required"})
    evaluated = [build_scheme(scheme) for scheme in candidate_schemes]
    valid = [scheme for scheme in evaluated if scheme["status"] == "validated"]
    return {
        "id": run_id, "workflow_id": "WF-003", "status": "ready_for_review" if valid else "blocked",
        "inputs": [problem, evidence_refs],
        "outputs": [{"type": "scheme_options", "options": valid, "rejected_count": len(evaluated) - len(valid)}],
        "review_required": True,
        "decision": "No scheme is automatically locked; staff must select and approve an option.",
    }
