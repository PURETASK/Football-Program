import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_red_team_matrix, check_play_scheme_compatibility
from test_play_compiler import valid_play
from test_scheme import offense_scheme


class CompatibilityTests(unittest.TestCase):
    def test_matching_play_and_scheme_are_compatible(self):
        result = check_play_scheme_compatibility(play=valid_play(), scheme=offense_scheme(), result_id="COMPAT-001")
        self.assertTrue(result["compatible"])
        self.assertEqual(result["issues"], [])
        self.assertTrue(result["review_required"])

    def test_mismatched_formation_is_rejected(self):
        play = valid_play()
        play["formation"] = "under_center"
        result = check_play_scheme_compatibility(play=play, scheme=offense_scheme(), result_id="COMPAT-002")
        self.assertFalse(result["compatible"])
        self.assertEqual(result["issues"][0]["code"], "COMPAT-FORMATION")

    def test_red_team_matrix_preserves_threat_response_counter(self):
        matrix = build_red_team_matrix(
            matrix_id="REDTEAM-001", scheme_id="SCHEME-OFF-001",
            rows=[{"threat": "pressure", "response": "protection check", "counter": "coverage rotation", "evidence_refs": ["EVD-1"]}],
        )
        self.assertEqual(matrix["status"], "draft")
        self.assertEqual(matrix["rows"][0]["counter"], "coverage rotation")
        self.assertTrue(matrix["review_required"])

    def test_red_team_rejects_incomplete_rows(self):
        matrix = build_red_team_matrix(
            matrix_id="REDTEAM-002", scheme_id="SCHEME-OFF-001",
            rows=[{"threat": "pressure", "response": "protection check"}],
        )
        self.assertEqual(matrix["issues"][0]["code"], "REDTEAM-ROW")


if __name__ == "__main__":
    unittest.main()
