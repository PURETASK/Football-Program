import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class GamePlanCollaborationApiTests(unittest.TestCase):
    def test_coach_and_owner_can_review_thread_with_scope(self):
        secret = "game-plan-collaboration-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization":"Bearer "+issue_token(subject="COACH-COLLAB-API", role="coach_staff", organization_id="ORG-COLLAB-API", secret=secret)}
        owner = {"Authorization":"Bearer "+issue_token(subject="OWNER-COLLAB-API", role="program_owner", organization_id="ORG-COLLAB-API", secret=secret)}
        body = {"organization_id":"ORG-COLLAB-API", "thread_id":"GAMEPLAN-THREAD-API-001", "plan_id":"GAMEPLAN-API-001", "week":"WEEK-1", "topic":"third down", "comment":"Review the pressure answer.", "evidence_refs":["CLIP-API-001"]}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, _ = handle_request(method="POST", path="/v1/game-plan/threads", headers=coach, body=body, service=service)
            self.assertEqual(status, 201)
            status, _ = handle_request(method="POST", path="/v1/game-plan/threads/comments", headers=coach, body={"organization_id":"ORG-COLLAB-API","thread_id":"GAMEPLAN-THREAD-API-001","comment_id":"COMMENT-API-002","comment":"Add the simulated pressure note.","evidence_refs":["SCOUT-API-001"]}, service=service)
            self.assertEqual(status, 200)
            status, payload = handle_request(method="POST", path="/v1/game-plan/threads/resolve", headers=owner, body={"organization_id":"ORG-COLLAB-API","thread_id":"GAMEPLAN-THREAD-API-001","decision":"accepted","decision_ref":"DEC-COLLAB-API-001","rationale":"Owner reviewed evidence."}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "resolved")
            status, payload = handle_request(method="GET", path="/v1/game-plan/threads?organization_id=ORG-COLLAB-API", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["open_thread_count"], 0)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
