import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.backup_scheduler import BackupScheduler
from nfl_fidos.sqlite_repository import SqliteRepository


class BackupSchedulerTests(unittest.TestCase):
    def test_due_plan_executes_verified_backup_without_retention_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "state.sqlite3"
            destination = root / "backups"
            repository = SqliteRepository(source)
            repository.put("records", "BACKUP-001", {"id": "BACKUP-001", "organization_id": "ORG-1"}, actor="OWNER", reason="fixture")
            repository.close()
            scheduler = BackupScheduler(environment="validation")
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            plan = scheduler.plan(source=source, destination_directory=destination, now=now, interval_hours=24, keep=2)
            self.assertTrue(plan["due"])
            result = scheduler.run(source=source, destination_directory=destination, actor="OWNER", execute=True, now=now, keep=2)
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["backup"]["content_match"])
            self.assertTrue(result["retention_plan"]["destructive_action_required"])
            self.assertEqual(len(list(destination.glob("*.sqlite3"))), 1)

    def test_production_execution_is_control_gated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "state.sqlite3"
            SqliteRepository(source).close()
            result = BackupScheduler(control_root=Path(__file__).parents[1], environment="production").run(source=source, destination_directory=root / "backups", actor="OWNER", execute=True)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("Stage 0", result["blocker"])


if __name__ == "__main__":
    unittest.main()
