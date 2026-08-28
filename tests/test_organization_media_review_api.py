import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationMediaReviewApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "organization-media-review-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-1", role="analyst", organization_id="ORG-MEDIA-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-MEDIA-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_submit_owner_validate_and_read(self):
        body = {"organization_id":"ORG-MEDIA-API","package_id":"ORG-MEDIA-REVIEW-API-001","season":"2026","assets":[{"id":"FILM-API-001","organization_id":"ORG-MEDIA-API","uri":"file:///api.mp4","sha256":"b"*64,"status":"registered"}],"clips":[{"id":"CLIP-API-001","asset_id":"FILM-API-001","status":"ready"}],"playlists":[{"id":"PLAYLIST-API-001","clip_ids":["CLIP-API-001"],"status":"draft"}],"observations":[{"id":"FILM-OBS-API-001","clip_id":"CLIP-API-001","confidence":"high","classification":"observed"}],"qa_id":"QA-API-001"}
        status, _ = handle_request(method="POST", path="/v1/media/organization-review", body=body, headers=self.analyst, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/media/organization-review/approve", body={"organization_id":"ORG-MEDIA-API","package_id":"ORG-MEDIA-REVIEW-API-001","decision_ref":"DEC-MEDIA-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/media/organization-review?organization_id=ORG-MEDIA-API", headers=self.analyst, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["packages"]), 1)


if __name__ == "__main__":
    unittest.main()
