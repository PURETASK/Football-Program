import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationDoctrineApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-doctrine-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-DOCTRINE-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-DOCTRINE-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-DOCTRINE-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_coach_submit_owner_validate_and_team_read(self):
        body = {"organization_id": "ORG-DOCTRINE-API", "doctrine_id": "ORG-DOCTRINE-API-001", "team_context": "TEAM-DOCTRINE-API", "season": "2026", "scheme_family_ids": ["SCHEME-FAM-OFF-001", "SCHEME-FAM-DEF-001"], "special_teams_unit_ids": ["ST-UNIT-001"], "source_refs": ["AUTH-SOURCE-001"]}
        status, response = handle_request(method="POST", path="/v1/schemes/organization-doctrine", body=body, headers=self.coach, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/schemes/organization-doctrine/approve", body={"organization_id": "ORG-DOCTRINE-API", "doctrine_id": "ORG-DOCTRINE-API-001", "decision_ref": "DEC-DOCTRINE-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        self.assertFalse(response["data"]["production_implementation_allowed"])
        status, response = handle_request(method="GET", path="/v1/schemes/organization-doctrine?organization_id=ORG-DOCTRINE-API", headers=self.coach, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/schemes/organization-doctrine?organization_id=ORG-DOCTRINE-API", headers=self.player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
