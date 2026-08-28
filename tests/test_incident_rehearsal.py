import unittest

from scripts.incident_rehearsal import run_rehearsal


class IncidentRehearsalTests(unittest.TestCase):
    def test_local_failure_recovery_rehearsal_is_non_activating(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["simulated_failure_recorded"])
        self.assertTrue(result["recovery_recorded"])
        self.assertEqual(result["export"]["exported"], 2)
        self.assertEqual(result["export"]["failed"], 0)
        self.assertTrue(result["rollback_contract_valid"])
        self.assertTrue(result["production_disabled"])
        self.assertTrue(result["events_are_temporary"])


if __name__ == "__main__":
    unittest.main()
