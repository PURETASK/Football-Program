import unittest

from scripts.agent_runtime_rehearsal import run_rehearsal


class AgentRuntimeRehearsalTests(unittest.TestCase):
    def test_all_controlled_roles_dispatch_through_local_adapters(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["role_count"], 16)
        self.assertTrue(result["checks"]["all_roles_covered"])
        self.assertTrue(result["checks"]["all_runs_completed"])
        self.assertTrue(result["checks"]["all_outputs_local_only"])
        self.assertFalse(result["external_provider_called"])
        self.assertFalse(result["canonical_write_performed"])
        self.assertFalse(result["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
