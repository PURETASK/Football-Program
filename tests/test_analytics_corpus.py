import json
import unittest
from pathlib import Path

from nfl_fidos.analytics_corpus import validate_analytics_corpus


class AnalyticsCorpusTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.dictionary = json.loads((root / "analytics" / "metrics-dictionary.json").read_text(encoding="utf-8"))
        self.corpus = json.loads((root / "analytics" / "nfl-metric-validation-corpus.json").read_text(encoding="utf-8"))

    def test_corpus_covers_required_domains_and_dictionary(self):
        result = validate_analytics_corpus(self.corpus, self.dictionary)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["record_count"], 12)
        self.assertEqual(set(result["domains"]), {"offense", "defense", "special_teams", "player", "play", "drive", "game_plan"})

    def test_corpus_rejects_missing_denominator_and_lineage(self):
        invalid = dict(self.corpus)
        invalid["records"] = [dict(self.corpus["records"][0], denominator_definition="", lineage_fields=[])]
        result = validate_analytics_corpus(invalid, self.dictionary)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("denominator_definition" in error for error in result["errors"]))
        self.assertTrue(any("lineage fields" in error for error in result["errors"]))
