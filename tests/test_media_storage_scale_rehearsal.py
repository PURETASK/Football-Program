import unittest

from scripts.media_storage_scale_rehearsal import run_rehearsal


class MediaStorageScaleRehearsalTests(unittest.TestCase):
    def test_storage_scale_preserves_integrity_isolation_and_retention_safety(self):
        result = run_rehearsal(assets_per_tenant=2)
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["checks"]["digest_integrity"])
        self.assertTrue(result["checks"]["tenant_path_isolation"])
        self.assertTrue(result["checks"]["retention_non_destructive"])


if __name__ == "__main__":
    unittest.main()
