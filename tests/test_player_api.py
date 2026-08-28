import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class PlayerApiTests(unittest.TestCase):
    def test_coach_assigns_and_player_reads_only_own_today(self):
        secret = "player-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PLAYER-API", role="coach_staff", organization_id="ORG-PLAYER-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-PLAYER-API", secret=secret)}
        other_player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-2", role="player", organization_id="ORG-PLAYER-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PLAYER-API", "assignment_id":"ASSIGNMENT-API-001", "player_id":"PLAYER-1", "title":"Protection", "assignment_type":"playbook", "artifact_id":"PLAY-API-001", "source_refs":["PLAY-API-001"]}
            status, _ = handle_request(method="POST", path="/v1/player/assignments", body=body, headers=coach, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path="/v1/player/today?organization_id=ORG-PLAYER-API&player_id=PLAYER-1", headers=player, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["next_step"]["id"], "ASSIGNMENT-API-001")
            status, _ = handle_request(method="GET", path="/v1/player/today?organization_id=ORG-PLAYER-API&player_id=PLAYER-1", headers=other_player, service=service)
            self.assertEqual(status, 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
