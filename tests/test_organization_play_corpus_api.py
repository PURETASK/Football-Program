import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationPlayCorpusApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-play-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.coach_headers = {"Authorization": "Bearer " + issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-PLAY-API", secret=self.secret)}
        self.owner_headers = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-PLAY-API", secret=self.secret)}
        self.player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-PLAY-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def _play(self):
        return {"id": "PLAY-ORG-API-001", "version": "0.1.0", "unit": "offense", "team_context": "TEAM-ORG-API", "situation": {"down": 1, "distance": 10, "field_zone": "open_field"}, "personnel": "11", "formation": "shotgun", "assignments": [{"role": "QB", "assignment": "read shell"}, {"role": "C", "assignment": "set protection"}], "source": {"kind": "team_playbook", "ref": "AUTH-SOURCE-001"}, "status": "draft"}

    def test_coach_submit_owner_validate_and_team_read(self):
        body = {"organization_id": "ORG-PLAY-API", "corpus_id": "ORG-PLAY-CORPUS-API-001", "team_context": "TEAM-ORG-API", "season": "2026", "plays": [self._play()], "source_refs": ["AUTH-SOURCE-001"]}
        status, response = handle_request(method="POST", path="/v1/playbook/organization-corpus", body=body, headers=self.coach_headers, service=self.service)
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["status"], "under_review")
        status, response = handle_request(method="POST", path="/v1/playbook/organization-corpus/approve", body={"organization_id": "ORG-PLAY-API", "corpus_id": "ORG-PLAY-CORPUS-API-001", "decision_ref": "DEC-PLAY-API-001"}, headers=self.owner_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        self.assertFalse(response["data"]["production_implementation_allowed"])
        status, response = handle_request(method="GET", path="/v1/playbook/organization-corpus?organization_id=ORG-PLAY-API", headers=self.coach_headers, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["corpora"]), 1)
        self.assertEqual(handle_request(method="GET", path="/v1/playbook/organization-corpus?organization_id=ORG-PLAY-API", headers=self.player_headers, service=self.service)[0], 403)


if __name__ == "__main__":
    unittest.main()
