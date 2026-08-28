import tempfile
import unittest
from pathlib import Path

from scripts.stage0_runtime_smoke import run_smoke


class Stage0RuntimeSmokeTests(unittest.TestCase):
    def test_synthetic_seed_is_reachable_through_public_and_authenticated_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_smoke(Path(directory) / "stage0.sqlite3")
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["safety"]["external_state_changed"])
        self.assertGreaterEqual(len(result["checks"]), 5)
        self.assertTrue(all(item["passed"] for item in result["checks"]))


if __name__ == "__main__":
    unittest.main()
