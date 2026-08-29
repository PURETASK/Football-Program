import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class AuditMasterPlanOutputTests(unittest.TestCase):
    def test_cli_persists_the_same_conformance_report_it_prints(self):
        from scripts import audit_master_plan

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "master-plan-audit.json"
            argv = [
                "audit_master_plan.py",
                "--root", str(root),
                "--markdown", str(root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md"),
                "--docx", str(root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.docx"),
                "--traceability", str(root / "control" / "requirements-traceability.json"),
                "--output", str(output),
            ]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()) as captured:
                exit_code = audit_master_plan.main()

            self.assertEqual(exit_code, 0)
            printed = json.loads(captured.getvalue())
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(printed, persisted)
            self.assertEqual(persisted["status"], "passed")
            self.assertEqual(persisted["evidence_output"], str(output.resolve()))


if __name__ == "__main__":
    unittest.main()
