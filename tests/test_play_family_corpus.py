import copy
import json
import unittest
from pathlib import Path

from nfl_fidos.play_family_corpus import validate_play_family_corpus


class PlayFamilyCorpusTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "playbook" / "play-family-corpus.json"
        self.corpus = json.loads(path.read_text(encoding="utf-8"))

    def test_cross_unit_corpus_compiles_with_red_team_checks(self):
        result = validate_play_family_corpus(self.corpus)
        self.assertEqual(result["status"], "valid", result)
        self.assertEqual(result["play_count"], 6)
        self.assertEqual(set(result["units"]), {"offense", "defense", "special_teams"})

    def test_missing_unit_core_role_is_rejected(self):
        invalid = copy.deepcopy(self.corpus)
        invalid["plays"][2]["assignments"] = [{"role":"CB1","assignment":"match"}]
        result = validate_play_family_corpus(invalid)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("PLAY-CORE-ROLES" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
