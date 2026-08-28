"""Validation for the broader synthetic evaluation scenario corpus."""

from __future__ import annotations

from typing import Any


REQUIRED_DOMAINS = {"football_fact_correctness", "NFL_rule_authority", "scheme_consistency_and_legality", "terminology_consistency", "evidence_and_citations", "nuance_and_contradiction", "safety_and_professional_boundaries", "agent_handoffs", "structured_output_and_data_quality", "regression_and_calibration", "permissions_and_tenancy", "auditability_and_observability"}
REQUIRED_FIELDS = ("id", "domain", "input_class", "expected_outcome", "failure_action", "human_review_required", "source_ref")
OUTCOMES = {"pass_with_citation", "pass_with_caveat", "review_required", "reject", "escalate"}


def validate_evaluation_scenario_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    scenarios = corpus.get("scenarios", [])
    seen: set[str] = set()
    domains: set[str] = set()
    for index, scenario in enumerate(scenarios):
        prefix = f"scenarios[{index}]"
        for field in REQUIRED_FIELDS:
            if field not in scenario or scenario[field] in (None, ""):
                errors.append(f"{prefix}: missing {field}")
        scenario_id = scenario.get("id")
        if scenario_id in seen:
            errors.append(f"{prefix}: duplicate id {scenario_id}")
        seen.add(scenario_id)
        domain = scenario.get("domain")
        domains.add(domain)
        if domain not in REQUIRED_DOMAINS:
            errors.append(f"{prefix}: unsupported domain {domain}")
        if scenario.get("expected_outcome") not in OUTCOMES:
            errors.append(f"{prefix}: unsupported expected outcome")
        if not str(scenario.get("source_ref", "")).startswith("VALIDATION-"):
            errors.append(f"{prefix}: source_ref must be explicitly labeled VALIDATION-")
        if scenario.get("failure_action") not in {"block_promotion", "require_review"}:
            errors.append(f"{prefix}: unsupported failure action")
        if scenario.get("expected_outcome") in {"review_required", "escalate", "pass_with_caveat"} and scenario.get("human_review_required") is not True:
            errors.append(f"{prefix}: nuanced outcome requires human review")
    errors.extend(f"missing required evaluation domain: {domain}" for domain in sorted(REQUIRED_DOMAINS - domains))
    if not corpus.get("corpus_id") or not corpus.get("version") or not corpus.get("purpose"):
        errors.append("corpus identity and purpose are required")
    if corpus.get("status") != "validation_fixture":
        errors.append("corpus status must remain validation_fixture")
    return {"corpus_id": corpus.get("corpus_id"), "status": "valid" if not errors else "invalid", "errors": errors, "scenario_count": len(scenarios), "domain_count": len(domains), "domains": sorted(domains)}
