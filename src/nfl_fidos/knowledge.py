"""Source hierarchy and provenance-aware knowledge claims."""

from __future__ import annotations

from typing import Any


SOURCE_TIERS = {
    "tier_1_authoritative": 1,
    "tier_2_team_locked": 2,
    "tier_3_primary_observation": 3,
    "tier_4_analytical_research": 4,
    "tier_5_secondary_commentary": 5,
}

CLAIM_TYPES = {"fact", "rule", "team_rule", "observed_tendency", "coaching_preference", "contextual_principle", "hypothesis"}


def validate_source(source: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if source.get("tier") not in SOURCE_TIERS:
        issues.append({"code": "SOURCE-TIER", "message": "Source tier is not registered", "path": "tier"})
    for field in ("id", "kind", "ref", "captured_at"):
        if not source.get(field):
            issues.append({"code": "SOURCE-REQUIRED", "message": f"Source requires {field}", "path": field})
    return issues


def build_knowledge_claim(
    *,
    claim_id: str,
    claim: str,
    classification: str,
    sources: list[dict[str, Any]],
    team: str,
    situations: list[str],
    confidence: str,
    uncertainty: list[str],
    high_impact: bool = False,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not claim_id.startswith("CLAIM-"):
        issues.append({"code": "CLAIM-ID", "message": "Claim id must start with CLAIM-", "path": "claim_id"})
    if classification not in CLAIM_TYPES:
        issues.append({"code": "CLAIM-CLASSIFICATION", "message": "Claim classification is not registered", "path": "classification"})
    if confidence not in {"low", "moderate", "high"}:
        issues.append({"code": "CLAIM-CONFIDENCE", "message": "Claim confidence is invalid", "path": "confidence"})
    if not claim or not team or not situations or not uncertainty or not sources:
        issues.append({"code": "CLAIM-CONTEXT", "message": "Claim, team, situations, uncertainty, and sources are required", "path": "context"})
    for index, source in enumerate(sources):
        issues.extend({**issue, "path": f"sources[{index}].{issue['path']}"} for issue in validate_source(source))
    if high_impact and confidence == "high" and not any(source.get("tier") in {"tier_1_authoritative", "tier_2_team_locked"} for source in sources):
        issues.append({"code": "CLAIM-HIGH-IMPACT-SOURCE", "message": "High-impact high-confidence claim requires authoritative or team-locked source", "path": "sources"})
    return {
        "id": claim_id, "claim": claim, "classification": classification,
        "source_refs": [source.get("id") for source in sources],
        "source_tiers": [source.get("tier") for source in sources],
        "context": {"team": team, "situations": situations},
        "confidence": confidence, "uncertainty": uncertainty,
        "high_impact": high_impact, "status": "rejected" if issues else "draft", "issues": issues,
    }
