"""Role-scoped usability feedback validation for pilot and deployment review."""

from __future__ import annotations

from datetime import datetime
from typing import Any


ROLES = {"player", "coach_staff", "analyst", "program_owner", "validator", "performance_staff"}
OUTCOMES = {"completed", "partially_completed", "blocked"}
SEVERITIES = {"note", "minor", "major", "critical"}
DISPOSITIONS = {"new", "under_review", "accepted", "rejected"}


def build_usability_feedback(*, feedback_id: str, organization_id: str, session_id: str, user_role: str, screen_id: str, task_id: str, outcome: str, severity: str, feedback_text: str, submitted_at: str, evidence_refs: list[str], accessibility_issue: bool = False, duration_seconds: float | None = None, satisfaction_score: float | None = None) -> dict[str, Any]:
    return {
        "feedback_id": feedback_id,
        "organization_id": organization_id,
        "session_id": session_id,
        "user_role": user_role,
        "screen_id": screen_id,
        "task_id": task_id,
        "outcome": outcome,
        "severity": severity,
        "feedback_text": feedback_text,
        "accessibility_issue": accessibility_issue,
        "duration_seconds": duration_seconds,
        "satisfaction_score": satisfaction_score,
        "submitted_at": submitted_at,
        "evidence_refs": list(evidence_refs),
        "disposition": "new",
    }


def validate_usability_feedback(feedback: dict[str, Any], *, screen_ids: set[str] | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not isinstance(feedback.get("feedback_id"), str) or not feedback["feedback_id"].startswith("UX-FEEDBACK-"):
        issues.append({"code": "UX-FEEDBACK-ID", "message": "feedback_id must use UX-FEEDBACK- prefix", "path": "feedback_id"})
    if not isinstance(feedback.get("organization_id"), str) or not feedback["organization_id"].startswith("ORG-"):
        issues.append({"code": "UX-FEEDBACK-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not isinstance(feedback.get("session_id"), str) or not feedback["session_id"].startswith("UX-SESSION-"):
        issues.append({"code": "UX-FEEDBACK-SESSION", "message": "session_id must use UX-SESSION- prefix", "path": "session_id"})
    if feedback.get("user_role") not in ROLES:
        issues.append({"code": "UX-FEEDBACK-ROLE", "message": "user_role is not a controlled role", "path": "user_role"})
    if not feedback.get("screen_id"):
        issues.append({"code": "UX-FEEDBACK-SCREEN", "message": "screen_id is required", "path": "screen_id"})
    elif screen_ids is not None and feedback["screen_id"] not in screen_ids:
        issues.append({"code": "UX-FEEDBACK-SCREEN", "message": "screen_id is not in the UX screen inventory", "path": "screen_id"})
    if not feedback.get("task_id"):
        issues.append({"code": "UX-FEEDBACK-TASK", "message": "task_id is required", "path": "task_id"})
    if feedback.get("outcome") not in OUTCOMES:
        issues.append({"code": "UX-FEEDBACK-OUTCOME", "message": "outcome is not controlled", "path": "outcome"})
    if feedback.get("severity") not in SEVERITIES:
        issues.append({"code": "UX-FEEDBACK-SEVERITY", "message": "severity is not controlled", "path": "severity"})
    if not isinstance(feedback.get("feedback_text"), str) or not feedback["feedback_text"].strip():
        issues.append({"code": "UX-FEEDBACK-TEXT", "message": "feedback_text is required", "path": "feedback_text"})
    if not isinstance(feedback.get("evidence_refs"), list) or not feedback["evidence_refs"]:
        issues.append({"code": "UX-FEEDBACK-EVIDENCE", "message": "at least one evidence reference is required", "path": "evidence_refs"})
    if feedback.get("duration_seconds") is not None and (not isinstance(feedback.get("duration_seconds"), (int, float)) or feedback.get("duration_seconds") < 0):
        issues.append({"code": "UX-FEEDBACK-DURATION", "message": "duration_seconds must be a non-negative number", "path": "duration_seconds"})
    if feedback.get("satisfaction_score") is not None and (not isinstance(feedback.get("satisfaction_score"), (int, float)) or not 1 <= feedback.get("satisfaction_score") <= 5):
        issues.append({"code": "UX-FEEDBACK-SATISFACTION", "message": "satisfaction_score must be between 1 and 5", "path": "satisfaction_score"})
    if feedback.get("disposition", "new") not in DISPOSITIONS:
        issues.append({"code": "UX-FEEDBACK-DISPOSITION", "message": "disposition is not controlled", "path": "disposition"})
    try:
        datetime.fromisoformat(str(feedback.get("submitted_at", "")).replace("Z", "+00:00"))
    except ValueError:
        issues.append({"code": "UX-FEEDBACK-TIME", "message": "submitted_at must be an ISO-8601 timestamp", "path": "submitted_at"})
    return {"status": "valid" if not issues else "invalid", "feedback_id": feedback.get("feedback_id"), "organization_id": feedback.get("organization_id"), "user_role": feedback.get("user_role"), "screen_id": feedback.get("screen_id"), "outcome": feedback.get("outcome"), "severity": feedback.get("severity"), "issues": issues, "human_review_required": feedback.get("outcome") == "blocked" or feedback.get("severity") in {"major", "critical"} or feedback.get("accessibility_issue") is True}
