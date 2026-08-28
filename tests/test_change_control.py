import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import approve_change_request, build_change_request, build_decision_record


class ChangeControlTests(unittest.TestCase):
    def test_decision_record_requires_rationale_and_alternatives(self):
        decision = build_decision_record(
            decision_id="DEC-001", title="Adopt ontology alias rule", decision="Require team aliases to map to canonical terms",
            owner="program-owner", rationale="Protect shared semantics", alternatives=["Allow free-text aliases"], affected_ids=["CAP-022"],
        )
        self.assertEqual(decision["status"], "proposed")
        self.assertEqual(decision["affected_ids"], ["CAP-022"])

    def test_change_request_requires_impact_analysis(self):
        request = build_change_request(
            request_id="CR-001", title="Change terminology policy", requester="coach-1", change_type="terminology",
            description="Add a locked team alias", impact_scope="team context", dependencies=["OBJ-004"], risks=["RISK-013"], roadmap_effect="Update Stage 2 artifacts", affected_ids=["TERM-FORMATION-SHOTGUN"],
        )
        self.assertEqual(request["status"], "under_review")
        self.assertTrue(request["approval_required"])

    def test_change_request_approval_creates_decision_link(self):
        request = build_change_request(
            request_id="CR-002", title="Change workflow", requester="owner", change_type="workflow",
            description="Add review step", impact_scope="workflow", dependencies=["WF-001"], risks=["RISK-012"], roadmap_effect="Update Stage 20", affected_ids=["WF-001"],
        )
        approved = approve_change_request(request, approver="program-owner", decision_id="DEC-002")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(approved["decision_id"], "DEC-002")

    def test_draft_request_cannot_be_approved(self):
        request = build_change_request(
            request_id="CR-003", title="Missing impact", requester="owner", change_type="scope",
            description="Change", impact_scope="scope", dependencies=[], risks=[], roadmap_effect="unknown", affected_ids=["CAP-001"],
        )
        rejected = approve_change_request(request, approver="program-owner", decision_id="DEC-003")
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["issues"][0]["code"], "CR-IMPACT")


if __name__ == "__main__":
    unittest.main()
