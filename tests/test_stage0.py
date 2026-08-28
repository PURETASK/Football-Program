import json
import unittest
from pathlib import Path

from nfl_fidos.stage0 import evaluate_stage0_exit


class Stage0GateTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "control" / "stage-0a-registry.json"
        self.registry = json.loads(path.read_text(encoding="utf-8"))

    def test_current_registry_is_structurally_valid_but_not_approved(self):
        result = evaluate_stage0_exit(self.registry)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["eligible_to_advance"])
        self.assertIn("STAGE0-GAP-AUDIT", {check["id"] for check in result["checks"]})
        self.assertIn("STAGE0-OWNER-APPROVAL", {check["id"] for check in result["checks"]})

    def test_approval_requires_gap_audit(self):
        result = evaluate_stage0_exit(self.registry, owner_approved=True)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["eligible_to_advance"])

    def test_complete_gate_advances(self):
        result = evaluate_stage0_exit(self.registry, gap_audit_complete=True, owner_approved=True)
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["eligible_to_advance"])

    def test_unresolved_dependency_blocks(self):
        registry = json.loads(json.dumps(self.registry))
        registry["capabilities"][0]["dependencies"].append("OBJ-MISSING")
        result = evaluate_stage0_exit(registry, gap_audit_complete=True, owner_approved=True)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("OBJ-MISSING" in blocker for blocker in result["blockers"]))
