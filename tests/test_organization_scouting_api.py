import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationScoutingApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-scouting-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-1", role="analyst", organization_id="ORG-SCOUT-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-SCOUT-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-SCOUT-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_analyst_submit_owner_validate_and_team_read(self):
        body = {"organization_id": "ORG-SCOUT-API", "package_id": "ORG-SCOUT-API-001", "opponent": "TEAM-OPP-API", "season": "2026", "source_refs": ["AUTH-SOURCE-001"], "profile": {"id": "OPP-PROFILE-API-001", "schedule_context": {"week": 1}, "roster_context": {"status": "review"}, "offense": {"status": "review"}, "defense": {"status": "review"}, "special_teams": {"status": "review"}, "sources": [{"kind": "team_film", "ref": "AUTH-SOURCE-001", "captured_at": "2026-08-23T00:00:00Z"}]}, "reports": [{"id": "SCOUT-REPORT-API-001", "situation": {"down": 3}, "claims": [{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample"], "evidence_refs": ["AUTH-SOURCE-001"]}], "sample_size": 4, "source_refs": ["AUTH-SOURCE-001"]}], "matchups": [], "evolutions": []}
        status, response = handle_request(method="POST", path="/v1/scouting/organization-package", body=body, headers=self.analyst, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/scouting/organization-package/approve", body={"organization_id": "ORG-SCOUT-API", "package_id": "ORG-SCOUT-API-001", "decision_ref": "DEC-SCOUT-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/scouting/organization-package?organization_id=ORG-SCOUT-API", headers=self.analyst, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/scouting/organization-package?organization_id=ORG-SCOUT-API", headers=self.player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
