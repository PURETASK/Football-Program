import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import compile_play


def valid_play():
    return {
        "id": "PLAY-001",
        "version": "0.1.0",
        "team_context": "TEAM-EXAMPLE",
        "situation": {"down": 3, "distance": 6, "field_zone": "open_field"},
        "personnel": "11",
        "formation": "shotgun",
        "motion": None,
        "assignments": [
            {"role": "QB", "assignment": "read coverage and execute concept"},
            {"role": "C", "assignment": "identify protection point"},
            {"role": "WR1", "assignment": "run vertical route"}
        ],
        "source": {"kind": "team_playbook", "ref": "PB-001"},
        "status": "draft"
    }


class PlayCompilerTests(unittest.TestCase):
    def test_valid_draft_compiles_and_promotes_to_validated(self):
        result = compile_play(valid_play())
        self.assertTrue(result.valid)
        self.assertEqual(result.issues, ())
        self.assertEqual(result.normalized_play["status"], "validated")


    def test_missing_core_assignment_is_rejected(self):
        play = valid_play()
        play["assignments"] = [{"role": "WR1", "assignment": "run route"}]
        result = compile_play(play)
        self.assertFalse(result.valid)
        self.assertTrue(any(issue.code == "PLAY-CORE-ROLES" for issue in result.issues))
        self.assertEqual(result.normalized_play["status"], "rejected")


    def test_invalid_context_and_provenance_are_rejected(self):
        play = valid_play()
        play["situation"]["down"] = 5
        play["source"] = {"kind": "team_playbook"}
        result = compile_play(play)
        codes = {issue.code for issue in result.issues}
        self.assertTrue({"PLAY-DOWN", "PLAY-SOURCE"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()
