import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class PlaybookWorkspaceApiTests(unittest.TestCase):
    def test_authenticated_authoring_lifecycle(self):
        secret = "playbook-workspace-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization":"Bearer "+issue_token(subject="COACH-PLAYBOOK-API", role="coach_staff", organization_id="ORG-PLAYBOOK-API", secret=secret)}
        owner = {"Authorization":"Bearer "+issue_token(subject="OWNER-PLAYBOOK-API", role="program_owner", organization_id="ORG-PLAYBOOK-API", secret=secret)}
        play = {"id":"PLAY-API-WORKSPACE-001", "version":"0.1.0", "unit":"offense", "status":"draft", "team_context":"TEAM-API", "situation":{"down":1,"distance":10,"field_zone":"open_field"}, "personnel":"11", "formation":"shotgun", "motion":None, "assignments":[{"role":"QB","assignment":"read coverage","responsibility":"read coverage"},{"role":"RB","assignment":"check release","responsibility":"check release"},{"role":"WR1","assignment":"win leverage","responsibility":"win leverage"},{"role":"C","assignment":"set protection","responsibility":"set protection"}], "source":{"kind":"team_playbook","ref":"PB-API-001"}}
        body = {"organization_id":"ORG-PLAYBOOK-API", "play":play, "play_family_id":"PLAY-FAM-API-001", "install_level":"review", "checks":[{"role":"QB","text":"confirm rotation"}], "situational_variants":[], "opponent_notes":[], "coaching_notes":["eyes before feet"], "dependencies":[]}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/playbook/drafts", headers=coach, body=body, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="POST", path="/v1/playbook/drafts/request-approval", headers=coach, body={"organization_id":"ORG-PLAYBOOK-API","play_id":"PLAY-API-WORKSPACE-001","decision_ref":"DEC-API-001"}, service=service)
            self.assertEqual(status, 200)
            status, payload = handle_request(method="POST", path="/v1/playbook/drafts/approve", headers=owner, body={"organization_id":"ORG-PLAYBOOK-API","play_id":"PLAY-API-WORKSPACE-001","decision_ref":"DEC-API-002"}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "locked")
            status, payload = handle_request(method="GET", path="/v1/playbook/workspace?organization_id=ORG-PLAYBOOK-API", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "ready")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
