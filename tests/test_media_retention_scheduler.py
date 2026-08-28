import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.media_retention_scheduler import MediaRetentionScheduler
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.tenant_repository import TenantRepository


class MediaRetentionSchedulerTests(unittest.TestCase):
    def test_scan_persists_review_without_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-RETENTION-SCAN", actor="OWNER")
            repository.put("film_assets", "FILM-OLD-SCAN", {"id":"FILM-OLD-SCAN", "organization_id":"ORG-RETENTION-SCAN", "captured_at":"2020-01-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/old.mp4"}}, actor="OWNER", reason="test_seed")
            report = MediaRetentionScheduler(repository).run_scan(actor="OWNER", retention_days=1, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertTrue(report["id"].startswith("MEDIA-RETENTION-SCAN-"))
            self.assertTrue(report["destructive_action_required"])
            self.assertFalse(report["destructive_action_executed"])
            self.assertEqual(len(repository.list("media_retention_runs")), 1)
            self.assertIsNotNone(repository.get("film_assets", "FILM-OLD-SCAN"))

    def test_api_requires_owner_governance_scope(self):
        secret = "retention-scan-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            with tempfile.TemporaryDirectory() as directory:
                service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
                owner = {"Authorization":"Bearer " + issue_token(subject="OWNER-SCAN", role="program_owner", organization_id="ORG-SCAN", secret=secret)}
                player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-SCAN", role="player", organization_id="ORG-SCAN", secret=secret)}
                self.assertEqual(handle_request(method="POST", path="/v1/media/retention-scan", body={"organization_id":"ORG-SCAN"}, headers=owner, service=service)[0], 200)
                self.assertEqual(handle_request(method="POST", path="/v1/media/retention-scan", body={"organization_id":"ORG-SCAN"}, headers=player, service=service)[0], 403)
        finally:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
