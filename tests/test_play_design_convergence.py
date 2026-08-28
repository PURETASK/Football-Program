import unittest

from nfl_fidos.play_design_convergence import run_convergence_rehearsal


class PlayDesignConvergenceTests(unittest.TestCase):
    def test_disjoint_edits_converge_and_overlapping_edits_remain_explicit(self):
        report = run_convergence_rehearsal()
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["cases"]["disjoint_edits"]["converged"])
        self.assertEqual(report["cases"]["disjoint_edits"]["conflicts"], [])
        self.assertTrue(report["cases"]["overlapping_edits"]["conflict_detected"])
        self.assertEqual(report["cases"]["overlapping_edits"]["conflicts"], ["elements.ROUTE-X"])
        self.assertFalse(report["external_state_changed"])


if __name__ == "__main__":
    unittest.main()
