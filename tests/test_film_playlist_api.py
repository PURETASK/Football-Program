import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class FilmPlaylistApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.directory.name) / "state.json"))
        self.secret = "playlist-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PLAYLIST", role="coach_staff", organization_id="ORG-PLAYLIST", secret=self.secret)}
        self.player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-PLAYLIST", role="player", organization_id="ORG-PLAYLIST", secret=self.secret)}
        self.service.repository.put("film_clips", "CLIP-PLAYLIST-001", {"id":"CLIP-PLAYLIST-001", "organization_id":"ORG-PLAYLIST", "status":"ready"}, actor="seed", reason="test_seed")

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        self.directory.cleanup()

    def test_playlist_is_persisted_and_role_filtered(self):
        status, payload = handle_request(method="POST", path="/v1/film/playlists", service=self.service, headers=self.coach, body={"organization_id":"ORG-PLAYLIST", "playlist_id":"PLAYLIST-001", "name":"Third down", "purpose":"teaching", "clip_ids":["CLIP-PLAYLIST-001"], "filters":{"situation":"third_down"}, "access_roles":["coach_staff"]})
        self.assertEqual(status, 201)
        self.assertEqual(payload["data"]["organization_id"], "ORG-PLAYLIST")
        status, payload = handle_request(method="GET", path="/v1/film/playlists?organization_id=ORG-PLAYLIST", service=self.service, headers=self.coach)
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]["playlists"]), 1)
        status, _ = handle_request(method="GET", path="/v1/film/playlists?organization_id=ORG-PLAYLIST", service=self.service, headers=self.player)
        self.assertEqual(status, 403)

    def test_unknown_clip_and_cross_org_access_are_blocked(self):
        status, _ = handle_request(method="POST", path="/v1/film/playlists", service=self.service, headers=self.coach, body={"organization_id":"ORG-PLAYLIST", "playlist_id":"PLAYLIST-002", "name":"Bad", "purpose":"teaching", "clip_ids":["CLIP-OTHER"], "filters":{}, "access_roles":["coach_staff"]})
        self.assertEqual(status, 422)
        other = {"Authorization": "Bearer " + issue_token(subject="COACH-OTHER", role="coach_staff", organization_id="ORG-OTHER", secret=self.secret)}
        status, _ = handle_request(method="GET", path="/v1/film/playlists?organization_id=ORG-PLAYLIST", service=self.service, headers=other)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
