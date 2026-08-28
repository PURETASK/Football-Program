import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class MediaRetentionApiTests(unittest.TestCase):
    def test_owner_can_review_retention_plan_and_players_cannot(self):
        secret = "retention-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        owner = {"Authorization":"Bearer " + issue_token(subject="OWNER-RETENTION", role="program_owner", organization_id="ORG-RETENTION-API", secret=secret)}
        player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-RETENTION", role="player", organization_id="ORG-RETENTION-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("film_assets", "FILM-RETENTION-API", {"id":"FILM-RETENTION-API", "organization_id":"ORG-RETENTION-API", "captured_at":"2020-01-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/retention.mp4"}}, actor="owner", reason="retention_api_test")
            status, payload = handle_request(method="GET", path="/v1/media/retention-plan?organization_id=ORG-RETENTION-API&retention_days=1", headers=owner, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "review_required")
            self.assertEqual(handle_request(method="GET", path="/v1/media/retention-plan?organization_id=ORG-RETENTION-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
