import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.browser_evidence import validate_browser_evidence


class BrowserEvidenceTests(unittest.TestCase):
    def test_repository_evidence_is_valid_and_local_only(self):
        root = Path(__file__).resolve().parents[1]
        result = validate_browser_evidence(evidence_path=root / "control" / "browser-validation-evidence.json")
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["external_state_changed"])
        self.assertFalse(result["production_implementation_allowed"])

    def test_incomplete_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps({"stage":"STAGE-22", "status":"passed", "url":"https://production.example", "checks":[]}), encoding="utf-8")
            result = validate_browser_evidence(evidence_path=path)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(result["issues"])
