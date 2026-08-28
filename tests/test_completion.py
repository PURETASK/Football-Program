import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_completion_gate, close_completion_gate


class CompletionTests(unittest.TestCase):
    def checks(self, complete=True):
        names = ["requirement_id", "owner", "inputs_outputs", "ontology_review", "nfl_rule_review", "context_rules", "nuance_cases", "data_model", "permissions", "agent_contracts", "deterministic_validation", "tests_evals", "observability", "documentation", "acceptance_evidence"]
        return {name: complete for name in names}

    def test_complete_gate_requires_all_definition_of_done_checks(self):
        gate = build_completion_gate(gate_id="DONE-001", capability_id="CAP-001", owner="owner", checks=self.checks())
        self.assertEqual(gate["status"], "complete")
        self.assertEqual(len(gate["blockers"]), 0)

    def test_missing_check_creates_explicit_blocker(self):
        checks = self.checks()
        checks["permissions"] = False
        gate = build_completion_gate(gate_id="DONE-002", capability_id="CAP-001", owner="owner", checks=checks)
        self.assertEqual(gate["status"], "blocked")
        self.assertTrue(any("permissions" in blocker for blocker in gate["blockers"]))

    def test_closure_requires_approval_and_acceptance_evidence(self):
        gate = build_completion_gate(gate_id="DONE-003", capability_id="CAP-001", owner="owner", checks=self.checks())
        closed = close_completion_gate(gate, acceptance_evidence=["TEST-RESULT-001"], approver="program-owner")
        self.assertEqual(closed["status"], "complete")
        self.assertEqual(closed["approved_by"], "program-owner")
        blocked = close_completion_gate(gate, acceptance_evidence=[], approver="")
        self.assertEqual(blocked["status"], "blocked")

    def test_invalid_identity_is_not_complete(self):
        gate = build_completion_gate(gate_id="BAD", capability_id="BAD", owner="", checks=self.checks())
        self.assertEqual(gate["status"], "in_progress")
        self.assertTrue(gate["issues"])


if __name__ == "__main__":
    unittest.main()
