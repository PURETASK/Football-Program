import copy
import json
import unittest
from pathlib import Path

from nfl_fidos.scheme_lineage import validate_scheme_lineage_corpus


class SchemeLineageTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.corpus = json.loads((root / "scheme" / "team-doctrine-lineage-validation.json").read_text(encoding="utf-8"))
        self.bible = json.loads((root / "scheme" / "scheme-bible.json").read_text(encoding="utf-8"))

    def test_fixture_corpus_covers_every_scheme_family_without_claiming_approval(self):
        result = validate_scheme_lineage_corpus(self.corpus, self.bible)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["family_count"], 8)
        self.assertEqual(result["unit_counts"], {"offense":4, "defense":4})

    def test_unknown_family_or_approved_status_is_rejected(self):
        invalid = copy.deepcopy(self.corpus)
        invalid["records"][0]["family_id"] = "SCHEME-FAM-UNKNOWN"
        invalid["records"][1]["review_status"] = "approved"
        result = validate_scheme_lineage_corpus(invalid, self.bible)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unknown family" in error for error in result["errors"]))
        self.assertTrue(any("review_required" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
