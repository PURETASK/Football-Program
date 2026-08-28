import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class DeploymentEvidenceOutputTests(unittest.TestCase):
    def test_preflight_persists_value_free_report_without_activation(self):
        from scripts import deployment_preflight

        root = Path(__file__).resolve().parents[1]
        contract = root / "deployment" / "nfl-fidos-deployment.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preflight.json"
            argv = [
                "deployment_preflight.py",
                "--contract",
                str(contract),
                "--control-root",
                str(root),
                "--output",
                str(output),
            ]
            with patch("sys.argv", argv), patch.dict(os.environ, {"NFL_FIDOS_AUTH_SECRET": ""}, clear=False), contextlib.redirect_stdout(io.StringIO()):
                exit_code = deployment_preflight.main()

            self.assertEqual(exit_code, 1)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["evidence_output"], str(output.resolve()))
            self.assertFalse(report["activation_performed"])
            self.assertFalse(report["secret_source"]["value_exposed"])


if __name__ == "__main__":
    unittest.main()
