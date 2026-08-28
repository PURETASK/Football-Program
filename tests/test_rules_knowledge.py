import json
import unittest
from pathlib import Path

from nfl_fidos.rules_knowledge import build_rule_aware_recommendation, validate_rules_knowledge_model
from nfl_fidos.rule_sources import load_authoritative_rule_sources, validate_rule_source_registry


class RulesKnowledgeTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "rules" / "rules-knowledge-model.json"
        self.model = json.loads(path.read_text(encoding="utf-8"))

    def test_rule_model_is_versioned_and_nfl_scoped(self):
        result = validate_rules_knowledge_model(self.model)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["entry_count"], 5)
        self.assertTrue(result["source_registry_valid"])

    def test_authoritative_source_registry_is_official_and_current(self):
        sources = load_authoritative_rule_sources()
        self.assertIn("NFL-RULEBOOK-VERSIONED", sources)
        self.assertEqual(sources["NFL-RULEBOOK-VERSIONED"]["authority"], "official_nfl")
        self.assertEqual(validate_rule_source_registry({"jurisdiction":"NFL", "sources":list(sources.values())})["status"], "valid")

    def test_non_official_rule_source_is_rejected(self):
        bad = {"jurisdiction":"NFL", "sources":[{"id":"BAD", "title":"copy", "authority":"secondary", "kind":"official_rulebook", "version":"2026", "uri":"https://example.com/rules", "allowed_domain":"example.com", "retrieved_at":"2026-08-23", "effective_date":"2026-01-01", "status":"current"}]}
        self.assertEqual(validate_rule_source_registry(bad)["status"], "invalid")

    def test_recommendation_separates_rule_facts_and_strategy(self):
        result = build_rule_aware_recommendation(recommendation_id="RULE-REC-001", question="fourth down", rule_facts=[{"id":"RULE-KB-005","authority":"authoritative","fact":"rule fact"}], strategy_recommendation="compare options", situation={"down":4,"distance":2,"clock":90}, requester_role="coach_staff", rule_refs=["RULE-KB-005"], evidence_refs=["DATA-1"])
        self.assertEqual(result["status"], "under_review")
        self.assertTrue(result["facts_and_strategy_separated"])
        self.assertTrue(result["human_review_required"])

    def test_secondary_fact_is_rejected(self):
        result = build_rule_aware_recommendation(recommendation_id="RULE-REC-002", question="x", rule_facts=[{"id":"RULE-KB-1","authority":"secondary","fact":"x"}], strategy_recommendation="x", situation={"down":1}, requester_role="coach", rule_refs=["RULE-KB-1"], evidence_refs=[])
        self.assertEqual(result["status"], "rejected")
