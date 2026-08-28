import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class GamePlanApiTests(unittest.TestCase):
    def test_coach_can_read_scoped_game_plan_workspace(self):
        secret = "game-plan-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PLAN-API", role="coach_staff", organization_id="ORG-PLAN-API", secret=secret)}
        analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-PLAN-API", role="analyst", organization_id="ORG-PLAN-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-PLAN-API", role="player", organization_id="ORG-PLAN-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("game_plans", "GAMEPLAN-API", {"id":"GAMEPLAN-API", "organization_id":"ORG-PLAN-API", "week":"WEEK-1", "status":"under_review"}, actor="COACH-PLAN-API", reason="fixture")
            status, payload = handle_request(method="GET", path="/v1/game-plan/workspace?organization_id=ORG-PLAN-API&week=WEEK-1", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["plans"][0]["id"], "GAMEPLAN-API")
            self.assertEqual(handle_request(method="GET", path="/v1/game-plan/workspace?organization_id=ORG-OTHER", headers=analyst, service=service)[0], 403)
            self.assertEqual(handle_request(method="GET", path="/v1/game-plan/workspace?organization_id=ORG-PLAN-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
