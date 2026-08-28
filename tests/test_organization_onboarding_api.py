import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos import FootballIntelligenceService, handle_request, issue_token
from nfl_fidos.repository import JsonRepository


class OrganizationOnboardingAPITests(unittest.TestCase):
    def test_program_owner_can_register_context_and_read_it_back(self):
        secret = "o" * 32
        token = issue_token(subject="OWNER-ORG", role="program_owner", organization_id="ORG-ONBOARD-API", secret=secret)
        headers = {"Authorization":"Bearer " + token}
        body = {"organization_id":"ORG-ONBOARD-API", "name":"Evaluation Club", "season":"2026", "team_id":"TEAM-ONBOARD-API", "people":[{"id":"PLAYER-1", "name":"Player One", "type":"player", "position":"QB"}], "terminology_version":"TERM-0.1.0", "source":{"kind":"team_system", "ref":"ORG-SOURCE-API"}}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, response = handle_request(method="POST", path="/v1/organizations/context", headers=headers, body=body, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(response["data"]["organization"]["status"], "draft")
            read_status, read_response = handle_request(method="GET", path="/v1/organizations/context?organization_id=ORG-ONBOARD-API", headers=headers, service=service)
            self.assertEqual(read_status, 200)
            self.assertEqual(len(read_response["data"]["contexts"]), 1)
            self.assertEqual(len(read_response["data"]["terminology_bundles"]), 1)
            approve_status, approve_response = handle_request(method="POST", path="/v1/organizations/context/approve", headers=headers, body={"organization_id":"ORG-ONBOARD-API", "decision_ref":"DEC-ORG-API-001"}, service=service)
            self.assertEqual(approve_status, 200)
            self.assertEqual(approve_response["data"]["organization"]["status"], "active")
            self.assertFalse(approve_response["data"]["production_implementation_allowed"])

    def test_non_owner_cannot_register_context(self):
        secret = "n" * 32
        token = issue_token(subject="COACH-ORG", role="coach_staff", organization_id="ORG-ONBOARD-API", secret=secret)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, _ = handle_request(method="POST", path="/v1/organizations/context", headers={"Authorization":"Bearer " + token}, body={"organization_id":"ORG-ONBOARD-API"}, service=service)
            self.assertEqual(status, 400)
            body = {"organization_id":"ORG-ONBOARD-API", "name":"Evaluation Club", "season":"2026", "team_id":"TEAM-ONBOARD-API", "people":[], "terminology_version":"TERM-0.1.0", "source":{"kind":"team_system", "ref":"ORG-SOURCE-API"}}
            status, _ = handle_request(method="POST", path="/v1/organizations/context", headers={"Authorization":"Bearer " + token}, body=body, service=service)
            self.assertEqual(status, 403)
            self.assertEqual(handle_request(method="POST", path="/v1/organizations/context/approve", headers={"Authorization":"Bearer " + token}, body={"organization_id":"ORG-ONBOARD-API", "decision_ref":"DEC-ORG-API-001"}, service=service)[0], 403)


if __name__ == "__main__":
    unittest.main()
