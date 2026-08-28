import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_coach_mastery_plan, build_development_plan, build_mastery_record


class DevelopmentTests(unittest.TestCase):
    def test_mastery_record_requires_upward_evidence_backed_progression(self):
        record = build_mastery_record(
            record_id="MASTERY-001", learner_id="PLAYER-1", capability_id="CAP-001",
            current_level="developing", target_level="proficient", evidence=[{"kind": "film_grade", "ref": "FILM-1"}], next_actions=["reps"],
        )
        self.assertEqual(record["status"], "draft")
        self.assertTrue(record["review_required"])
        invalid = build_mastery_record(
            record_id="MASTERY-002", learner_id="PLAYER-1", capability_id="CAP-001",
            current_level="proficient", target_level="developing", evidence=[{"ref": "x"}], next_actions=["y"],
        )
        self.assertEqual(invalid["status"], "invalid")
        self.assertEqual(invalid["issues"][0]["code"], "MASTERY-TARGET")

    def test_player_idp_requires_measured_objectives(self):
        plan = build_development_plan(
            plan_id="IDP-PLAYER-001", learner_id="PLAYER-1", learner_type="player",
            objectives=[{"capability_id": "CAP-001", "outcome": "execute assignment", "measure": "4 of 5 reps"}], owner="coach-1", review_cadence="weekly",
        )
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["objectives"][0]["measure"], "4 of 5 reps")

    def test_coach_plan_has_coach_dimensions(self):
        plan = build_coach_mastery_plan(
            plan_id="IDP-COACH-001", coach_id="COACH-1",
            objectives=[{"capability_id": "CAP-004", "outcome": "teach concept", "measure": "player check"}], owner="head-coach",
        )
        self.assertEqual(plan["learner_type"], "coach")
        self.assertIn("practice_design", plan["coach_dimensions"])
        self.assertEqual(plan["capability_id"], "CAP-004")

    def test_incomplete_idp_is_held_for_review(self):
        plan = build_development_plan(
            plan_id="IDP-PLAYER-002", learner_id="PLAYER-1", learner_type="player",
            objectives=[{"capability_id": "CAP-001", "outcome": "execute"}], owner="coach-1", review_cadence="weekly",
        )
        self.assertEqual(plan["status"], "under_review")
        self.assertTrue(plan["issues"])


if __name__ == "__main__":
    unittest.main()
