import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class RosterWorkspaceApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "roster-workspace-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temporary = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temporary.name) / "state.json"))
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-ROSTER", role="program_owner", organization_id="ORG-ROSTER", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-ROSTER", role="player", organization_id="ORG-ROSTER", secret=self.secret)}

    def tearDown(self):
        self.temporary.cleanup()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_owner_can_create_player_depth_chart_and_personnel_package(self):
        player_body = {"organization_id": "ORG-ROSTER", "player_id": "PLAYER-ROSTER-1", "display_name": "Jordan Example", "position": "WR", "position_group": "wide receivers", "status": "active", "availability": "available", "owner": "OWNER-ROSTER", "source_refs": ["ROSTER-SOURCE-1"], "role_groups": ["X"]}
        status, payload = handle_request(method="POST", path="/v1/roster/players", headers=self.owner, body=player_body, service=self.service)
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["position"], "WR")
        chart = {"organization_id": "ORG-ROSTER", "depth_chart_id": "DEPTH-ROSTER-1", "unit": "offense", "position": "WR", "season": "2026", "slots": [{"rank": 1, "player_id": "PLAYER-ROSTER-1", "role": "starter"}]}
        status, _ = handle_request(method="POST", path="/v1/roster/depth-charts", headers=self.owner, body=chart, service=self.service)
        self.assertEqual(status, 201)
        package = {"organization_id": "ORG-ROSTER", "package_id": "PERSONNEL-ROSTER-1", "name": "11 personnel", "unit": "offense", "roles": ["QB", "RB", "WR", "TE", "OL"], "player_ids": ["PLAYER-ROSTER-1"], "season": "2026"}
        status, _ = handle_request(method="POST", path="/v1/roster/personnel-packages", headers=self.owner, body=package, service=self.service)
        self.assertEqual(status, 201)

    def test_player_read_is_privacy_filtered(self):
        self.service.repository.put("roster_players", "PLAYER-ROSTER-OWN", {"id": "PLAYER-ROSTER-OWN", "organization_id": "ORG-ROSTER", "display_name": "Own Player", "position": "QB", "position_group": "quarterbacks", "status": "active"}, actor="OWNER-ROSTER", reason="fixture")
        self.service.repository.put("roster_players", "PLAYER-OTHER", {"id": "PLAYER-OTHER", "organization_id": "ORG-ROSTER", "display_name": "Other Player", "position": "WR", "position_group": "wide receivers", "status": "active"}, actor="OWNER-ROSTER", reason="fixture")
        status, payload = handle_request(method="GET", path="/v1/roster/workspace?organization_id=ORG-ROSTER", headers=self.player, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual([record["id"] for record in payload["data"]["players"]], [])

        own_player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-ROSTER", role="player", organization_id="ORG-ROSTER", secret=self.secret)}
        self.service.repository.put("roster_players", "PLAYER-ROSTER-OWN", {"id": "PLAYER-ROSTER-OWN", "organization_id": "ORG-ROSTER", "display_name": "Own Player", "player_id": "PLAYER-ROSTER", "position": "QB", "position_group": "quarterbacks", "status": "active", "owner": "PLAYER-ROSTER"}, actor="OWNER-ROSTER", reason="fixture")
        status, payload = handle_request(method="GET", path="/v1/roster/workspace?organization_id=ORG-ROSTER", headers=own_player, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual([record["id"] for record in payload["data"]["players"]], ["PLAYER-ROSTER-OWN"])


if __name__ == "__main__":
    unittest.main()
