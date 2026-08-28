import json
import unittest
from pathlib import Path


class UxUiAuditTests(unittest.TestCase):
    def test_local_ux_evidence_and_brand_asset_are_present(self):
        root = Path(__file__).resolve().parents[1]
        evidence = json.loads((root / "control" / "ux-ui-audit-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["status"], "passed")
        self.assertTrue(all(value for key, value in evidence["findings"].items() if key != "browser_console_errors"))
        self.assertEqual(evidence["findings"]["browser_console_errors"], 0)
        self.assertFalse(evidence["runtime_evidence"]["production_implementation_allowed"])
        self.assertFalse(evidence["runtime_evidence"]["external_state_changed"])
        self.assertTrue((root / "ui" / "assets" / "nfl-fidos-mark.svg").is_file())
