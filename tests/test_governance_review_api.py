import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class GovernanceReviewApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "governance-review-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-REVIEW", role="program_owner", organization_id="ORG-REVIEW", secret=self.secret)}
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-REVIEW", role="analyst", organization_id="ORG-REVIEW", secret=self.secret)}
        self.temporary = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temporary.name) / "state.json"))
        self.service.repository.put("game_plans", "GAMEPLAN-REVIEW", {"id":"GAMEPLAN-REVIEW", "organization_id":"ORG-REVIEW", "status":"under_review", "source_refs":["SCOUT-1"]}, actor="COACH", reason="fixture")
        self.service.repository.put("change_requests", "CHANGE-REVIEW", {"id":"CHANGE-REVIEW", "organization_id":"ORG-REVIEW", "status":"under_review", "issues":[], "approval_required":True}, actor="ANALYST", reason="fixture")

    def tearDown(self):
        self.temporary.cleanup()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def review(self, **overrides):
        body = {
            "organization_id":"ORG-REVIEW",
            "collection":"game_plans",
            "record_id":"GAMEPLAN-REVIEW",
            "decision":"returned",
            "decision_ref":"DEC-REVIEW-RETURN-001",
            "rationale":"Add the missing pressure evidence.",
            **overrides,
        }
        return handle_request(method="POST", path="/v1/governance/inbox/review", headers=self.owner, body=body, service=self.service)

    def test_owner_can_return_an_item_and_preserve_decision_evidence(self):
        status, payload = self.review()
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["item"]["status"], "needs_review")
        self.assertEqual(payload["data"]["decision"]["record_id"], "GAMEPLAN-REVIEW")
        self.assertFalse(payload["data"]["canonical_approval_performed"])

    def test_generic_inbox_cannot_bypass_workflow_specific_approval(self):
        status, payload = self.review(decision="approved", decision_ref="DEC-REVIEW-APPROVE-001")
        self.assertEqual(status, 422)
        self.assertIn("applicable workflow endpoint", payload["error"])

    def test_change_request_can_use_its_canonical_approval_primitive(self):
        status, payload = self.review(collection="change_requests", record_id="CHANGE-REVIEW", decision="approved", decision_ref="DEC-REVIEW-CHANGE-001", rationale="Impact and risks were reviewed.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["item"]["status"], "approved")
        self.assertTrue(payload["data"]["canonical_approval_performed"])

    def test_non_owner_cannot_record_a_governance_decision(self):
        body = {"organization_id":"ORG-REVIEW", "collection":"game_plans", "record_id":"GAMEPLAN-REVIEW", "decision":"returned", "decision_ref":"DEC-REVIEW-DENY-001", "rationale":"No authority."}
        status, _ = handle_request(method="POST", path="/v1/governance/inbox/review", headers=self.analyst, body=body, service=self.service)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
