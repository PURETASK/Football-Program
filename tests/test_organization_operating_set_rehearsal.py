import unittest

from scripts.organization_operating_set_rehearsal import run_rehearsal


class OrganizationOperatingSetRehearsalTests(unittest.TestCase):
    def test_real_package_builders_compose_all_thirteen_synthetic_components(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["component_count"], 13)
        self.assertEqual(result["readiness"]["status"], "ready_for_bundle")
        self.assertEqual(result["bundle"]["status"], "ready_for_owner_review")
        self.assertTrue(result["owner_approval_required"])
        self.assertFalse(result["activation_performed"])
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["external_state_changed"])


if __name__ == "__main__":
    unittest.main()
