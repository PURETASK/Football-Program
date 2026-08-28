import copy
import unittest

from nfl_fidos.position_drill_library import load_position_drill_library, validate_position_drill_library


class PositionDrillLibraryTests(unittest.TestCase):
    def test_nfl_position_family_corpus_is_complete_and_valid(self):
        result = validate_position_drill_library(load_position_drill_library())
        self.assertEqual(result["status"], "valid", result)
        self.assertEqual(result["position_count"], 10)
        self.assertEqual(result["drill_count"], 20)

    def test_position_link_and_safety_constraints_are_enforced(self):
        library = load_position_drill_library()
        library["positions"][0]["drills"][0]["position"] = "DB"
        result = validate_position_drill_library(library)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(error["code"] == "POSITION-DRILL-LINK" for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
