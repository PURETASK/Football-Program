import copy
import unittest

from nfl_fidos.scheme_family_corpus import load_scheme_family_corpus, validate_scheme_family_corpus


class SchemeFamilyCorpusTests(unittest.TestCase):
    def test_offense_and_defense_have_four_validated_families(self):
        result = validate_scheme_family_corpus(load_scheme_family_corpus())
        self.assertEqual(result["status"], "valid", result)
        self.assertEqual(result["family_count"], 8)
        self.assertEqual(result["unit_counts"], {"offense":4, "defense":4})

    def test_corpus_rejects_missing_counter_depth(self):
        bible = load_scheme_family_corpus()
        bible["families"][0]["counter_counters"] = []
        result = validate_scheme_family_corpus(bible)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(error["code"] == "SCHEME-FAMILY-COUNTERS" for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
