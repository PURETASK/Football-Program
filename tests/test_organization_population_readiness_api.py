import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationPopulationReadinessApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "population-readiness-api-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.service = FootballIntelligenceService(JsonRepository(Path(tempfile.mkdtemp()) / "state.json"))
        token = issue_token(subject="OWNER-POPULATION-API", role="program_owner", organization_id="ORG-POPULATION-API", secret=self.secret)
        self.headers = {"Authorization": "Bearer " + token}

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_owner_can_inspect_incomplete_population_and_scope_is_enforced(self):
        status, response = handle_request(method="GET", path="/v1/organizations/population-readiness?organization_id=ORG-POPULATION-API&season=2026", headers=self.headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "population_incomplete")
        self.assertEqual(response["data"]["required_component_count"], 13)
        self.assertFalse(response["data"]["activation_performed"])
        self.assertEqual(handle_request(method="GET", path="/v1/organizations/population-readiness?organization_id=ORG-OTHER&season=2026", headers=self.headers, service=self.service)[0], 403)

    def test_season_is_required(self):
        status, _ = handle_request(method="GET", path="/v1/organizations/population-readiness?organization_id=ORG-POPULATION-API", headers=self.headers, service=self.service)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
