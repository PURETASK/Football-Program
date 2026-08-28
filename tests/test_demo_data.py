import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, find_demo_records, purge_demo_data, seed_demo_data
from nfl_fidos.repository import JsonRepository
from nfl_fidos.sqlite_repository import SqliteRepository
from scripts.stage0_rehearsal import build_rehearsal_report


class DemoDataTests(unittest.TestCase):
    def _exercise(self, repository_factory, filename):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / filename
            repository = repository_factory(database)
            try:
                result = seed_demo_data(repository, database_path=database, generate_media=False)
                self.assertEqual(result["status"], "seeded")
                self.assertGreaterEqual(sum(result["record_counts"].values()), 70)
                self.assertEqual(repository.get("play_designs", "PD-DEMO-OFF-DAGGER")["status"], "published")
                self.assertEqual(repository.get("play_designs", "PD-DEMO-DEF-COVER3")["status"], "under_review")
                self.assertEqual(repository.get("play_designs", "PD-DEMO-OFF-DAGGER")["validation"]["status"], "valid")
                self.assertEqual(seed_demo_data(repository, database_path=database, generate_media=False)["status"], "already_seeded")
                repository.put("plays", "PLAY-KEEP-REAL", {"id": "PLAY-KEEP-REAL", "organization_id": "ORG-REAL-KEEP", "status": "draft"}, actor="TEST", reason="unrelated_fixture")
                cleanup = purge_demo_data(repository, database_path=database)
                self.assertEqual(cleanup["status"], "purged")
                self.assertEqual(find_demo_records(repository), {})
                self.assertIsNotNone(repository.get("plays", "PLAY-KEEP-REAL"))
                self.assertEqual(len(repository.history(record_id="PLAY-KEEP-REAL")), 1)
            finally:
                close = getattr(repository, "close", None)
                if close:
                    close()

    def test_sqlite_seed_is_end_to_end_and_cleanup_is_scoped(self):
        self._exercise(SqliteRepository, "demo.sqlite3")

    def test_json_seed_is_end_to_end_and_cleanup_is_scoped(self):
        self._exercise(JsonRepository, "demo.json")

    def test_replace_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            repository = SqliteRepository(database)
            try:
                seed_demo_data(repository, database_path=database, generate_media=False)
                with self.assertRaises(ValueError):
                    seed_demo_data(repository, database_path=database, replace=True, replace_confirmed=False, generate_media=False)
            finally:
                repository.close()

    def test_production_environment_blocks_seed_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            repository = SqliteRepository(database)
            try:
                with patch.dict(os.environ, {"NFL_FIDOS_ENV": "production"}):
                    with self.assertRaises(RuntimeError):
                        seed_demo_data(repository, database_path=database, generate_media=False)
                    with self.assertRaises(RuntimeError):
                        purge_demo_data(repository, database_path=database)
            finally:
                repository.close()

    def test_scope_is_locked_to_the_demo_organization(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"
            repository = SqliteRepository(database)
            try:
                with self.assertRaises(ValueError):
                    seed_demo_data(repository, database_path=database, organization_id="ORG-REAL", generate_media=False)
                with self.assertRaises(ValueError):
                    purge_demo_data(repository, database_path=database, organization_id="ORG-REAL")
            finally:
                repository.close()

    def test_stage0_rehearsal_report_is_ready_without_fabricating_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "control").mkdir()
            source_root = Path(__file__).parents[1] / "control"
            for name in ("stage-0a-registry.json", "stage-0-gap-audit.json"):
                (root / "control" / name).write_text((source_root / name).read_text(encoding="utf-8"), encoding="utf-8")
            database = root / "stage0.sqlite3"
            repository = SqliteRepository(database)
            try:
                seed = seed_demo_data(repository, database_path=database, generate_media=False)
            finally:
                repository.close()
            report = build_rehearsal_report(root=root, database=database, seed=seed)
            self.assertEqual(report["status"], "ready_for_owner_review")
            self.assertTrue(report["rehearsal"]["synthetic"])
            self.assertGreaterEqual(report["rehearsal"]["persisted_operating_component_count"], 13)
            self.assertFalse(report["safety"]["owner_approval_recorded"])
            self.assertFalse(report["safety"]["production_implementation_allowed"])
            self.assertFalse(report["safety"]["activation_performed"])


if __name__ == "__main__":
    unittest.main()
