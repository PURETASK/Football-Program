import unittest

from scripts.deployment_runtime_rehearsal import run_rehearsal


class DeploymentRuntimeRehearsalTests(unittest.TestCase):
    def test_runtime_rehearsal_is_passed_and_non_activating(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(all(result["checks"].values()))
        self.assertTrue(result["temporary_workspace"])
        self.assertFalse(result["external_state_changed"])
        self.assertFalse(result["activation_performed"])
        self.assertFalse(result["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
