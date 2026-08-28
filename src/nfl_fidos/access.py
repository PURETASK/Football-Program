"""Role-based access and locked-artifact authorization controls."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ROLE_PERMISSIONS = {
    "player": {"read_own_development", "read_assigned_playbook", "read_roster", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "update_collaboration", "record_play_mastery", "submit_reflection", "submit_usability_feedback"},
    "coach_staff": {"read_team_context", "read_team_playbook", "read_staff", "read_player_development", "read_special_teams", "read_film", "read_media_review", "read_provider_adapter", "read_game_plan", "read_practice", "read_scheme", "read_analytics", "read_scouting", "read_roster", "read_delivery", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "collaborate_workspace", "resolve_collaboration", "assign_collaboration", "update_collaboration", "update_delivery", "draft_delivery", "draft_staff", "draft_player_development", "draft_special_teams", "draft_media_review", "draft_provider_adapter", "draft_scheme", "draft_scouting", "draft_roster", "draft_play", "draft_practice", "record_practice_attendance", "review_recommendation", "record_play_mastery", "collaborate_game_plan", "submit_usability_feedback"},
    "analyst": {"read_team_context", "read_film", "read_media_review", "read_provider_adapter", "read_game_plan", "read_practice", "read_scheme", "read_analytics", "read_scouting", "read_roster", "read_delivery", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "collaborate_workspace", "resolve_collaboration", "assign_collaboration", "update_collaboration", "update_delivery", "draft_delivery", "draft_media_review", "draft_provider_adapter", "draft_scheme", "draft_analytics", "draft_scouting", "create_metric", "create_scouting_claim", "refresh_source", "collaborate_game_plan", "submit_usability_feedback"},
    "performance_staff": {"read_performance", "read_roster", "read_practice", "read_delivery", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "collaborate_workspace", "assign_collaboration", "update_collaboration", "update_delivery", "draft_performance_support", "record_practice_attendance", "escalate_health_signal", "submit_usability_feedback"},
    "program_owner": {"read_all", "read_team_context", "read_team_playbook", "read_staff", "read_player_development", "read_special_teams", "read_media_review", "read_provider_adapter", "read_performance", "read_governance", "read_game_plan", "read_practice", "read_scheme", "read_analytics", "read_scouting", "read_roster", "read_delivery", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "collaborate_workspace", "resolve_collaboration", "assign_collaboration", "update_collaboration", "update_delivery", "draft_delivery", "draft_roster", "draft_play", "draft_media_review", "record_practice_attendance", "review_recommendation", "record_play_mastery", "approve_change", "lock_artifact", "unlock_artifact", "manage_permissions", "manage_sources", "manage_ontology", "manage_organization", "approve_organization", "approve_high_impact", "collaborate_game_plan", "run_media_worker", "run_agent_validation", "submit_usability_feedback"},
    "validator": {"read_governance", "read_delivery", "read_operations_inbox", "update_operations_inbox", "read_collaboration", "collaborate_workspace", "resolve_collaboration", "assign_collaboration", "update_collaboration", "validate_artifact", "reject_artifact", "review_safety", "run_agent_validation", "submit_usability_feedback"},
}

# Outcome capture is a bounded operational write shared by coaching and analytics staff.
ROLE_PERMISSIONS["coach_staff"].add("record_outcome")
ROLE_PERMISSIONS["analyst"].add("record_outcome")
ROLE_PERMISSIONS["program_owner"].add("record_outcome")
ROLE_PERMISSIONS["performance_staff"].add("record_outcome")

HIGH_IMPACT_ACTIONS = {"lock_artifact", "unlock_artifact", "approve_high_impact", "manage_permissions", "publish_locked"}


def authorize(
    *,
    decision_id: str,
    requester_role: str,
    action: str,
    resource: str,
    locked: bool = False,
    human_approved: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    if not decision_id.startswith("ACCESS-"):
        reasons.append("Decision id must start with ACCESS-")
    if requester_role not in ROLE_PERMISSIONS:
        reasons.append("Unknown requester role")
    if action not in ROLE_PERMISSIONS.get(requester_role, set()) and action not in {"read_own_development", "read_assigned_playbook"}:
        reasons.append("Role does not have the requested action")
    approval_required = locked or action in HIGH_IMPACT_ACTIONS
    if approval_required and not human_approved:
        status = "pending_human_approval" if not reasons else "denied"
        if locked:
            reasons.append("Locked artifact requires explicit human approval")
        if action in HIGH_IMPACT_ACTIONS:
            reasons.append("High-impact action requires explicit human approval")
    else:
        status = "denied" if reasons else "allowed"
    allowed = status == "allowed"
    return {
        "id": decision_id,
        "requester_role": requester_role,
        "action": action,
        "resource": resource,
        "locked": locked,
        "allowed": allowed,
        "status": status,
        "reasons": reasons,
        "human_approval_required": approval_required,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
