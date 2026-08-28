"""Player and coach mastery/individual-development primitives."""

from __future__ import annotations

from typing import Any


MASTERY_LEVELS = ("exposed", "developing", "functional", "proficient", "mastery")


def build_mastery_record(
    *,
    record_id: str,
    learner_id: str,
    capability_id: str,
    current_level: str,
    target_level: str,
    evidence: list[dict[str, Any]],
    next_actions: list[str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not record_id.startswith("MASTERY-"):
        issues.append({"code": "MASTERY-ID", "message": "Mastery id must start with MASTERY-", "path": "record_id"})
    if not learner_id or not capability_id.startswith("CAP-"):
        issues.append({"code": "MASTERY-IDENTITY", "message": "Learner and CAP-* capability are required", "path": "identity"})
    if current_level not in MASTERY_LEVELS or target_level not in MASTERY_LEVELS:
        issues.append({"code": "MASTERY-LEVEL", "message": "Unknown mastery level", "path": "level"})
    elif MASTERY_LEVELS.index(target_level) < MASTERY_LEVELS.index(current_level):
        issues.append({"code": "MASTERY-TARGET", "message": "Target level cannot be below current level", "path": "target_level"})
    if not evidence or not next_actions:
        issues.append({"code": "MASTERY-EVIDENCE", "message": "Evidence and next actions are required", "path": "evidence"})
    return {
        "id": record_id, "learner_id": learner_id, "capability_id": capability_id,
        "current_level": current_level, "target_level": target_level,
        "evidence": evidence, "next_actions": next_actions,
        "review_required": True, "status": "invalid" if issues else "draft", "issues": issues,
    }


def build_development_plan(
    *,
    plan_id: str,
    learner_id: str,
    learner_type: str,
    objectives: list[dict[str, Any]],
    owner: str,
    review_cadence: str,
) -> dict[str, Any]:
    if not plan_id.startswith("IDP-") or learner_type not in {"player", "coach"} or not objectives or not owner or not review_cadence:
        raise ValueError({"code": "IDP-INCOMPLETE", "message": "ID, learner type, objectives, owner, and review cadence are required"})
    incomplete = [index for index, objective in enumerate(objectives) if not objective.get("capability_id") or not objective.get("outcome") or not objective.get("measure")]
    return {
        "id": plan_id, "learner_id": learner_id, "learner_type": learner_type,
        "objectives": objectives, "owner": owner, "review_cadence": review_cadence,
        "status": "under_review" if incomplete else "draft",
        "review_required": True, "issues": [{"code": "IDP-OBJECTIVE", "message": "Objective requires capability, outcome, and measure", "path": f"objectives[{i}]"} for i in incomplete],
    }


def build_coach_mastery_plan(*, plan_id: str, coach_id: str, objectives: list[dict[str, Any]], owner: str) -> dict[str, Any]:
    plan = build_development_plan(plan_id=plan_id, learner_id=coach_id, learner_type="coach", objectives=objectives, owner=owner, review_cadence="weekly")
    plan["capability_id"] = "CAP-004"
    plan["coach_dimensions"] = ["teaching", "evaluation", "scheme_communication", "practice_design", "staff_collaboration"]
    return plan
