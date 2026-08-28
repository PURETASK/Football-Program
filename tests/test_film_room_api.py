import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.film_intelligence import build_film_observation
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class FilmRoomApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "film-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.token = issue_token(subject="COACH-API", role="coach_staff", organization_id="ORG-API", secret=self.secret)
        self.analyst_token = issue_token(subject="ANALYST-API", role="analyst", organization_id="ORG-API", secret=self.secret)
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.analyst_headers = {"Authorization": f"Bearer {self.analyst_token}"}
        self.temp = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp.name) / "state.json"))

    def tearDown(self):
        self.temp.cleanup()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def observation(self):
        record = build_film_observation(
            observation_id="FILM-OBS-API-001", clip_id="CLIP-API-001", asset_id="FILM-API-001",
            domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2",
            situation={"down": 3}, source_frame="00:00:02.000", confidence="moderate",
            observed_or_inferred="observed", annotator="COACH-API", evidence="rotation visible",
        )
        record["organization_id"] = "ORG-API"
        return record

    def test_observation_can_be_saved_and_searched_with_org_scope(self):
        status, payload = handle_request(method="POST", path="/v1/film/observations", headers=self.analyst_headers, service=self.service, body={"organization_id":"ORG-API", "observation":self.observation()})
        self.assertEqual(status, 201)
        status, payload = handle_request(method="GET", path="/v1/film/search?organization_id=ORG-API&opponent=TEAM-2", headers=self.analyst_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]["results"]), 1)

    def test_observation_can_link_to_downstream_workspaces(self):
        observation = self.observation()
        observation["linked_record_refs"] = [{"record_type": "scouting", "record_id": "SCOUT-REPORT-1"}, {"record_type": "analytics", "record_id": "OUTCOME-1"}]
        status, payload = handle_request(method="POST", path="/v1/film/observations", headers=self.analyst_headers, service=self.service, body={"organization_id": "ORG-API", "observation": observation})
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["linked_record_refs"][0]["record_type"], "scouting")
        invalid = self.observation()
        invalid["id"] = "FILM-OBS-API-002"
        invalid["linked_record_refs"] = [{"record_type": "unknown", "record_id": "X-1"}]
        status, _ = handle_request(method="POST", path="/v1/film/observations", headers=self.analyst_headers, service=self.service, body={"organization_id": "ORG-API", "observation": invalid})
        self.assertEqual(status, 422)

    def test_quiz_creation_and_attempt_are_persisted(self):
        body = {"organization_id":"ORG-API", "quiz_id":"QUIZ-API-001", "title":"Coverage", "role":"QB", "clip_ids":["CLIP-API-001"], "questions":[{"id":"Q-1", "prompt":"shell", "expected_answer":"two_high", "evidence_refs":["CLIP-API-001"]}]}
        status, _ = handle_request(method="POST", path="/v1/film/quizzes", headers=self.headers, service=self.service, body=body)
        self.assertEqual(status, 201)
        status, payload = handle_request(method="POST", path="/v1/film/quizzes/QUIZ-API-001/attempts", headers=self.headers, service=self.service, body={"organization_id":"ORG-API", "attempt_id":"QUIZ-ATTEMPT-API-001", "participant":"PLAYER-1", "answers":{"Q-1":"two_high"}})
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["score"], 1.0)

    def test_cross_org_search_is_denied(self):
        status, payload = handle_request(method="GET", path="/v1/film/search?organization_id=ORG-OTHER", headers=self.headers, service=self.service)
        self.assertEqual(status, 403)
        self.assertEqual(payload["status"], "error")

    def test_annotation_session_persists_low_confidence_correction_state(self):
        body = {"organization_id":"ORG-API", "session_id":"ANNOTATION-API-001", "clip_id":"CLIP-API-001", "allowed_domains":["coverage"], "source_refs":["CLIP-API-001"]}
        status, payload = handle_request(method="POST", path="/v1/film/annotation-sessions", headers=self.analyst_headers, service=self.service, body=body)
        self.assertEqual(status, 201)
        observation = self.observation()
        observation["confidence"] = "low"
        status, payload = handle_request(method="POST", path="/v1/film/annotation-sessions/ANNOTATION-API-001/annotations", headers=self.analyst_headers, service=self.service, body={"organization_id":"ORG-API", "observation":observation})
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["correction_required"])
        status, payload = handle_request(method="GET", path="/v1/film/annotation-sessions?organization_id=ORG-API", headers=self.analyst_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]["sessions"]), 1)


if __name__ == "__main__":
    unittest.main()
