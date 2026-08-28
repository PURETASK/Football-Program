import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos import JsonRepository
from nfl_fidos.media_retention_executor import execute_media_retention
from nfl_fidos.tenant_repository import TenantRepository


class MediaRetentionExecutorTests(unittest.TestCase):
    def _fixture(self, directory):
        root = Path(directory) / "managed"
        root.mkdir()
        media = root / "old.mp4"
        media.write_bytes(b"temporary")
        repo = JsonRepository(Path(directory) / "state.json")
        repo.put("film_assets", "FILM-OLD", {"id":"FILM-OLD", "organization_id":"ORG-RETENTION-EXEC", "captured_at":"2020-01-01T00:00:00+00:00", "managed_storage":{"destination_path":str(media)}}, actor="OWNER", reason="test")
        return root, media, repo, TenantRepository(repo, organization_id="ORG-RETENTION-EXEC", actor="OWNER")

    def test_default_is_dry_run_and_execution_requires_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            root, media, repo, tenant = self._fixture(directory)
            planned = execute_media_retention(repository=tenant, actor="OWNER", actor_role="program_owner", approval_ref=None, managed_root=root, retention_days=1, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(planned["status"], "planned")
            self.assertFalse(planned["delete_performed"])
            self.assertTrue(media.exists())
            denied = execute_media_retention(repository=tenant, actor="COACH", actor_role="coach_staff", approval_ref="APPROVAL-1", managed_root=root, retention_days=1, execute=True, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(denied["status"], "blocked")

    def test_approved_validation_execution_deletes_only_managed_file_and_keeps_tombstone(self):
        with tempfile.TemporaryDirectory() as directory:
            root, media, repo, tenant = self._fixture(directory)
            result = execute_media_retention(repository=tenant, actor="OWNER", actor_role="program_owner", approval_ref="APPROVAL-RETENTION-TEST", managed_root=root, retention_days=1, execute=True, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(result["status"], "executed")
            self.assertTrue(result["delete_performed"])
            self.assertFalse(media.exists())
            self.assertEqual(repo.get("film_assets", "FILM-OLD")["retention_status"], "media_deleted")

    def test_production_execution_is_blocked_by_stage_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(repo, organization_id="ORG-RETENTION-EXEC", actor="OWNER")
            result = execute_media_retention(repository=tenant, actor="OWNER", actor_role="program_owner", approval_ref="APPROVAL-1", managed_root=directory, execute=True, environment="production")
            self.assertEqual(result["status"], "blocked")
            self.assertIn("Stage 0", result["blocker"])
