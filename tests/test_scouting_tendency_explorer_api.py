import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class ScoutingTendencyExplorerApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "scouting-explorer-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-EXPLORER", role="analyst", organization_id="ORG-EXPLORER", secret=self.secret)}
        self.temp = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp.name) / "state.json"))
        self.service.repository.put("scouting_reports", "SCOUT-REPORT-API-1", {"id": "SCOUT-REPORT-API-1", "organization_id": "ORG-EXPLORER", "opponent": "OPP-API", "sample_size": 15, "situation": {"down": 3, "distance": "medium"}, "claims": [{"statement": "Pressure tendency", "stance": "increase", "confidence": "moderate", "evidence_refs": ["FILM-OBS-API-1"]}]}, actor="SEED", reason="fixture")

    def tearDown(self):
        self.temp.cleanup()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_endpoint_returns_filtered_server_result_with_evidence_and_gate(self):
        status, payload = handle_request(method="GET", path="/v1/scouting/tendency-explorer?organization_id=ORG-EXPLORER&opponent=OPP-API&down=3", headers=self.headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["records"][0]["source_clips"], [])
        self.assertEqual(payload["data"]["records"][0]["review_gate"], "ready_for_staff_review")

    def test_endpoint_enforces_tenant_scope(self):
        status, payload = handle_request(method="GET", path="/v1/scouting/tendency-explorer?organization_id=ORG-OTHER", headers=self.headers, service=self.service)
        self.assertEqual(status, 403)
        self.assertEqual(payload["status"], "error")


if __name__ == "__main__":
    unittest.main()
