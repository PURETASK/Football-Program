import unittest

from nfl_fidos.seasonal_role_drill_variants import load_seasonal_role_variants, validate_seasonal_role_variants


class SeasonalRoleDrillVariantTests(unittest.TestCase):
    def test_variant_corpus_covers_all_seasons_and_validates(self):
        result = validate_seasonal_role_variants(variants_library=load_seasonal_role_variants())
        self.assertEqual(result["status"], "valid", result)
        self.assertEqual(result["variant_count"], 10)
        self.assertEqual(set(result["seasons"]), {"offseason", "preseason", "regular_season", "postseason"})

    def test_variant_must_match_base_position_and_have_adaptation(self):
        library = load_seasonal_role_variants()
        library["variants"][0]["position"] = "DB"
        library["variants"][1]["adaptation"].pop("safety_controls")
        result = validate_seasonal_role_variants(variants_library=library)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(error["code"] == "VARIANT-POSITION" for error in result["errors"]))
        self.assertTrue(any(error["code"] == "VARIANT-ADAPTATION" for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
