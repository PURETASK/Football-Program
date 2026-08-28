import tempfile
import unittest
from pathlib import Path

from nfl_fidos.database_operations import backup_sqlite_database
from nfl_fidos.migrations import apply_migrations
from nfl_fidos.operational_readiness import run_operational_readiness
from nfl_fidos.sqlite_repository import SqliteRepository


class OperationalReadinessTests(unittest.TestCase):
    def test_migrated_database_and_passing_evals_are_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "fidos.sqlite3"
            repository = SqliteRepository(database)
            repository.close()
            apply_migrations(database)
            report = run_operational_readiness(
                environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_DATABASE":str(database)},
                database_path=database,
            )
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["blockers"], [])

    def test_missing_database_is_an_explicit_deployment_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "missing.sqlite3"
            report = run_operational_readiness(
                environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_DATABASE":str(database)},
                database_path=database,
            )
            self.assertEqual(report["status"], "blocked")
            self.assertIn("database_integrity", report["blockers"])
            self.assertIn("database_migrations", report["blockers"])

    def test_supplied_current_eval_result_is_used_without_rerunning_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "fidos.sqlite3"
            repository = SqliteRepository(database)
            repository.close()
            apply_migrations(database)
            report = run_operational_readiness(
                environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_DATABASE":str(database)},
                database_path=database,
                run_evals=False,
                eval_result={"status":"passed", "passed":97, "failed":0, "suite_id":"test-suite"},
            )
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["blockers"], [])

    def test_short_production_secret_is_blocked_without_touching_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "missing.sqlite3"
            report = run_operational_readiness(
                environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"short", "NFL_FIDOS_DATABASE":str(database)},
                database_path=database,
                run_evals=False,
            )
            self.assertIn("runtime_config", report["blockers"])
            self.assertFalse(database.exists())

    def test_production_missing_media_tools_are_explicitly_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "missing.sqlite3"
            report = run_operational_readiness(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_FFMPEG":"missing-ffmpeg", "NFL_FIDOS_FFPROBE":"missing-ffprobe", "NFL_FIDOS_DATABASE":str(database)}, database_path=database, run_evals=False)
            self.assertIn("media_tooling", report["blockers"])


if __name__ == "__main__":
    unittest.main()
