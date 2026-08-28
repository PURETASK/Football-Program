"""Stage 5 coaching staff architecture and development contracts."""

from __future__ import annotations

from typing import Any


COACH_ROLES = {
    "head_coach": ("leadership", "culture", "decision_quality", "staff_alignment", "program_evaluation"),
    "offensive_coordinator": ("offensive_scheme", "installation", "play_calling", "adjustments", "staff_alignment"),
    "defensive_coordinator": ("defensive_scheme", "installation", "play_calling", "adjustments", "staff_alignment"),
    "special_teams_coordinator": ("special_teams_scheme", "phase_installation", "situational_management", "unit_development", "staff_alignment"),
    "position_coach": ("technique_teaching", "assignment_teaching", "film_diagnosis", "practice_design", "player_evaluation"),
    "quality_control": ("film_process", "data_quality", "scouting_support", "documentation", "communication"),
    "analyst": ("metric_definition", "evidence_quality", "contextual_interpretation", "visualization", "communication"),
    "game_management": ("clock_management", "rules_application", "decision_process", "contingency_planning", "communication"),
}


def build_coaching_staff_architecture(*, architecture_id: str, staff: list[dict[str, Any]], season: str, team_context: str) -> dict[str, Any]:
    """Build a role-complete staff map with explicit interfaces and review ownership."""
    issues: list[dict[str, str]] = []
    if not architecture_id.startswith("STAFF-"):
        issues.append({"code": "STAFF-ID", "message": "Architecture id must start with STAFF-", "path": "architecture_id"})
    if not season or not team_context or not staff:
        issues.append({"code": "STAFF-CONTEXT", "message": "Season, team context, and staff are required", "path": "context"})
    unknown = [person.get("role") for person in staff if person.get("role") not in COACH_ROLES]
    if unknown:
        issues.append({"code": "STAFF-ROLE", "message": f"Unsupported staff roles: {unknown}", "path": "staff"})
    records = [{
        "person_id": person.get("person_id"), "role": person.get("role"),
        "dimensions": list(COACH_ROLES.get(person.get("role"), ())),
        "reports_to": person.get("reports_to"), "review_owner": person.get("review_owner"),
    } for person in staff]
    return {
        "id": architecture_id, "season": season, "team_context": team_context,
        "staff": records,
        "interfaces": [
            {"from_role": "head_coach", "to_role": "offensive_coordinator", "purpose": "program identity and weekly alignment"},
            {"from_role": "head_coach", "to_role": "defensive_coordinator", "purpose": "program identity and weekly alignment"},
            {"from_role": "coordinator", "to_role": "position_coach", "purpose": "installation and correction priorities"},
            {"from_role": "quality_control", "to_role": "coordinator", "purpose": "film and evidence delivery"},
            {"from_role": "game_management", "to_role": "head_coach", "purpose": "rule-aware situational decision support"},
        ],
        "status": "invalid" if issues else "draft", "review_required": True, "issues": issues,
    }


def build_coach_development_pathway(*, pathway_id: str, coach_id: str, role: str, objectives: list[dict[str, Any]], mentor_id: str) -> dict[str, Any]:
    """Create a measurable role-specific pathway with teach/diagnose/improve stages."""
    issues: list[dict[str, str]] = []
    if not pathway_id.startswith("PATH-COACH-") or not coach_id or role not in COACH_ROLES or not mentor_id:
        issues.append({"code": "PATHWAY-IDENTITY", "message": "Pathway, coach, supported role, and mentor are required", "path": "identity"})
    expected = set(COACH_ROLES.get(role, ()))
    missing_dimensions = sorted(expected - {item.get("dimension") for item in objectives})
    if missing_dimensions:
        issues.append({"code": "PATHWAY-DIMENSIONS", "message": f"Missing role dimensions: {missing_dimensions}", "path": "objectives"})
    incomplete = [index for index, item in enumerate(objectives) if not item.get("measure") or not item.get("evidence_source")]
    if incomplete:
        issues.append({"code": "PATHWAY-MEASURES", "message": "Every objective needs a measure and evidence source", "path": "objectives"})
    return {
        "id": pathway_id, "coach_id": coach_id, "role": role, "mentor_id": mentor_id,
        "objectives": objectives,
        "stages": ["observe", "teach", "practice", "diagnose", "adapt", "review"],
        "status": "invalid" if issues else "draft", "review_required": True, "issues": issues,
    }


def evaluate_coach_performance(*, evaluation_id: str, coach_id: str, role: str, ratings: dict[str, float], evidence: list[dict[str, Any]], evaluator: str) -> dict[str, Any]:
    """Evaluate only observable coaching dimensions and retain evidence for review."""
    issues: list[dict[str, str]] = []
    if not evaluation_id.startswith("EVAL-COACH-") or not coach_id or role not in COACH_ROLES or not evaluator:
        issues.append({"code": "COACH-EVAL-IDENTITY", "message": "Evaluation identity, role, and evaluator are required", "path": "identity"})
    missing = sorted(set(COACH_ROLES.get(role, ())) - set(ratings))
    if missing:
        issues.append({"code": "COACH-EVAL-DIMENSIONS", "message": f"Missing ratings: {missing}", "path": "ratings"})
    invalid_ratings = [name for name, value in ratings.items() if name in COACH_ROLES.get(role, ()) and not isinstance(value, (int, float)) or isinstance(value, (int, float)) and not 0 <= value <= 5]
    if invalid_ratings:
        issues.append({"code": "COACH-EVAL-RATING", "message": "Ratings must be numeric values from 0 through 5", "path": "ratings"})
    if not evidence:
        issues.append({"code": "COACH-EVAL-EVIDENCE", "message": "Evaluation requires observable evidence", "path": "evidence"})
    return {
        "id": evaluation_id, "coach_id": coach_id, "role": role, "ratings": ratings,
        "evidence": evidence, "evaluator": evaluator,
        "status": "invalid" if issues else "under_review", "human_review_required": True, "issues": issues,
    }
