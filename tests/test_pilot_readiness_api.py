import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos import FootballIntelligenceService, handle_request, issue_token
from nfl_fidos.repository import JsonRepository


class PilotReadinessAPITests(unittest.TestCase):
    def test_authenticated_owner_can_evaluate_but_not_activate_pilot(self):
        secret = "p" * 32
        token = issue_token(subject="OWNER-PILOT", role="program_owner", organization_id="ORG-PILOT-API", secret=secret)
        headers = {"Authorization":"Bearer " + token}
        users = [{"id":"OWNER", "role":"program_owner"}, {"id":"COACH", "role":"coach_staff"}, {"id":"ANALYST", "role":"analyst"}, {"id":"PLAYER", "role":"player"}]
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PILOT-API", "wave_id":"WAVE-001", "pilot_users":users, "completed_capabilities":["CAP-004", "CAP-009", "CAP-010", "CAP-011", "CAP-012", "CAP-013", "CAP-021", "CAP-022"], "acceptance_evidence":["TEST-1"], "feature_flags":{"production_recommendations":False}, "rollback_tested":True, "owner_approval":"APPROVAL-PILOT-1"}
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-readiness", headers=headers, body=body, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["status"], "ready_for_pilot")
            self.assertFalse(response["data"]["production_implementation_allowed"])
            self.assertTrue(response["data"]["human_review_required"])
            listed_status, listed = handle_request(method="GET", path="/v1/delivery/pilot-readiness?organization_id=ORG-PILOT-API", headers=headers, service=service)
            self.assertEqual(listed_status, 200)
            self.assertEqual(len(listed["data"]["reports"]), 1)

    def test_non_owner_cannot_supply_owner_approval(self):
        secret = "q" * 32
        token = issue_token(subject="VALIDATOR-PILOT", role="validator", organization_id="ORG-PILOT-API", secret=secret)
        headers = {"Authorization":"Bearer " + token}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PILOT-API", "wave_id":"WAVE-001", "pilot_users":[], "completed_capabilities":[], "acceptance_evidence":[], "feature_flags":{}, "rollback_tested":False, "owner_approval":"FORGED"}
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-readiness", headers=headers, body=body, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["status"], "blocked")
            self.assertIsNone(response["data"]["owner_approval"])


if __name__ == "__main__":
    unittest.main()
