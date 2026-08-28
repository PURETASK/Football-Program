import json
import unittest
from pathlib import Path

from nfl_fidos.stage0 import evaluate_stage0_exit
from nfl_fidos.stage0_approval import build_stage0_owner_approval, validate_stage0_owner_approval


class Stage0ApprovalTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[1]
        self.registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
        self.gate = evaluate_stage0_exit(self.registry, gap_audit_complete=True)

    def test_owner_approval_requires_ready_gate_and_is_non_activating(self):
        record = build_stage0_owner_approval(
            approval_id="APPROVAL-STAGE0-001", gate_result=self.gate, registry_id=self.registry["registry_id"],
            approver="program-owner", rationale="Reviewed Stage 0 evidence", evidence_refs=["control/stage-0-exit-gate.json"],
            approved_at="2026-08-23T12:00:00Z",
        )
        self.assertEqual(record["decision"], "approved")
        self.assertFalse(record["production_implementation_allowed"])
        self.assertFalse(record["stage_advance_authorized"])
        self.assertEqual(validate_stage0_owner_approval(record, gate_result=self.gate)["status"], "valid")

    def test_approval_cannot_bypass_unready_gate_or_wrong_role(self):
        blocked = evaluate_stage0_exit(self.registry)
        record = build_stage0_owner_approval(
            approval_id="APPROVAL-STAGE0-002", gate_result=blocked, registry_id=self.registry["registry_id"],
            approver="program-owner", rationale="premature", evidence_refs=["control/stage-0-exit-gate.json"],
            approved_at="2026-08-23T12:00:00Z",
        )
        self.assertEqual(record["decision"], "rejected")
        record["decision"] = "approved"
        record["approver_role"] = "analyst"
        result = validate_stage0_owner_approval(record, gate_result=blocked)
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
