import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class AnalyticsOutcomeApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "analytics-outcomes-api-secret"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.service = FootballIntelligenceService(JsonRepository(Path(tempfile.mkdtemp()) / "state.json"))
        analyst = issue_token(subject="ANALYST-OUTCOME", role="analyst", organization_id="ORG-OUTCOME-API", secret=self.secret)
        player = issue_token(subject="PLAYER-OUTCOME", role="player", organization_id="ORG-OUTCOME-API", secret=self.secret)
        self.analyst_headers = {"Authorization": "Bearer " + analyst}
        self.player_headers = {"Authorization": "Bearer " + player}

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_analyst_records_and_reads_outcome_with_lineage(self):
        status, response = handle_request(method="POST", path="/v1/analytics/outcomes", headers=self.analyst_headers, service=self.service, body={
            "organization_id": "ORG-OUTCOME-API", "outcome_id": "OUTCOME-API-1", "intended_record_type": "play_design", "intended_record_id": "PLAY-API-1", "actual_result": "partial", "success_count": 3, "sample_size": 8, "context": {"situation": "red_zone"}, "evidence_refs": ["FILM-OBS-API-1"], "linked_play_id": "PLAY-API-1", "practice_id": "PRACTICE-API-1", "film_observation_ids": ["FILM-OBS-API-1"], "notes": "Execution varied by front.",
        })
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["recorded_by"], "ANALYST-OUTCOME")
        status, response = handle_request(method="GET", path="/v1/analytics/outcomes?organization_id=ORG-OUTCOME-API&intended_record_id=PLAY-API-1", headers=self.analyst_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["total"], 1)
        self.assertEqual(response["data"]["result_counts"]["partial"], 1)
        self.assertFalse(response["data"]["production_implementation_allowed"])

    def test_player_cannot_record_or_read_staff_outcomes(self):
        body = {"organization_id": "ORG-OUTCOME-API", "outcome_id": "OUTCOME-API-2", "intended_record_type": "play_design", "intended_record_id": "PLAY-API-1", "actual_result": "success", "success_count": 1, "sample_size": 1, "context": {"situation": "normal"}, "evidence_refs": ["FILM-1"]}
        self.assertEqual(handle_request(method="POST", path="/v1/analytics/outcomes", headers=self.player_headers, service=self.service, body=body)[0], 403)
        self.assertEqual(handle_request(method="GET", path="/v1/analytics/outcomes?organization_id=ORG-OUTCOME-API", headers=self.player_headers, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
