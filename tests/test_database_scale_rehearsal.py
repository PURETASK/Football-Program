import unittest

from scripts.database_scale_rehearsal import run_rehearsal


class DatabaseScaleRehearsalTests(unittest.TestCase):
    def test_bounded_scale_preserves_tenancy_and_audit_history(self):
        result = run_rehearsal(records_per_tenant=12)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["total_records"], 24)
        self.assertTrue(result["checks"]["tenant_read_counts"])
        self.assertTrue(result["checks"]["audit_history_counts"])
        self.assertTrue(result["checks"]["cross_tenant_isolation"])
        self.assertFalse(result["external_state_changed"])


if __name__ == "__main__":
    unittest.main()
