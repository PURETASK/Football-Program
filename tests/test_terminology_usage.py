import json
import unittest
from pathlib import Path

from nfl_fidos.terminology_usage import validate_team_usage_corpus


class TerminologyUsageTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "ontology" / "team-terminology-validation-corpus.json"
        self.corpus = json.loads(path.read_text(encoding="utf-8"))

    def test_source_linked_fixture_corpus_resolves_canonical_terms(self):
        result = validate_team_usage_corpus(self.corpus)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["record_count"], 11)
        self.assertEqual(result["team_count"], 3)

    def test_unknown_or_mismatched_usage_is_rejected(self):
        invalid = dict(self.corpus)
        invalid["records"] = [dict(self.corpus["records"][0], phrase="unknown private term")]
        result = validate_team_usage_corpus(invalid)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unresolved" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
