import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class UsabilityFeedbackApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = "ux-feedback-api-secret"
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.coach_headers = {"Authorization": "Bearer " + issue_token(subject="coach-1", role="coach_staff", organization_id="ORG-1", secret="ux-feedback-api-secret")}
        self.player_headers = {"Authorization": "Bearer " + issue_token(subject="player-1", role="player", organization_id="ORG-1", secret="ux-feedback-api-secret")}
        self.owner_headers = {"Authorization": "Bearer " + issue_token(subject="owner-1", role="program_owner", organization_id="ORG-1", secret="ux-feedback-api-secret")}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_authenticated_role_can_submit_and_governance_can_inspect_feedback(self):
        status, response = handle_request(
            method="POST",
            path="/v1/ux/usability-feedback",
            service=self.service,
            headers=self.coach_headers,
            body={"organization_id":"ORG-1","feedback_id":"UX-FEEDBACK-API-001","session_id":"UX-SESSION-API-001","screen_id":"SCREEN-GOVERNANCE","task_id":"TASK-LOAD-GATE","outcome":"partially_completed","severity":"minor","feedback_text":"The gate explanation needed one more cue.","submitted_at":"2026-08-23T12:00:00Z","evidence_refs":["BROWSER-VALIDATION-LOCAL-001"]},
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["feedback"]["user_role"], "coach_staff")
        status, response = handle_request(method="GET", path="/v1/ux/usability-feedback?organization_id=ORG-1", service=self.service, headers=self.owner_headers)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["feedback"]), 1)
        status, response = handle_request(method="GET", path="/v1/ux/usability-feedback/summary?organization_id=ORG-1", service=self.service, headers=self.owner_headers)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["feedback_count"], 1)
        self.assertEqual(response["data"]["status"], "blocked")

    def test_user_role_is_derived_from_token_and_invalid_screen_is_rejected(self):
        status, response = handle_request(
            method="POST",
            path="/v1/ux/usability-feedback",
            service=self.service,
            headers=self.player_headers,
            body={"organization_id":"ORG-1","feedback_id":"UX-FEEDBACK-API-002","session_id":"UX-SESSION-API-002","screen_id":"SCREEN-MISSING","task_id":"TASK-UNKNOWN","outcome":"completed","severity":"note","feedback_text":"No.","submitted_at":"2026-08-23T12:00:00Z","evidence_refs":["BROWSER-VALIDATION-LOCAL-001"]},
        )
        self.assertEqual(status, 422)
        self.assertEqual(response["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
