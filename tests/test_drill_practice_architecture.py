import unittest

from nfl_fidos.drill_library import build_drill, evaluate_drill
from nfl_fidos.practice_architecture import build_practice_architecture


def drill():
    return build_drill(
        drill_id="DRILL-001", name="Read and replace", drill_type="individual", position="QB", target_skill="coverage recognition", competencies=["CAP-003"],
        classification={"contact_level":"non_contact","decision_load":"high"}, setup={"space":"half_field","equipment":["cones"]}, dose={"minutes":8,"reps":12,"intensity":"moderate"},
        coaching_cues=["eyes before feet"], common_errors=["late confirmation"], corrections=["reset vision"], kpis=[{"name":"correct_read_rate","target":0.8}], regressions=["static shell"], progressions=["add rotation"], film_angles=["wide"], safety={"controls":["no contact","hydration"]},
    )


class DrillPracticeArchitectureTests(unittest.TestCase):
    def test_drill_is_linked_and_measurable(self):
        result = drill()
        self.assertEqual(result["status"], "draft")
        evaluation = evaluate_drill(evaluation_id="EVAL-DRILL-001", drill=result, athlete_id="PLAYER-1", observations=[{"kpi":"correct_read_rate","value":0.83}], evaluator="COACH")
        self.assertEqual(evaluation["status"], "under_review")

    def test_practice_maps_periods_and_load(self):
        result = build_practice_architecture(
            practice_id="PRACTICE-001", team_context="TEAM-1", season_phase="regular_season", week_context="week_1", objective="install third down",
            opponent_priorities=["pressure"], periods=[{"id":"PERIOD-1","type":"individual","objective":"read","owner":"QB_COACH","players":["QB"],"minutes":10,"reps":12,"learning_rationale":"read timing","load_rationale":"moderate"}],
            staff_available=["QB_COACH"], facility_constraints=[], load_controls={"max_total_minutes":120,"max_reps_by_position":{"QB":40}}, restrictions=[],
        )
        self.assertEqual(result["status"], "draft")
        self.assertEqual(result["total_minutes"], 10)
        self.assertEqual(result["objective_to_period"][0]["period_ids"], ["PERIOD-1"])

    def test_practice_rejects_excessive_load(self):
        result = build_practice_architecture(
            practice_id="PRACTICE-002", team_context="TEAM-1", season_phase="regular_season", week_context="week_1", objective="install", opponent_priorities=[],
            periods=[{"id":"P-1","type":"team","objective":"x","owner":"COACH","players":["all"],"minutes":50,"reps":1,"learning_rationale":"x","load_rationale":"x"}],
            staff_available=["COACH"], facility_constraints=[], load_controls={"max_total_minutes":30,"max_reps_by_position":{"all":1}}, restrictions=[],
        )
        self.assertEqual(result["status"], "invalid")
