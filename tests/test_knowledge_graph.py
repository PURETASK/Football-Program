import unittest

from nfl_fidos.knowledge_graph import KnowledgeGraph


class KnowledgeGraphTests(unittest.TestCase):
    def test_graph_preserves_provenance_and_relationships(self):
        graph = KnowledgeGraph(organization_id="ORG-1")
        play = graph.add_node(node_id="PLAY-1", label="third-down play", node_type="play", source_refs=["PB-1"], context={"season":"2026"}, classification="team_rule", confidence="high", state="current")
        pressure = graph.add_node(node_id="THREAT-1", label="pressure look", node_type="tendency", source_refs=["FILM-1"], context={"down":3}, classification="observed_tendency", confidence="moderate", state="current")
        edge = graph.add_edge(edge_id="EDGE-1", from_id="THREAT-1", to_id="PLAY-1", relation="has_answer", source_refs=["FILM-1","PB-1"], context={"situation":"third_down"})
        self.assertTrue(play["canonical_allowed"])
        self.assertTrue(edge["canonical_allowed"])
        self.assertEqual(graph.neighbors("PLAY-1")[0]["node"]["id"], "THREAT-1")

    def test_hypothesis_and_low_confidence_edge_require_review(self):
        graph = KnowledgeGraph(organization_id="ORG-1")
        graph.add_node(node_id="A", label="hypothesis", node_type="claim", source_refs=["OBS-1"], context={"sample":1}, classification="hypothesis", confidence="low", state="proposed")
        graph.add_node(node_id="B", label="concept", node_type="concept", source_refs=["PB-1"], context={"season":"2026"}, classification="fact", confidence="high", state="current")
        edge = graph.add_edge(edge_id="EDGE-2", from_id="A", to_id="B", relation="supports", source_refs=["OBS-1"], context={"sample":1}, confidence="low")
        self.assertFalse(edge["canonical_allowed"])
        reviewed = graph.review_edge(edge_id="EDGE-2", reviewer="COACH-1", decision="reject", reason="insufficient sample")
        self.assertEqual(reviewed["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
