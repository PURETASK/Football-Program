import tempfile
import unittest
from pathlib import Path

from nfl_fidos.database_operations import backup_sqlite_database, fingerprint_sqlite_database, plan_backup_retention, restore_sqlite_backup, verify_sqlite_database
from nfl_fidos.sqlite_repository import SqliteRepository


class DatabaseOperationsTests(unittest.TestCase):
    def test_backup_verify_restore_and_retention_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "state.sqlite"
            backup = root / "backup.sqlite"
            restored = root / "restored.sqlite"
            repository = SqliteRepository(database)
            repository.put("records", "PLAY-DB-001", {"id":"PLAY-DB-001", "organization_id":"ORG-DB"}, actor="COACH-1", reason="fixture")
            repository.close()
            self.assertEqual(verify_sqlite_database(database)["status"], "valid")
            created = backup_sqlite_database(database, backup)
            self.assertEqual(created["status"], "created")
            self.assertTrue(created["content_match"])
            self.assertEqual(created["source_sha256"], fingerprint_sqlite_database(database))
            restored_report = restore_sqlite_backup(backup, restored)
            self.assertEqual(restored_report["status"], "restored")
            self.assertTrue(restored_report["content_match"])
            self.assertEqual(verify_sqlite_database(restored)["status"], "valid")
            plan = plan_backup_retention(root, keep=1)
            self.assertTrue(plan["destructive_action_required"])
            self.assertIn(str(backup), plan["retained"] + plan["candidates"])

    def test_backup_and_restore_reject_same_path(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "db.sqlite"
            SqliteRepository(database).close()
            with self.assertRaises(ValueError):
                backup_sqlite_database(database, database)
            with self.assertRaises(ValueError):
                restore_sqlite_backup(database, database)


if __name__ == "__main__":
    unittest.main()
