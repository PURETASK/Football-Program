import json
import unittest
from pathlib import Path

from nfl_fidos.special_teams_bible import validate_special_teams_bible, validate_special_teams_unit


class SpecialTeamsBibleTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "special_teams" / "special-teams-bible.json"
        self.bible = json.loads(path.read_text(encoding="utf-8"))

    def test_bible_covers_required_units(self):
        result = validate_special_teams_bible(self.bible)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["unit_count"], 6)

    def test_unit_requires_scouting_and_practice_requirements(self):
        unit = dict(self.bible["units"][0])
        unit["scouting_requirements"] = []
        self.assertTrue(any("scouting_requirements" in issue for issue in validate_special_teams_unit(unit)))

    def test_bible_rejects_missing_unit(self):
        bible = json.loads(json.dumps(self.bible))
        bible["units"] = bible["units"][:-1]
        self.assertEqual(validate_special_teams_bible(bible)["status"], "invalid")
