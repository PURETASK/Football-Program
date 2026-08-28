import unittest

from nfl_fidos.research_protocol import build_research_packet, ingest_knowledge_item, register_research_source, resolve_claim_conflict


class ResearchProtocolTests(unittest.TestCase):
    def source(self, tier="tier_1_authoritative"):
        return register_research_source(source_id="SOURCE-001", tier=tier, kind="official_rulebook", ref="RULEBOOK-1", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="RESEARCH")

    def item(self):
        return ingest_knowledge_item(item_id="KNOWLEDGE-001", question="rule question", source=self.source(), raw_excerpt="source excerpt", normalized_claim="normalized claim", classification="rule", context={"jurisdiction":"NFL"}, ontology_refs=["OBJ-004"], state="current", extractor="AGT-013", confidence="high", uncertainty=["verify exceptions"])

    def test_ingestion_preserves_citation_and_review(self):
        result = self.item()
        self.assertEqual(result["status"], "under_review")
        self.assertTrue(result["canonical_eligible"])
        self.assertEqual(result["citation"]["source_ref"], "RULEBOOK-1")

    def test_conflict_prefers_higher_source_tier_but_is_explicit(self):
        result = resolve_claim_conflict(conflict_id="CONFLICT-001", claims=[{"id":"CLAIM-1","source_tier":"tier_5_secondary_commentary"},{"id":"CLAIM-2","source_tier":"tier_1_authoritative"}], conflict_type="contradiction")
        self.assertEqual(result["resolution"], "preferred_by_source_priority")
        self.assertEqual(result["preferred_claim_id"], "CLAIM-2")

    def test_same_tier_conflict_requires_review(self):
        result = resolve_claim_conflict(conflict_id="CONFLICT-002", claims=[{"id":"CLAIM-1","source_tier":"tier_3_primary_observation"},{"id":"CLAIM-2","source_tier":"tier_3_primary_observation"}], conflict_type="contradiction")
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse(result["canonical_publish_allowed"])

    def test_research_packet_requires_gaps_and_methodology(self):
        result = build_research_packet(packet_id="RESEARCH-PACKET-001", question="q", source_ids=["SOURCE-001"], knowledge_items=[self.item()], methodology=["compare sources"], gaps=["sample"], reviewer="OWNER")
        self.assertEqual(result["status"], "under_review")
