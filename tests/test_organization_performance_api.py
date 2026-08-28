import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationPerformanceApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-performance-api-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.staff = {"Authorization": "Bearer " + issue_token(subject="PERF-STAFF-1", role="performance_staff", organization_id="ORG-PERF-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-PERF-API", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-PERF-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_performance_staff_submit_owner_validate_and_staff_read(self):
        body = {"organization_id": "ORG-PERF-API", "package_id": "ORG-PERFORMANCE-API-001", "season": "2026", "batch_id": "PERF-BATCH-API-001", "source_manifest": {"kind": "practice_tracking", "ref": "SOURCE-PRACTICE-001", "captured_at": "2026-08-23T12:00:00Z"}, "records": [{"organization_id": "ORG-PERF-API", "observation_id": "PERF-OBS-API-001", "athlete_id": "PLAYER-1", "session_type": "practice", "duration_minutes": 30, "repetitions": 20, "quality_score": 0.9, "season_phase": "regular_season", "position": "WR", "observed_at": "2026-08-23T10:00:00Z"}], "readiness_summaries": [{"summary_id": "READINESS-API-001", "athlete_id": "PLAYER-1", "signals": ["monitor workload"]}]}
        status, response = handle_request(method="POST", path="/v1/performance/organization-package", body=body, headers=self.staff, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/performance/organization-package/approve", body={"organization_id": "ORG-PERF-API", "package_id": "ORG-PERFORMANCE-API-001", "decision_ref": "DEC-PERF-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        self.assertFalse(response["data"]["medical_decision_performed"])
        status, response = handle_request(method="GET", path="/v1/performance/organization-package?organization_id=ORG-PERF-API", headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/performance/organization-package?organization_id=ORG-PERF-API", headers=self.player, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
