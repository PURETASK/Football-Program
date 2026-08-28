import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.media_retention import plan_media_retention
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class MediaRetentionTests(unittest.TestCase):
    def test_plan_marks_old_assets_for_review_without_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-RETENTION", actor="owner")
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            repository.put("film_assets", "FILM-OLD", {"id":"FILM-OLD", "organization_id":"ORG-RETENTION", "captured_at":"2024-01-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/old.mp4"}}, actor="owner", reason="retention_test")
            repository.put("film_assets", "FILM-NEW", {"id":"FILM-NEW", "organization_id":"ORG-RETENTION", "captured_at":"2025-12-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/new.mp4"}}, actor="owner", reason="retention_test")
            report = plan_media_retention(repository=repository, retention_days=365, now=now)
            self.assertEqual(report["status"], "review_required")
            self.assertEqual([item["asset_id"] for item in report["candidates"]], ["FILM-OLD"])
            self.assertEqual([item["asset_id"] for item in report["retained"]], ["FILM-NEW"])
            self.assertFalse(report["delete_performed"])
            self.assertIsNotNone(repository.get("film_assets", "FILM-OLD"))

    def test_missing_timestamp_is_never_treated_as_expired(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-RETENTION", actor="owner")
            repository.put("film_assets", "FILM-UNKNOWN", {"id":"FILM-UNKNOWN", "organization_id":"ORG-RETENTION", "managed_storage":{}}, actor="owner", reason="retention_test")
            report = plan_media_retention(repository=repository, retention_days=1)
            self.assertEqual(len(report["unknown"]), 1)
            self.assertEqual(len(report["candidates"]), 0)


if __name__ == "__main__":
    unittest.main()
