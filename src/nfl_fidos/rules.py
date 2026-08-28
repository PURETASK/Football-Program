"""Authoritative rule and game-management boundary primitives."""

from __future__ import annotations

from typing import Any


AUTHORITY_LEVELS = {"authoritative", "team_locked", "secondary"}
JURISDICTIONS = {"NFL", "team", "competition_specific"}


def validate_rule_source(rule: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "jurisdiction", "rule_text", "source", "effective_date", "authority_level"):
        if not rule.get(field):
            issues.append({"code": "RULE-REQUIRED", "message": f"Missing required field: {field}", "path": field})
    if rule.get("id") and not rule["id"].startswith("RULE-"):
        issues.append({"code": "RULE-ID", "message": "Rule id must start with RULE-", "path": "id"})
    if rule.get("jurisdiction") not in JURISDICTIONS:
        issues.append({"code": "RULE-JURISDICTION", "message": "Unknown rule jurisdiction", "path": "jurisdiction"})
    if rule.get("authority_level") not in AUTHORITY_LEVELS:
        issues.append({"code": "RULE-AUTHORITY", "message": "Unknown authority level", "path": "authority_level"})
    source = rule.get("source")
    if not isinstance(source, dict) or not source.get("kind") or not source.get("ref") or not source.get("retrieved_at"):
        issues.append({"code": "RULE-PROVENANCE", "message": "Rule source requires kind, ref, and retrieved_at", "path": "source"})
    return issues


def answer_rule_request(*, request_id: str, question: str, rule: dict[str, Any], requester_role: str) -> dict[str, Any]:
    """Return a source-linked rule answer without inventing an answer when invalid."""
    issues = validate_rule_source(rule)
    if not request_id.startswith("RULE-REQUEST-"):
        issues.append({"code": "RULE-REQUEST-ID", "message": "Request id must start with RULE-REQUEST-", "path": "request_id"})
    if not question.strip():
        issues.append({"code": "RULE-QUESTION", "message": "Question is required", "path": "question"})
    answer_status = "escalate" if issues or rule.get("authority_level") == "secondary" else "answered"
    return {
        "id": request_id,
        "question": question,
        "answer": rule.get("rule_text") if answer_status == "answered" else None,
        "rule_id": rule.get("id"),
        "requester_role": requester_role,
        "jurisdiction": rule.get("jurisdiction"),
        "source": rule.get("source"),
        "effective_date": rule.get("effective_date"),
        "status": answer_status,
        "human_escalation_required": answer_status == "escalate",
        "issues": issues,
    }
