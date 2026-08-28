import unittest

from scripts.operational_rehearsal import run_rehearsal


class OperationalRehearsalTests(unittest.TestCase):
    def test_bounded_rehearsal_composes_readiness_and_stage_gate(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(result["temporary_workspace"])
        self.assertTrue(result["backup_content_match"])
        self.assertTrue(result["restore_content_match"])
        self.assertEqual(result["readiness_status"], "ready")
        self.assertTrue(result["scheduled_dry_run"])
        self.assertEqual(result["production_guard_status"], "blocked")
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["external_state_changed"])


if __name__ == "__main__":
    unittest.main()
