import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_release_candidate, evaluate_delivery_wave


class DeliveryTests(unittest.TestCase):
    def gate(self, capability_id="CAP-001", status="complete"):
        return {"id": "DONE-001", "capability_id": capability_id, "status": status}

    def evals(self, status="passed"):
        return {"suite_id": "EVAL-1", "status": status}

    def test_wave_ready_requires_complete_gates_and_passing_evals(self):
        wave = evaluate_delivery_wave(wave_id="WAVE-1", number=1, outcome="vertical slice", capability_ids=["CAP-001"], feature_gates=[self.gate()], eval_result=self.evals())
        self.assertEqual(wave["status"], "ready")
        self.assertTrue(wave["human_approval_required"])

    def test_wave_blocks_missing_gate_or_failed_evals(self):
        wave = evaluate_delivery_wave(wave_id="WAVE-2", number=2, outcome="slice", capability_ids=["CAP-002"], feature_gates=[self.gate("CAP-002", "blocked")], eval_result=self.evals("failed"))
        self.assertEqual(wave["status"], "blocked")
        self.assertTrue(any("CAP-002" in blocker for blocker in wave["blockers"]))
        self.assertTrue(any("evaluation" in blocker.lower() for blocker in wave["blockers"]))

    def test_release_candidate_requires_human_approval(self):
        wave = evaluate_delivery_wave(wave_id="WAVE-3", number=3, outcome="slice", capability_ids=["CAP-001"], feature_gates=[self.gate()], eval_result=self.evals())
        blocked = build_release_candidate(release_id="RC-1", wave=wave, feature_gate_ids=["DONE-001"], eval_result=self.evals())
        self.assertEqual(blocked["status"], "blocked")
        approved = build_release_candidate(release_id="RC-2", wave=wave, feature_gate_ids=["DONE-001"], eval_result=self.evals(), approver="program-owner")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(approved["approved_by"], "program-owner")


if __name__ == "__main__":
    unittest.main()
