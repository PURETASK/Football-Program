import unittest

from scripts.pilot_rehearsal import run_rehearsal


class PilotRehearsalTests(unittest.TestCase):
    def test_synthetic_pilot_and_rollback_rehearsal_pass(self):
        result = run_rehearsal(run_evaluations=False)
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["live_pilot"])
        self.assertEqual(result["readiness"]["status"], "ready_for_pilot")
        self.assertEqual(result["rollback"]["status"], "passed")
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["external_state_changed"])

    def test_missing_owner_approval_blocks_rehearsal(self):
        result = run_rehearsal(run_evaluations=False, owner_approval=None)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("program owner pilot approval" in blocker for blocker in result["readiness"]["blockers"]))


if __name__ == "__main__":
    unittest.main()
