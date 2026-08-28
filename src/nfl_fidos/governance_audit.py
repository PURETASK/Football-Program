"""Stage 20 governance matrix and promotion-audit evaluator."""

from __future__ import annotations

from typing import Any


def validate_eval_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    domains = bible.get("risk_domains", [])
    ids: set[str] = set()
    for domain in domains:
        if domain.get("id") in ids:
            issues.append(f"duplicate eval domain: {domain.get('id')}")
        ids.add(domain.get("id"))
        for field in ("id", "name", "risk", "check_type", "failure_action", "owner"):
            if not domain.get(field):
                issues.append(f"{domain.get('id')}: missing {field}")
        if domain.get("risk") not in {"low", "medium", "high", "critical"}:
            issues.append(f"{domain.get('id')}: invalid risk")
    if not bible.get("promotion_requirements") or not bible.get("failure_policy"):
        issues.append("promotion requirements and failure policy are required")
    return {"bible_id":bible.get("bible_id"), "status":"valid" if not issues else "invalid", "errors":issues, "domain_count":len(domains)}


def run_governance_audit(*, audit_id: str, eval_result: dict[str, Any], critical_failures: list[str], safety_failures: list[str], permission_failures: list[str], audit_event_id: str | None, observability_evidence: list[str], human_approval: str | None) -> dict[str, Any]:
    issues: list[str] = []
    if not audit_id.startswith("AUDIT-"):
        issues.append("audit id must start with AUDIT-")
    if eval_result.get("status") != "passed":
        issues.append("named evaluation suite did not pass")
    if critical_failures:
        issues.append(f"critical failures: {critical_failures}")
    if safety_failures:
        issues.append(f"safety failures: {safety_failures}")
    if permission_failures:
        issues.append(f"permission failures: {permission_failures}")
    if not audit_event_id:
        issues.append("audit event evidence is required")
    if not observability_evidence:
        issues.append("observability evidence is required")
    if not human_approval:
        issues.append("human approval evidence is required")
    return {"id":audit_id, "eval_suite_status":eval_result.get("status"), "audit_event_id":audit_event_id, "observability_evidence":observability_evidence, "human_approval":human_approval, "status":"blocked" if issues else "eligible_for_promotion", "promotion_blocked":bool(issues), "issues":issues}
