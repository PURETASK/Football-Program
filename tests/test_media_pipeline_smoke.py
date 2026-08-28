import unittest

from scripts.media_pipeline_smoke import run_smoke


class MediaPipelineSmokeTests(unittest.TestCase):
    def test_authorized_media_pipeline_is_bounded_and_tenant_scoped(self):
        result = run_smoke()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["asset_registered"])
        self.assertTrue(result["managed_storage"])
        self.assertTrue(result["worker_completed"])
        self.assertTrue(result["cross_tenant_isolation"])


if __name__ == "__main__":
    unittest.main()
