import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_knowledge_claim, validate_source


def source(tier="tier_3_primary_observation"):
    return {"id": "SOURCE-001", "tier": tier, "kind": "film", "ref": "FILM-001", "captured_at": "2026-08-23"}


class KnowledgeTests(unittest.TestCase):
    def test_source_validation_requires_registered_tier_and_metadata(self):
        self.assertEqual(validate_source(source()), [])
        self.assertTrue(validate_source({"id": "SOURCE-2", "tier": "unknown"}))

    def test_claim_preserves_classification_sources_context_and_uncertainty(self):
        claim = build_knowledge_claim(
            claim_id="CLAIM-001", claim="Observed contextual tendency", classification="observed_tendency",
            sources=[source()], team="TEAM-A", situations=["third_and_medium"], confidence="moderate",
            uncertainty=["small sample"],
        )
        self.assertEqual(claim["status"], "draft")
        self.assertEqual(claim["source_refs"], ["SOURCE-001"])
        self.assertEqual(claim["classification"], "observed_tendency")

    def test_high_impact_claim_requires_authoritative_or_team_locked_source(self):
        claim = build_knowledge_claim(
            claim_id="CLAIM-002", claim="High-impact recommendation basis", classification="contextual_principle",
            sources=[source()], team="TEAM-A", situations=["game_plan"], confidence="high",
            uncertainty=["requires review"], high_impact=True,
        )
        self.assertEqual(claim["status"], "rejected")
        self.assertEqual(claim["issues"][0]["code"], "CLAIM-HIGH-IMPACT-SOURCE")

    def test_team_locked_source_can_support_high_impact_claim(self):
        claim = build_knowledge_claim(
            claim_id="CLAIM-003", claim="Team rule claim", classification="team_rule",
            sources=[source("tier_2_team_locked")], team="TEAM-A", situations=["playbook"], confidence="high",
            uncertainty=["owner approval required"], high_impact=True,
        )
        self.assertEqual(claim["status"], "draft")


if __name__ == "__main__":
    unittest.main()
