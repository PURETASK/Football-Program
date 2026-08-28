import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.deployment_preflight import run_deployment_preflight
from nfl_fidos.secret_source import inspect_secret_source


class DeploymentPreflightTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.contract = self.root / "deployment" / "nfl-fidos-deployment.json"

    def test_validation_preflight_is_ready_without_exposing_secret(self):
        result = run_deployment_preflight(contract_path=self.contract, control_root=self.root, environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"x" * 32}, environment="validation")
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["activation_performed"])
        self.assertFalse(result["secret_source"]["value_exposed"])
        self.assertNotIn("x" * 32, json.dumps(result))

    def test_production_preflight_requires_external_source_and_gate(self):
        result = run_deployment_preflight(contract_path=self.contract, control_root=self.root, environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32}, environment="production")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("secret_source", result["blockers"])
        self.assertIn("control_plane", result["blockers"])

    def test_mounted_file_is_checked_without_returning_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            secret_path = Path(directory) / "auth.secret"
            secret_path.write_text("y" * 32, encoding="utf-8")
            result = inspect_secret_source(environ={"NFL_FIDOS_AUTH_SECRET_FILE":str(secret_path)}, environment="production", require_external_source=True)
            self.assertEqual(result["status"], "valid")
            self.assertEqual(result["source_type"], "mounted_file")
            self.assertNotIn("y" * 32, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
