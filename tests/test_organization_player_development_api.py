import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationPlayerDevelopmentApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-player-development-api-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-PLAYER-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-PLAYER-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-PLAYER-API", secret=self.secret)}
        self.other_player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-2", role="player", organization_id="ORG-PLAYER-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_coach_submit_owner_validate_and_player_own_read(self):
        body = {"organization_id": "ORG-PLAYER-API", "package_id": "ORG-PLAYER-DEV-API-001", "team_context": "TEAM-PLAYER-API", "season": "2026", "players": [{"player_id": "PLAYER-1", "position": "QB", "owner": "COACH-1", "objectives": [{"capability_id": "CAP-001", "outcome": "execute assignment", "measure": "4 of 5 reps"}], "mastery_records": []}]}
        status, response = handle_request(method="POST", path="/v1/player-development/organization-package", body=body, headers=self.coach, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/player-development/organization-package/approve", body={"organization_id": "ORG-PLAYER-API", "package_id": "ORG-PLAYER-DEV-API-001", "decision_ref": "DEC-PLAYER-DEV-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/player-development/organization-package?organization_id=ORG-PLAYER-API&player_id=PLAYER-1", headers=self.player, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["packages"][0]["players"][0]["player_id"], "PLAYER-1")
        self.assertEqual(handle_request(method="GET", path="/v1/player-development/organization-package?organization_id=ORG-PLAYER-API&player_id=PLAYER-1", headers=self.other_player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
