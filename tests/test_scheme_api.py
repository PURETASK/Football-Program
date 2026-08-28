import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class SchemeApiTests(unittest.TestCase):
    def test_coach_saves_and_reviews_compositional_scheme(self):
        secret = "scheme-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-SCHEME-API", role="coach_staff", organization_id="ORG-SCHEME-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-SCHEME-API", role="player", organization_id="ORG-SCHEME-API", secret=secret)}
        scheme = {"id":"SCHEME-API-001", "version":"0.1.0", "unit":"offense", "name":"API offense", "components":[{"id":"C-1", "kind":"personnel", "label":"11 personnel"},{"id":"C-2", "kind":"formation", "label":"shotgun"},{"id":"C-3", "kind":"concept", "label":"inside_zone"}], "assignments":[{"role":"QB", "responsibility":"read"}], "constraints":[], "source":{"kind":"team_playbook", "ref":"PB-API-1"}}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/schemes", body={"organization_id":"ORG-SCHEME-API", "scheme":scheme}, headers=coach, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["status"], "validated")
            status, payload = handle_request(method="GET", path="/v1/schemes/workspace?organization_id=ORG-SCHEME-API&unit=offense", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(len(payload["data"]["schemes"]), 1)
            self.assertEqual(handle_request(method="GET", path="/v1/schemes/workspace?organization_id=ORG-SCHEME-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
