import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class AnalyticsApiTests(unittest.TestCase):
    def test_analyst_creates_and_reviews_lineage_report(self):
        secret = "analytics-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-API", role="analyst", organization_id="ORG-ANALYTICS-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-API", role="player", organization_id="ORG-ANALYTICS-API", secret=secret)}
        observation = {"id":"METRIC-OBS-API-001", "metric_id":"METRIC-DEF-001", "numerator":6, "denominator":10, "rate":0.6, "confidence":"moderate", "uncertainty":{"method":"wilson", "interval":[0.3,0.8]}, "context":{"situation":"third_down"}, "source":{"kind":"charting", "ref":"FILM-API-1"}, "observation_ids":["PLAY-API-1"], "status":"valid"}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-ANALYTICS-API", "report_id":"ANALYTICS-REPORT-API-001", "audience":"coach_staff", "metric_observations":[observation], "context":{"situation":"third_down"}, "caveats":["sample only"]}
            status, payload = handle_request(method="POST", path="/v1/analytics/reports", body=body, headers=analyst, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["status"], "draft")
            status, payload = handle_request(method="GET", path="/v1/analytics/workspace?organization_id=ORG-ANALYTICS-API&situation=third_down", headers=analyst, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["lineage_complete_count"], 1)
            self.assertEqual(handle_request(method="GET", path="/v1/analytics/workspace?organization_id=ORG-ANALYTICS-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
