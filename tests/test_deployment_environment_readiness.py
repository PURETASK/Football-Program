import tempfile
import unittest
from pathlib import Path

from nfl_fidos.database_operations import backup_sqlite_database
from nfl_fidos.deployment_environment_readiness import run_deployment_environment_readiness
from nfl_fidos.migrations import apply_migrations
from nfl_fidos.sqlite_repository import SqliteRepository


class DeploymentEnvironmentReadinessTests(unittest.TestCase):
    def test_validation_composes_ready_non_activating_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "fidos.sqlite3"
            repository = SqliteRepository(database)
            repository.close()
            apply_migrations(database)
            result = run_deployment_environment_readiness(
                contract_path="deployment/nfl-fidos-deployment.json",
                control_root=".",
                environ={
                    "NFL_FIDOS_ENV": "validation",
                    "NFL_FIDOS_AUTH_SECRET": "x" * 32,
                    "NFL_FIDOS_DATABASE": str(database),
                    "NFL_FIDOS_OBSERVABILITY_PATH": str(root / "events.jsonl"),
                    "NFL_FIDOS_SCHEDULER_PROVIDER": "provider_neutral",
                    "NFL_FIDOS_SCHEDULER_REGISTRATION_REF": "SCHEDULER-REG-001",
                    "NFL_FIDOS_MONITORING_BACKEND": "structured_jsonl",
                    "NFL_FIDOS_MONITORING_REGISTRATION_REF": "MONITORING-REG-001",
                },
                database_path=database,
                run_evals=False,
                eval_result={"status": "passed", "passed": 97, "failed": 0, "suite_id": "test-suite"},
                environment="validation",
            )
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["blockers"], [])
            self.assertFalse(result["activation_performed"])
            self.assertFalse(result["external_state_changed"])

    def test_production_report_blocks_without_external_deployment_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_deployment_environment_readiness(
                contract_path="deployment/nfl-fidos-deployment.json",
                control_root=".",
                environ={
                    "NFL_FIDOS_ENV": "production",
                    "NFL_FIDOS_AUTH_SECRET": "x" * 32,
                    "NFL_FIDOS_DATABASE": str(Path(directory) / "missing.sqlite3"),
                    "NFL_FIDOS_OBSERVABILITY_PATH": str(Path(directory) / "events.jsonl"),
                    "NFL_FIDOS_SCHEDULER_PROVIDER": "provider_neutral",
                    "NFL_FIDOS_MONITORING_BACKEND": "structured_jsonl",
                },
                database_path=Path(directory) / "missing.sqlite3",
                run_evals=False,
                environment="production",
            )
            self.assertEqual(result["status"], "blocked")
            self.assertIn("deployment_preflight", result["blockers"])
            self.assertIn("operational_readiness", result["blockers"])
            self.assertIn("scheduler_registration", result["blockers"])
            self.assertFalse(result["activation_performed"])


if __name__ == "__main__":
    unittest.main()
