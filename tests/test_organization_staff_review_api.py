import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationStaffReviewApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-staff-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-STAFF-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-STAFF-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-STAFF-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_coach_submit_owner_validate_and_team_read(self):
        body = {"organization_id": "ORG-STAFF-API", "package_id": "ORG-STAFF-API-001", "team_context": "TEAM-STAFF-API", "season": "2026", "staff": [{"person_id": "STAFF-1", "role": "head_coach", "review_owner": "OWNER-1"}], "evaluations": [{"evaluation_id": "EVAL-COACH-API-001", "coach_id": "STAFF-1", "role": "head_coach", "ratings": {"leadership": 4, "culture": 4, "decision_quality": 3, "staff_alignment": 4, "program_evaluation": 3}, "evidence": [{"source_ref": "AUTH-SOURCE-001", "observation": "review artifact"}], "evaluator": "OWNER-1"}]}
        status, response = handle_request(method="POST", path="/v1/staff/organization-review", body=body, headers=self.coach, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/staff/organization-review/approve", body={"organization_id": "ORG-STAFF-API", "package_id": "ORG-STAFF-API-001", "decision_ref": "DEC-STAFF-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/staff/organization-review?organization_id=ORG-STAFF-API", headers=self.coach, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/staff/organization-review?organization_id=ORG-STAFF-API", headers=self.player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
