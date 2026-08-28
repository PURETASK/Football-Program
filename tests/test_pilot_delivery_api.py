import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos import FootballIntelligenceService, JsonRepository, TenantRepository, handle_request
from nfl_fidos.auth import issue_token


class PilotDeliveryApiTests(unittest.TestCase):
    def test_owner_composes_selection_readiness_and_rollback(self):
        secret = "pilot-delivery-secret"
        token = issue_token(subject="OWNER-DELIVERY", role="program_owner", organization_id="ORG-DELIVERY", secret=secret)
        headers = {"Authorization": "Bearer " + token}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            tenant = TenantRepository(service.repository, organization_id="ORG-DELIVERY", actor="OWNER-DELIVERY")
            tenant.put("pilot_selections", "PILOT-SEL-DELIVERY", {"id":"PILOT-SEL-DELIVERY", "organization_id":"ORG-DELIVERY", "wave_id":"WAVE-001", "status":"selected", "live_pilot":False}, actor="OWNER-DELIVERY")
            tenant.put("pilot_readiness_reports", "PILOT-READINESS-DELIVERY", {"id":"PILOT-READINESS-DELIVERY", "organization_id":"ORG-DELIVERY", "wave_id":"WAVE-001", "status":"ready_for_pilot", "feature_flags":{"production_recommendations":False}}, actor="OWNER-DELIVERY")
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-package", headers=headers, body={"organization_id":"ORG-DELIVERY", "package_id":"PILOT-PKG-DELIVERY", "selection_id":"PILOT-SEL-DELIVERY", "readiness_report_id":"PILOT-READINESS-DELIVERY", "rollback":{"status":"passed", "external_state_changed":False, "historical_evidence_preserved":True}}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(response["data"]["status"], "ready_for_bounded_pilot")
            self.assertFalse(response["data"]["live_pilot"])
            self.assertFalse(response["data"]["production_implementation_allowed"])

    def test_package_blocks_failed_rollback(self):
        secret = "pilot-delivery-secret-2"
        token = issue_token(subject="OWNER-DELIVERY", role="program_owner", organization_id="ORG-DELIVERY", secret=secret)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET":secret}, clear=False):
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            tenant = TenantRepository(service.repository, organization_id="ORG-DELIVERY", actor="OWNER-DELIVERY")
            tenant.put("pilot_selections", "PILOT-SEL-DELIVERY", {"id":"PILOT-SEL-DELIVERY", "organization_id":"ORG-DELIVERY", "wave_id":"WAVE-001", "status":"selected"}, actor="OWNER-DELIVERY")
            tenant.put("pilot_readiness_reports", "PILOT-READINESS-DELIVERY", {"id":"PILOT-READINESS-DELIVERY", "organization_id":"ORG-DELIVERY", "wave_id":"WAVE-001", "status":"ready_for_pilot", "feature_flags":{"production_recommendations":False}}, actor="OWNER-DELIVERY")
            status, response = handle_request(method="POST", path="/v1/delivery/pilot-package", headers={"Authorization":"Bearer "+token}, body={"organization_id":"ORG-DELIVERY", "package_id":"PILOT-PKG-DELIVERY-2", "selection_id":"PILOT-SEL-DELIVERY", "readiness_report_id":"PILOT-READINESS-DELIVERY", "rollback":{"status":"failed", "external_state_changed":False}}, service=service)
            self.assertEqual(status, 422)
            self.assertEqual(response["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
