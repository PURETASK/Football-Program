import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationAnalyticsApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-analytics-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-1", role="analyst", organization_id="ORG-ANALYTICS-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-ANALYTICS-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-ANALYTICS-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_analyst_submit_owner_validate_and_team_read(self):
        definition = {"id": "METRIC-DEF-API-RATE", "name": "API rate", "unit": "rate", "definition": "successes", "required_data": ["play_id"], "formula": "numerator / denominator", "context_dimensions": ["situation"], "caveats": ["sample"], "validation_method": "review", "consumers": ["coach_staff"]}
        body = {"organization_id": "ORG-ANALYTICS-API", "package_id": "ORG-ANALYTICS-API-001", "season": "2026", "source_refs": ["PROVIDER-001"], "observations": [{"observation_id": "METRIC-OBS-API-001", "definition": definition, "numerator": 5, "denominator": 10, "context": {"situation": "red_zone"}, "source_ref": "PROVIDER-001", "observation_ids": ["PLAY-API-1"]}], "reports": [{"id": "ANALYTICS-REPORT-API-001", "audience": "coach_staff", "observation_ids": ["METRIC-OBS-API-001"], "context": {"situation": "red_zone"}, "caveats": ["sample"]}]}
        status, response = handle_request(method="POST", path="/v1/analytics/organization-package", body=body, headers=self.analyst, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/analytics/organization-package/approve", body={"organization_id": "ORG-ANALYTICS-API", "package_id": "ORG-ANALYTICS-API-001", "decision_ref": "DEC-ANALYTICS-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/analytics/organization-package?organization_id=ORG-ANALYTICS-API", headers=self.analyst, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/analytics/organization-package?organization_id=ORG-ANALYTICS-API", headers=self.player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
