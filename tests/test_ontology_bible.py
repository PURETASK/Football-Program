import unittest

from nfl_fidos.ontology_bible import validate_ontology_bible


class OntologyBibleTests(unittest.TestCase):
    def test_control_artifacts_are_valid_and_report_remaining_expansion(self):
        result = validate_ontology_bible()
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["term_count"], 40)
        self.assertGreaterEqual(result["alias_count"], 10)
        self.assertGreaterEqual(result["relationship_count"], 10)
        self.assertTrue(result["expansion_required"])


if __name__ == "__main__":
    unittest.main()
