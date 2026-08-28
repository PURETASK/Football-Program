import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.tenant_repository import TenantRepository


class FilmVoiceNotesApiTests(unittest.TestCase):
    def test_owner_can_create_and_read_bounded_voice_note(self):
        secret = "film-voice-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            with tempfile.TemporaryDirectory() as directory:
                repository = JsonRepository(Path(directory) / "state.json")
                tenant = TenantRepository(repository, organization_id="ORG-VOICE", actor="OWNER-VOICE")
                tenant.put("film_clips", "CLIP-VOICE-API", {"id": "CLIP-VOICE-API", "organization_id": "ORG-VOICE", "asset_id": "FILM-VOICE-API"}, actor="SEED", reason="fixture")
                service = FootballIntelligenceService(repository)
                token = issue_token(subject="OWNER-VOICE", role="program_owner", organization_id="ORG-VOICE", secret=secret)
                headers = {"Authorization": "Bearer " + token}
                status, payload = handle_request(method="POST", path="/v1/film/voice-notes", headers=headers, service=service, body={"organization_id": "ORG-VOICE", "note_id": "VOICE-NOTE-API", "clip_id": "CLIP-VOICE-API", "frame_seconds": 4.5, "mime_type": "audio/webm", "audio_data": "data:audio/webm;base64,AAE=", "transcript": "Read the safety rotation."})
                self.assertEqual(status, 201)
                status, payload = handle_request(method="GET", path="/v1/film/voice-notes?organization_id=ORG-VOICE", headers=headers, service=service)
                self.assertEqual(status, 200)
                self.assertEqual(payload["data"]["voice_notes"][0]["clip_id"], "CLIP-VOICE-API")
        finally:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
