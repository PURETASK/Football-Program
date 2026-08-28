import json
import unittest
from pathlib import Path

from nfl_fidos.traceability import validate_traceability_ledger


class TraceabilityTests(unittest.TestCase):
    def test_ledger_covers_all_stages_and_explicit_remaining_work(self):
        root = Path(__file__).parents[1]
        ledger = json.loads((root / "control" / "requirements-traceability.json").read_text(encoding="utf-8"))
        result = validate_traceability_ledger(ledger)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["stage_count"], 26)
        self.assertIn("program owner approval of Stage 0 exit", ledger["global_remaining_work"])

    def test_all_repository_evidence_references_resolve(self):
        root = Path(__file__).parents[1]
        ledger = json.loads((root / "control" / "requirements-traceability.json").read_text(encoding="utf-8"))
        result = validate_traceability_ledger(ledger, root=root)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["evidence_reference_count"], 479)
        self.assertEqual(result["missing_evidence"], [])


if __name__ == "__main__":
    unittest.main()
