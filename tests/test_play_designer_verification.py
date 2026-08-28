import unittest
from pathlib import Path

from src.nfl_fidos.play_designer_verification import verify_play_designer


class PlayDesignerVerificationTests(unittest.TestCase):
    def test_integrated_surface_passes_local_verification(self):
        result = verify_play_designer(Path(__file__).parents[1])
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["production_implementation_allowed"])
        self.assertTrue(all(check["passed"] for check in result["checks"]))


if __name__ == "__main__":
    unittest.main()
