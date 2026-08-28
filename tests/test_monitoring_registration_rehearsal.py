import unittest

from scripts.monitoring_registration_rehearsal import run_rehearsal


class MonitoringRegistrationRehearsalTests(unittest.TestCase):
    def test_monitoring_rehearsal_is_ready_without_external_registration(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["checks"]["production_metadata_ready"])
        self.assertTrue(result["checks"]["missing_registration_fails_closed"])
        self.assertFalse(result["external_registration_performed"])


if __name__ == "__main__":
    unittest.main()
