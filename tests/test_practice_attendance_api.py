import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class PracticeAttendanceApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "practice-attendance-api-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.service = FootballIntelligenceService(JsonRepository(Path(tempfile.mkdtemp()) / "state.json"))
        owner = issue_token(subject="OWNER-ATTENDANCE", role="program_owner", organization_id="ORG-ATTENDANCE-API", secret=self.secret)
        analyst = issue_token(subject="ANALYST-ATTENDANCE", role="analyst", organization_id="ORG-ATTENDANCE-API", secret=self.secret)
        self.owner_headers = {"Authorization": "Bearer " + owner}
        self.analyst_headers = {"Authorization": "Bearer " + analyst}
        repository = self.service.repository
        repository.put("practice_plans", "PRACTICE-API-1", {"id": "PRACTICE-API-1", "organization_id": "ORG-ATTENDANCE-API", "status": "draft"}, actor="OWNER-ATTENDANCE", reason="fixture")
        repository.put("roster_players", "PLAYER-API-1", {"id": "PLAYER-API-1", "organization_id": "ORG-ATTENDANCE-API", "display_name": "API Player", "position": "QB", "position_group": "QB", "status": "active"}, actor="OWNER-ATTENDANCE", reason="fixture")

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_owner_records_and_analyst_reads_attendance(self):
        status, response = handle_request(method="POST", path="/v1/practice/attendance", headers=self.owner_headers, service=self.service, body={
            "organization_id": "ORG-ATTENDANCE-API", "attendance_id": "ATTENDANCE-API-1", "practice_id": "PRACTICE-API-1", "player_id": "PLAYER-API-1", "status": "present", "recorded_by": "ignored-by-server", "minutes_available": 70,
        })
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["recorded_by"], "OWNER-ATTENDANCE")
        status, response = handle_request(method="GET", path="/v1/practice/attendance?organization_id=ORG-ATTENDANCE-API&practice_id=PRACTICE-API-1", headers=self.analyst_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["counts"]["present"], 1)
        self.assertFalse(response["data"]["production_implementation_allowed"])

    def test_analyst_cannot_record_and_tenant_scope_is_enforced(self):
        status, _ = handle_request(method="POST", path="/v1/practice/attendance", headers=self.analyst_headers, service=self.service, body={"organization_id": "ORG-ATTENDANCE-API", "attendance_id": "ATTENDANCE-API-2", "practice_id": "PRACTICE-API-1", "player_id": "PLAYER-API-1", "status": "present", "recorded_by": "ANALYST-ATTENDANCE"})
        self.assertEqual(status, 403)
        status, _ = handle_request(method="GET", path="/v1/practice/attendance?organization_id=ORG-OTHER", headers=self.owner_headers, service=self.service)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
