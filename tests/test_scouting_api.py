import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class ScoutingApiTests(unittest.TestCase):
    def test_analyst_creates_and_reviews_scoped_scouting_report(self):
        secret = "scouting-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SCOUT-API", role="analyst", organization_id="ORG-SCOUT-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-SCOUT-API", role="player", organization_id="ORG-SCOUT-API", secret=secret)}
        report = {"id":"SCOUT-REPORT-API-001", "opponent":"OPP-API", "situation":{"down":3}, "claims":[{"classification":"observed", "confidence":"moderate", "uncertainty":["sample"], "evidence_refs":["CLIP-API"]}], "sample_size":4, "source_refs":["CLIP-API"], "analyst":"ANALYST-SCOUT-API", "status":"under_review"}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/scouting/reports", body={"organization_id":"ORG-SCOUT-API", "report":report}, headers=analyst, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path="/v1/scouting/workspace?organization_id=ORG-SCOUT-API&opponent=OPP-API", headers=analyst, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["low_sample_count"], 1)
            self.assertEqual(handle_request(method="GET", path="/v1/scouting/workspace?organization_id=ORG-SCOUT-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_api_rejects_scouting_claim_without_evidence_metadata(self):
        secret = "scouting-api-invalid-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SCOUT-INVALID", role="analyst", organization_id="ORG-SCOUT-INVALID", secret=secret)}
        report = {"id":"SCOUT-REPORT-INVALID-001", "opponent":"OPP-INVALID", "situation":{"down":3}, "claims":[{"classification":"inferred"}], "sample_size":4, "source_refs":["CLIP-INVALID"]}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/scouting/reports", body={"organization_id":"ORG-SCOUT-INVALID", "report":report}, headers=analyst, service=service)
            self.assertEqual(status, 422)
            self.assertEqual(payload["status"], "invalid")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
