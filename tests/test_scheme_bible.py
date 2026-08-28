import json
import unittest
from pathlib import Path

from nfl_fidos.scheme_bible import validate_scheme_bible, validate_scheme_dossier


class SchemeBibleTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "scheme" / "scheme-bible.json"
        self.bible = json.loads(path.read_text(encoding="utf-8"))

    def test_starter_scheme_bible_is_compositional_and_complete(self):
        result = validate_scheme_bible(self.bible)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["family_count"], 6)
        self.assertEqual(result["units"], ["defense", "offense"])

    def test_dossier_requires_counter_counter_logic(self):
        dossier = dict(self.bible["families"][0])
        dossier["counter_counters"] = []
        self.assertTrue(any(issue["code"] == "DOSSIER-LIST" for issue in validate_scheme_dossier(dossier)))

    def test_unknown_unit_is_rejected(self):
        dossier = dict(self.bible["families"][0])
        dossier["unit"] = "special_teams"
        self.assertTrue(any(issue["code"] == "DOSSIER-UNIT" for issue in validate_scheme_dossier(dossier)))
