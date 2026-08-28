"""Version-aware, non-promoting refresh planning for NFL rule sources."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .rule_sources import validate_rule_source_registry


def _candidate_validation(registry: dict[str, Any]) -> dict[str, Any]:
    candidate = deepcopy(registry)
    statuses = {"proposed", "under_review", "current"}
    issues: list[str] = []
    for source in candidate.get("sources", []):
        if source.get("status") not in statuses:
            issues.append(f"unsupported candidate source status: {source.get('status')}")
        source["status"] = "current"
    result = validate_rule_source_registry(candidate)
    return {"status":"valid" if not issues and result["status"] == "valid" else "invalid", "errors":issues + result["errors"]}


def plan_rule_source_refresh(*, current_registry: dict[str, Any], candidate_registry: dict[str, Any], review_id: str) -> dict[str, Any]:
    issues: list[str] = []
    if not review_id.startswith("RULE-REFRESH-"):
        issues.append("review id must start with RULE-REFRESH-")
    if current_registry.get("jurisdiction") != "NFL" or candidate_registry.get("jurisdiction") != "NFL":
        issues.append("both registries must be NFL-scoped")
    candidate_check = _candidate_validation(candidate_registry)
    issues.extend(candidate_check["errors"])
    current = {source.get("id"):source for source in current_registry.get("sources", [])}
    candidate = {source.get("id"):source for source in candidate_registry.get("sources", [])}
    changes: list[dict[str, Any]] = []
    for source_id in sorted(set(current) | set(candidate)):
        before, after = current.get(source_id), candidate.get(source_id)
        if before is None:
            changes.append({"source_id":source_id, "change":"added", "before":None, "after":after})
        elif after is None:
            changes.append({"source_id":source_id, "change":"removed", "before":before, "after":None})
        elif any(before.get(field) != after.get(field) for field in ("version", "uri", "effective_date", "retrieved_at", "content_sha256")):
            changes.append({"source_id":source_id, "change":"updated", "before":before, "after":after})
    return {
        "id":review_id, "jurisdiction":"NFL", "current_registry_id":current_registry.get("registry_id"), "candidate_registry_id":candidate_registry.get("registry_id"),
        "status":"under_review" if not issues and changes else "no_change" if not issues else "rejected", "changes":changes, "issues":issues,
        "planned_at":datetime.now(timezone.utc).isoformat(), "human_review_required":True, "promotion_allowed":False, "promoted_registry":None,
    }


def approve_rule_source_refresh(review: dict[str, Any], *, approver_role: str, decision_ref: str, candidate_registry: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(review)
    issues = list(result.get("issues", []))
    if result.get("status") != "under_review":
        issues.append("only an under_review refresh can be approved")
    if approver_role != "program_owner":
        issues.append("only program_owner can approve a rule-source refresh")
    if not decision_ref.startswith("DEC-"):
        issues.append("refresh approval requires a DEC-* decision reference")
    if issues:
        result.update({"status":"rejected", "issues":issues, "promotion_allowed":False, "promoted_registry":None})
        return result
    promoted = deepcopy(candidate_registry)
    promoted["status"] = "current"
    promoted["approval_ref"] = decision_ref
    promoted["approved_at"] = datetime.now(timezone.utc).isoformat()
    promoted["approved_by_role"] = approver_role
    result.update({"status":"approved", "issues":[], "decision_ref":decision_ref, "promotion_allowed":False, "promoted_registry":promoted, "human_review_required":True})
    return result
