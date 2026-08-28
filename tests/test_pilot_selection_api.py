import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class PilotSelectionApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "pilot-selection-api-secret"
        self.token = issue_token(subject="owner-pilot", role="program_owner", organization_id="ORG-PILOT-API", secret=self.secret)
        self.headers = {"Authorization": "Bearer " + self.token}

    def test_owner_selects_approved_context_for_non_live_pilot(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET": self.secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            onboarding = {"organization_id":"ORG-PILOT-API", "name":"Pilot Club", "season":"2026", "team_id":"TEAM-PILOT-API", "people":[], "terminology_version":"TERM-0.1.0", "source":{"kind":"team_system", "ref":"ORG-SOURCE-PILOT"}}
            self.assertEqual(handle_request(method="POST", path="/v1/organizations/context", headers=self.headers, body=onboarding, service=service)[0], 201)
            self.assertEqual(handle_request(method="POST", path="/v1/organizations/context/approve", headers=self.headers, body={"organization_id":"ORG-PILOT-API", "decision_ref":"DEC-ORG-PILOT-001"}, service=service)[0], 200)
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-organization", headers=self.headers, body={"organization_id":"ORG-PILOT-API", "selection_id":"PILOT-SEL-API-001", "wave_id":"WAVE-001", "pilot_users":[{"id":"OWNER","role":"program_owner"},{"id":"COACH","role":"coach_staff"},{"id":"ANALYST","role":"analyst"},{"id":"PLAYER","role":"player"}], "decision_ref":"DEC-PILOT-API-001"}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(response["data"]["status"], "selected")
            self.assertFalse(response["data"]["live_pilot"])
            self.assertFalse(response["data"]["production_implementation_allowed"])
            read_status, read_response = handle_request(method="GET", path="/v1/delivery/pilot-organization?organization_id=ORG-PILOT-API", headers=self.headers, service=service)
            self.assertEqual(read_status, 200)
            self.assertEqual(len(read_response["data"]["selections"]), 1)

    def test_selection_requires_active_context_and_owner(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET": self.secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PILOT-API", "selection_id":"PILOT-SEL-API-002", "wave_id":"WAVE-001", "pilot_users":[], "decision_ref":"DEC-PILOT-API-002"}
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-organization", headers=self.headers, body=body, service=service)
            self.assertEqual(status, 409)
            self.assertEqual(response["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
