import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class Stage0ApprovalApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = "stage0-api-test-secret"
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.owner_headers = {"Authorization": "Bearer " + issue_token(subject="owner-1", role="program_owner", organization_id="ORG-1", secret="stage0-api-test-secret")}
        self.analyst_headers = {"Authorization": "Bearer " + issue_token(subject="analyst-1", role="analyst", organization_id="ORG-1", secret="stage0-api-test-secret")}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_owner_can_record_non_activating_approval_evidence(self):
        status, response = handle_request(
            method="POST",
            path="/v1/control/stage-0-approval",
            service=self.service,
            headers=self.owner_headers,
            body={
                "organization_id": "ORG-1",
                "approval_id": "APPROVAL-STAGE0-API-001",
                "rationale": "Reviewed the Stage 0 evidence package.",
                "evidence_refs": ["control/stage-0a-registry.json", "control/stage-0-gap-audit.json"],
                "approved_at": "2026-08-23T12:00:00Z",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["validation"]["status"], "valid")
        self.assertFalse(response["data"]["production_implementation_allowed"])
        self.assertFalse(response["data"]["stage_advance_authorized"])

        status, response = handle_request(method="GET", path="/v1/control/stage-0-approval?organization_id=ORG-1", service=self.service, headers=self.owner_headers)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["gate"]["status"], "ready_for_approval")
        self.assertEqual(len(response["data"]["approvals"]), 1)

    def test_non_owner_cannot_submit_stage0_approval(self):
        status, response = handle_request(
            method="POST",
            path="/v1/control/stage-0-approval",
            service=self.service,
            headers=self.analyst_headers,
            body={"organization_id": "ORG-1", "approval_id": "APPROVAL-STAGE0-API-002", "rationale": "No", "evidence_refs": ["x"], "approved_at": "2026-08-23T12:00:00Z"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(response["status"], "error")


if __name__ == "__main__":
    unittest.main()
