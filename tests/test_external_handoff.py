import json
import unittest
from pathlib import Path

from nfl_fidos.external_handoff import build_external_action_handoff


class ExternalHandoffTests(unittest.TestCase):
    def test_handoff_covers_remaining_ledger_actions_without_enabling_production(self):
        root = Path(__file__).resolve().parents[1]
        ledger = json.loads((root / "control" / "requirements-traceability.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "control" / "manifest.json").read_text(encoding="utf-8"))
        result = build_external_action_handoff(ledger=ledger, manifest=manifest)
        expected = sum(len(stage.get("remaining", [])) for stage in ledger["stages"])
        self.assertEqual(result["status"], "awaiting_external_authority")
        self.assertEqual(len(result["actions"]), expected)
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["stage_advance_authorized"])
        self.assertFalse(result["external_state_changed"])
        self.assertTrue(any(item["stage"] == "STAGE-0" and item["responsible_authority"] == "program_owner" for item in result["actions"]))


if __name__ == "__main__":
    unittest.main()
