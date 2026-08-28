import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import run_player_development_loop, run_scheme_selection, run_weekly_team_loop
from test_play_compiler import valid_play
from test_scheme import offense_scheme


class WorkflowTests(unittest.TestCase):
    def test_player_development_loop_composes_lesson_practice_and_evaluation(self):
        result = run_player_development_loop(
            run_id="RUN-PLAYER-001", play=valid_play(), learner_role="QB",
            drills=[{"id": "DRILL-1", "skill": "read", "evaluation": "4 of 5 correct"}],
            assessment={"baseline": "needs work"},
        )
        self.assertEqual(result["workflow_id"], "WF-001")
        self.assertEqual(result["status"], "ready_for_review")
        self.assertEqual(len(result["outputs"]), 3)
        self.assertTrue(result["review_required"])

    def test_player_development_loop_blocks_when_drill_is_incomplete(self):
        result = run_player_development_loop(
            run_id="RUN-PLAYER-002", play=valid_play(), learner_role="QB", drills=[{"id": "DRILL-1"}], assessment={"baseline": "x"},
        )
        self.assertEqual(result["status"], "blocked")

    def test_scheme_selection_keeps_options_and_human_decision(self):
        result = run_scheme_selection(run_id="RUN-SCHEME-001", candidate_schemes=[offense_scheme()], problem="solve pressure", evidence_refs=["EVD-1"])
        self.assertEqual(result["workflow_id"], "WF-003")
        self.assertEqual(result["status"], "ready_for_review")
        self.assertTrue(result["review_required"])
        self.assertEqual(len(result["outputs"][0]["options"]), 1)

    def test_weekly_team_loop_blocks_on_invalid_input(self):
        result = run_weekly_team_loop(
            run_id="RUN-WEEK-001", team_context="TEAM-A", self_scout={"status": "draft"},
            opponent_scout={"status": "valid"}, practice_plan={"status": "draft"}, game_plan={"status": "invalid"},
        )
        self.assertEqual(result["workflow_id"], "WF-002")
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
