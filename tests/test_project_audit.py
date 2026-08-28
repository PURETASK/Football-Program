import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos.project_audit import run_project_audit


class ProjectAuditTests(unittest.TestCase):
    def test_checkpoint_passes_without_claiming_completion(self):
        root = Path(__file__).resolve().parents[1]
        result = run_project_audit(root=root, run_evals=False)
        self.assertEqual(result["status"], "foundation_verified")
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["completion_claimed"])
        self.assertGreater(result["remaining_stage_count"], 0)
        self.assertFalse(result["control"]["production_implementation_allowed"])

    def test_cli_can_persist_machine_readable_checkpoint(self):
        root = Path(__file__).resolve().parents[1]
        output = Path(tempfile.mkdtemp()) / "project-audit.json"
        with patch("sys.argv", ["project_audit.py", "--root", str(root), "--skip-evals", "--output", str(output)]):
            from scripts import project_audit

            self.assertEqual(project_audit.main(), 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "foundation_verified")
        self.assertFalse(payload["completion_claimed"])
        self.assertEqual(Path(payload["evidence_output"]), output)


if __name__ == "__main__":
    unittest.main()
