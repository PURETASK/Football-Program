import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class PerformanceIntegrationApiTests(unittest.TestCase):
    def test_performance_staff_can_submit_provider_batch(self):
        secret = "performance-integration-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        headers = {"Authorization": "Bearer " + issue_token(subject="PERF-STAFF-API", role="performance_staff", organization_id="ORG-PERF-API", secret=secret)}
        body = {
            "organization_id":"ORG-PERF-API",
            "provider":{"kind":"practice_system", "mode":"read_only", "source_ref":"SOURCE-PRACTICE-001"},
            "batch_id":"PERF-BATCH-API-001",
            "records":[{"organization_id":"ORG-PERF-API", "observation_id":"PERF-OBS-API-001", "athlete_id":"PLAYER-API-1", "session_type":"practice", "duration_minutes":30, "repetitions":20, "quality_score":0.9, "season_phase":"regular_season", "position":"WR", "observed_at":"2026-08-23T10:00:00Z"}],
            "source_manifest":{"kind":"practice_tracking", "ref":"SOURCE-PRACTICE-001", "captured_at":"2026-08-23T12:00:00Z"},
        }
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/performance/batches", headers=headers, body=body, service=service)
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["status"], "accepted")
        self.assertFalse(payload["data"]["external_state_changed"])
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
