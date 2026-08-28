import tempfile
import unittest
from pathlib import Path

from nfl_fidos.migrations import apply_migrations, inspect_migrations, rollback_snapshot
from nfl_fidos.sqlite_repository import SqliteRepository


class MigrationTests(unittest.TestCase):
    def test_dry_run_does_not_apply_and_apply_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.db"
            repository = SqliteRepository(database)
            repository.put("plays", "PLAY-1", {"id":"PLAY-1", "organization_id":"ORG-1"}, actor="coach", reason="fixture")
            before = inspect_migrations(database)
            self.assertEqual(before["version"], 0)
            self.assertTrue(apply_migrations(database, dry_run=True)["pending"])
            self.assertEqual(inspect_migrations(database)["version"], 0)
            repository.close()
            result = apply_migrations(database)
            self.assertEqual(result["version"], 1)
            migrated = SqliteRepository(database)
            self.assertEqual(migrated.get("plays", "PLAY-1")["organization_id"], "ORG-1")
            self.assertEqual(len(migrated.history(record_id="PLAY-1")), 1)
            migrated.close()

    def test_snapshot_rollback_restores_previous_schema_state(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.db"
            snapshot = Path(directory) / "state.before.db"
            repository = SqliteRepository(database)
            repository.put("objects", "OBJ-1", {"id":"OBJ-1", "organization_id":"ORG-1", "value":"before"}, actor="owner", reason="fixture")
            repository.close()
            apply_migrations(database, snapshot_path=snapshot)
            changed = SqliteRepository(database)
            changed.put("objects", "OBJ-1", {"id":"OBJ-1", "organization_id":"ORG-1", "value":"after"}, actor="owner", reason="change")
            changed.close()
            rollback_snapshot(database, snapshot)
            restored = SqliteRepository(database)
            self.assertEqual(restored.get("objects", "OBJ-1")["value"], "before")
            restored.close()


if __name__ == "__main__":
    unittest.main()
