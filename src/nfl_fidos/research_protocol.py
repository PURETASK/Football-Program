"""Stage 19 controlled knowledge ingestion, citation, freshness, and conflict handling."""

from __future__ import annotations

from typing import Any


SOURCE_PRIORITY = {"tier_1_authoritative":1, "tier_2_team_locked":2, "tier_3_primary_observation":3, "tier_4_analytical_research":4, "tier_5_secondary_commentary":5}
CLAIM_STATES = {"current", "historical", "superseded", "unresolved"}


def register_research_source(*, source_id: str, tier: str, kind: str, ref: str, captured_at: str, effective_period: str, citation_location: str, owner: str, authorized: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    if not source_id.startswith("SOURCE-") or tier not in SOURCE_PRIORITY or not kind or not ref or not captured_at or not effective_period or not citation_location or not owner:
        issues.append("source id, tier, kind, reference, timestamps, citation location, and owner are required")
    if not authorized:
        issues.append("source is not authorized for ingestion")
    return {"id":source_id, "tier":tier, "kind":kind, "ref":ref, "captured_at":captured_at, "effective_period":effective_period, "citation_location":citation_location, "owner":owner, "authorized":authorized, "status":"rejected" if issues else "registered", "issues":issues}


def ingest_knowledge_item(*, item_id: str, question: str, source: dict[str, Any], raw_excerpt: str, normalized_claim: str, classification: str, context: dict[str, Any], ontology_refs: list[str], state: str, extractor: str, confidence: str, uncertainty: list[str]) -> dict[str, Any]:
    issues: list[str] = []
    if not item_id.startswith("KNOWLEDGE-") or not question or source.get("status") != "registered" or not raw_excerpt or not normalized_claim or not context or not ontology_refs or not extractor or not uncertainty:
        issues.append("knowledge item requires identity, question, registered source, excerpt, normalized claim, context, ontology refs, extractor, and uncertainty")
    if classification not in {"fact", "rule", "team_rule", "observed_tendency", "coaching_preference", "contextual_principle", "hypothesis"}:
        issues.append("claim classification is invalid")
    if state not in CLAIM_STATES:
        issues.append("claim state is invalid")
    if confidence not in {"low", "moderate", "high"}:
        issues.append("confidence is invalid")
    return {"id":item_id, "question":question, "source_id":source.get("id"), "raw_excerpt":raw_excerpt, "normalized_claim":normalized_claim, "classification":classification, "context":context, "ontology_refs":ontology_refs, "state":state, "extractor":extractor, "confidence":confidence, "uncertainty":uncertainty, "citation":{"source_ref":source.get("ref"), "location":source.get("citation_location"), "captured_at":source.get("captured_at")}, "canonical_eligible":not issues and classification not in {"hypothesis"} and state in {"current", "historical"}, "status":"rejected" if issues else "under_review", "human_review_required":True, "issues":issues}


def resolve_claim_conflict(*, conflict_id: str, claims: list[dict[str, Any]], conflict_type: str, reviewer: str | None = None) -> dict[str, Any]:
    issues: list[str] = []
    if not conflict_id.startswith("CONFLICT-") or len(claims) < 2 or not conflict_type:
        issues.append("conflict requires id, at least two claims, and conflict type")
    tiers = [SOURCE_PRIORITY.get(claim.get("source_tier"), 99) for claim in claims]
    if any(tier == 99 for tier in tiers):
        issues.append("every claim requires a registered source tier")
    winner = None
    resolution = "unresolved"
    if not issues and len(set(tiers)) > 1:
        winner = claims[tiers.index(min(tiers))].get("id")
        resolution = "preferred_by_source_priority"
    elif not issues and reviewer:
        resolution = "human_reviewed"
    return {"id":conflict_id, "claim_ids":[claim.get("id") for claim in claims], "conflict_type":conflict_type, "resolution":resolution, "preferred_claim_id":winner, "reviewer":reviewer, "canonical_publish_allowed":resolution in {"preferred_by_source_priority", "human_reviewed"}, "status":"needs_review" if resolution == "unresolved" else "resolved", "issues":issues}


def build_research_packet(*, packet_id: str, question: str, source_ids: list[str], knowledge_items: list[dict[str, Any]], methodology: list[str], gaps: list[str], reviewer: str) -> dict[str, Any]:
    issues: list[str] = []
    if not packet_id.startswith("RESEARCH-PACKET-") or not question or not source_ids or not knowledge_items or not methodology or not gaps or not reviewer:
        issues.append("research packet requires question, sources, knowledge items, methodology, gaps, and reviewer")
    invalid = [item.get("id") for item in knowledge_items if item.get("status") != "under_review"]
    if invalid:
        issues.append(f"packet contains invalid knowledge items: {invalid}")
    return {"id":packet_id, "question":question, "source_ids":source_ids, "knowledge_item_ids":[item.get("id") for item in knowledge_items], "methodology":methodology, "gaps":gaps, "reviewer":reviewer, "citations_required":True, "status":"invalid" if issues else "under_review", "issues":issues}
