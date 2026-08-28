import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class AgentRuntimeApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "agent-api-test-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.root = Path(tempfile.mkdtemp())
        self.service = FootballIntelligenceService(JsonRepository(self.root / "state.json"))
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-AGENT-API", role="program_owner", organization_id="ORG-AGENT-API", secret=self.secret)}
        self.validator = {"Authorization": "Bearer " + issue_token(subject="VALIDATOR-AGENT-API", role="validator", organization_id="ORG-AGENT-API", secret=self.secret)}
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-AGENT-API", role="coach_staff", organization_id="ORG-AGENT-API", secret=self.secret)}

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def body(self, run_id="RUN-API-001"):
        return {
            "organization_id": "ORG-AGENT-API",
            "run_id": run_id,
            "agent_id": "AGT-007",
            "family": "validation",
            "capability": "validate",
            "workflow_id": "WF-API-001",
            "payload": {"play_id": "PLAY-API-001", "rule_context": "local"},
            "local_validation": True,
            "requested_permissions": ["validate"],
        }

    def test_owner_can_dispatch_local_validation_and_read_it_back(self):
        status, response = handle_request(method="POST", path="/v1/agents/runs", body=self.body(), headers=self.owner, service=self.service)
        self.assertEqual(status, 201)
        run = response["data"]["run"]
        self.assertEqual(run["status"], "completed")
        self.assertTrue(response["data"]["local_validation_only"])
        self.assertFalse(response["data"]["external_provider_called"])
        self.assertFalse(response["data"]["canonical_write_performed"])
        self.assertFalse(response["data"]["production_implementation_allowed"])
        status, response = handle_request(method="GET", path="/v1/agents/runs?organization_id=ORG-AGENT-API", headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["runs"]), 1)

    def test_validator_is_allowed_but_coach_and_non_local_requests_are_blocked(self):
        status, _ = handle_request(method="POST", path="/v1/agents/runs", body=self.body("RUN-API-002"), headers=self.validator, service=self.service)
        self.assertEqual(status, 201)
        blocked = self.body("RUN-API-003")
        blocked["local_validation"] = False
        self.assertEqual(handle_request(method="POST", path="/v1/agents/runs", body=blocked, headers=self.owner, service=self.service)[0], 403)
        self.assertEqual(handle_request(method="POST", path="/v1/agents/runs", body=self.body("RUN-API-004"), headers=self.coach, service=self.service)[0], 403)

    def test_agent_api_enforces_organization_scope(self):
        other = self.body("RUN-API-005")
        other["organization_id"] = "ORG-OTHER"
        self.assertEqual(handle_request(method="POST", path="/v1/agents/runs", body=other, headers=self.owner, service=self.service)[0], 403)
        self.assertEqual(handle_request(method="GET", path="/v1/agents/runs?organization_id=ORG-OTHER", headers=self.owner, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
