import unittest

from nfl_fidos.game_plan_architecture import build_countermeasure, build_weekly_game_plan


class GamePlanArchitectureTests(unittest.TestCase):
    def plan(self):
        return build_weekly_game_plan(
            plan_id="GAMEPLAN-001", team_context="TEAM-1", week_context="week_1", identity={"offense":"wide_zone","defense":"match"}, assumptions=["sample is current"], evidence_refs=["SCOUT-1"], offense={"base_calls":["run"]}, defense={"base_calls":["fit"]}, special_teams={"base_calls":["punt"]}, opening_script=[{"call":"run","owner":"OC"}], base_calls=[{"call":"run","owner":"OC"}], shot_plan=[{"call":"play_action","owner":"OC"}], pressure_answers=[{"threat":"pressure","answer":"hot","owner":"OC"}], situational_plans=[{"situation":"third_down","primary":"concept_a","opponent_responses":["pressure"],"counters":["hot"]}], matchups=[{"player":"WR1","opponent":"CB1","plan":"release"}], contingencies=[{"id":"TRIGGER-1","trigger":"pressure_rate>40%","response":"change protection","owner":"OC","evidence_refs":["FILM-1"]}], ownership={"head_coach":"HC","offense":"OC","defense":"DC","special_teams":"STC"}, teaching_outputs=[{"role":"QB","message":"confirm pressure"}], in_game_update={"cadence":"series","owner":"HC"},
        )

    def test_plan_contains_counters_and_teaching_outputs(self):
        result = self.plan()
        self.assertEqual(result["status"], "under_review")
        self.assertTrue(result["human_decision_required"])

    def test_countermeasure_requires_counter_counter(self):
        result = build_countermeasure(countermeasure_id="COUNTERMEASURE-001", threat="pressure", primary_response="hot", opponent_counter="drop", counter_counter="screen", trigger="pressure look", evidence_refs=["FILM-1"], owner="OC")
        self.assertEqual(result["status"], "draft")

    def test_plan_rejects_missing_trigger_owner(self):
        result = self.plan()
        result["contingencies"][0].pop("owner")
        from nfl_fidos.game_plan_architecture import validate_game_plan
        self.assertTrue(validate_game_plan(result))
