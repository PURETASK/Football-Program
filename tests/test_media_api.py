import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class MediaApiTests(unittest.TestCase):
    def test_asset_clip_and_scoped_listing_routes(self):
        secret = "media-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        token = issue_token(subject="COACH-MEDIA-API", role="coach_staff", organization_id="ORG-MEDIA-API", secret=secret)
        headers = {"Authorization": f"Bearer {token}"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "game.mp4"
            media.write_bytes(b"media fixture")
            service = FootballIntelligenceService(JsonRepository(root / "state.json"))
            asset_body = {"organization_id":"ORG-MEDIA-API", "file_path":str(media), "asset_id":"FILM-API-MEDIA-001", "duration_seconds":90.0, "source":{"kind":"licensed_film", "ref":"LICENSE-API-001"}, "captured_at":"2026-08-23", "team_context":"TEAM-1", "allowed_roots":[str(root)]}
            status, payload = handle_request(method="POST", path="/v1/media/assets", body=asset_body, headers=headers, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["sha256"] is not None, True)
            clip_body = {"organization_id":"ORG-MEDIA-API", "clip_id":"CLIP-API-MEDIA-001", "asset_id":"FILM-API-MEDIA-001", "start_seconds":5.0, "end_seconds":15.0, "team":"TEAM-1", "opponent":"TEAM-2", "situation":"third_down"}
            status, _ = handle_request(method="POST", path="/v1/media/clips", body=clip_body, headers=headers, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path="/v1/media/clips?organization_id=ORG-MEDIA-API&opponent=TEAM-2", headers=headers, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(len(payload["data"]["clips"]), 1)
            job_body = {"organization_id":"ORG-MEDIA-API", "job_id":"MEDIA-JOB-API-001", "asset_id":"FILM-API-MEDIA-001", "operation":"probe", "payload":{"uri":payload["data"]["clips"][0]["source"]["ref"]}}
            status, _ = handle_request(method="POST", path="/v1/media/jobs", body=job_body, headers=headers, service=service)
            self.assertEqual(status, 201)
            status, _ = handle_request(method="POST", path="/v1/media/jobs/MEDIA-JOB-API-001/claim", body={"organization_id":"ORG-MEDIA-API", "worker_id":"WORKER-API"}, headers=headers, service=service)
            self.assertEqual(status, 200)
            status, payload = handle_request(method="POST", path="/v1/media/jobs/MEDIA-JOB-API-001/complete", body={"organization_id":"ORG-MEDIA-API", "worker_id":"WORKER-API", "output_refs":["META-API-001"]}, headers=headers, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "completed")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
