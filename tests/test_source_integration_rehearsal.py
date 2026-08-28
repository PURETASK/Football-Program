import unittest

from scripts.source_integration_rehearsal import run_rehearsal


class SourceIntegrationRehearsalTests(unittest.TestCase):
    def test_local_http_source_rehearsal_passes_without_external_state(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(result["synthetic"])
        self.assertTrue(result["local_fixture"])
        self.assertFalse(result["external_state_changed"])
        self.assertFalse(result["production_implementation_allowed"])
        self.assertTrue(all(result["checks"].values()), result)


if __name__ == "__main__":
    unittest.main()
