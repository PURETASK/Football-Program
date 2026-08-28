import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_player_lesson
from test_play_compiler import valid_play


class PlayerLearningTests(unittest.TestCase):
    def test_lesson_is_role_specific_and_traceable(self):
        lesson = build_player_lesson(valid_play(), "QB")
        self.assertEqual(lesson["capability_id"], "CAP-001")
        self.assertEqual(lesson["workflow_id"], "WF-001")
        self.assertEqual(lesson["assignment"], "read coverage and execute concept")
        self.assertEqual(lesson["provenance"]["ref"], "PB-001")
        self.assertEqual(len(lesson["checks"]), 3)

    def test_lesson_rejects_unassigned_role(self):
        with self.assertRaises(ValueError) as raised:
            build_player_lesson(valid_play(), "TE")
        self.assertEqual(raised.exception.args[0]["code"], "LESSON-ROLE-NOT-IN-PLAY")


if __name__ == "__main__":
    unittest.main()
