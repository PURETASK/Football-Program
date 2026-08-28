"""Stage 18 versioned NFL rules model and fact/strategy separation."""

from __future__ import annotations

from typing import Any

from .rule_sources import load_authoritative_rule_sources


TOPICS = {"formation_and_eligibility", "timing_and_two_minute", "penalty_enforcement", "kicking_and_possession", "replay_and_challenges", "scoring", "overtime", "fourth_down", "timeouts"}


def validate_rule_knowledge_entry(entry: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("id", "topic", "fact", "applies_when", "exceptions", "not_applies_when", "source", "effective_date"):
        if not entry.get(field) and entry.get(field) != []:
            issues.append({"code":"RULE-KB-REQUIRED", "message":f"Missing rule knowledge field: {field}", "path":field})
    if entry.get("id") and not str(entry["id"]).startswith("RULE-KB-"):
        issues.append({"code":"RULE-KB-ID", "message":"Rule knowledge id must start with RULE-KB-", "path":"id"})
    if entry.get("topic") not in TOPICS:
        issues.append({"code":"RULE-KB-TOPIC", "message":"Unknown rule knowledge topic", "path":"topic"})
    source = entry.get("source", {})
    if source.get("kind") not in {"official_rulebook", "official_interpretation", "team_locked_rule"} or not source.get("ref") or not source.get("retrieved_at"):
        issues.append({"code":"RULE-KB-SOURCE", "message":"Rule knowledge requires an authoritative/versioned source", "path":"source"})
    return issues


def validate_rules_knowledge_model(model: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    try:
        source_registry = load_authoritative_rule_sources()
    except (OSError, ValueError) as exc:
        source_registry = {}
        issues.append(f"authoritative rule-source registry invalid: {exc}")
    ids: set[str] = set()
    for entry in model.get("entries", []):
        if entry.get("id") in ids:
            issues.append(f"duplicate rule knowledge id: {entry.get('id')}")
        ids.add(entry.get("id"))
        issues.extend(f"{entry.get('id')}: {issue['message']}" for issue in validate_rule_knowledge_entry(entry))
        source_ref = entry.get("source", {}).get("ref")
        if source_ref not in source_registry:
            issues.append(f"{entry.get('id')}: source ref is not in the authoritative registry: {source_ref}")
        elif source_registry[source_ref].get("status") != "current":
            issues.append(f"{entry.get('id')}: source is not current: {source_ref}")
    if model.get("jurisdiction") != "NFL":
        issues.append("rules model must be NFL-scoped")
    return {"model_id":model.get("model_id"), "status":"valid" if not issues else "invalid", "errors":issues, "entry_count":len(model.get("entries", [])), "source_registry_valid": bool(source_registry)}


def build_rule_aware_recommendation(*, recommendation_id: str, question: str, rule_facts: list[dict[str, Any]], strategy_recommendation: str, situation: dict[str, Any], requester_role: str, rule_refs: list[str], evidence_refs: list[str]) -> dict[str, Any]:
    issues: list[str] = []
    if not recommendation_id.startswith("RULE-REC-") or not question or not rule_facts or not strategy_recommendation or not situation or not requester_role or not rule_refs:
        issues.append("recommendation requires question, rule facts, strategy, situation, requester, and rule refs")
    invalid_facts = [fact.get("id") for fact in rule_facts if fact.get("authority") not in {"authoritative", "team_locked"}]
    if invalid_facts:
        issues.append(f"rule facts require authoritative or team-locked authority: {invalid_facts}")
    return {"id":recommendation_id, "question":question, "rule_facts":rule_facts, "strategy_recommendation":strategy_recommendation, "situation":situation, "requester_role":requester_role, "rule_refs":rule_refs, "evidence_refs":evidence_refs, "facts_and_strategy_separated":True, "human_review_required":True, "status":"rejected" if issues else "under_review", "issues":issues}
