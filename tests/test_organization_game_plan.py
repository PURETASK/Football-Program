import unittest

from nfl_fidos.organization_game_plan import approve_organization_game_plan, build_organization_game_plan


def valid_plan():
    return {"id": "GAMEPLAN-ORG-001", "identity": {"offense": "wide_zone", "defense": "match"}, "assumptions": ["sample is current"], "evidence_refs": ["SCOUT-REPORT-1"], "offense": {"base_calls": ["run"]}, "defense": {"base_calls": ["fit"]}, "special_teams": {"base_calls": ["punt"]}, "opening_script": [{"call": "run", "owner": "OC"}], "base_calls": [{"call": "run", "owner": "OC"}], "shot_plan": [{"call": "play_action", "owner": "OC"}], "pressure_answers": [{"threat": "pressure", "answer": "hot", "owner": "OC"}], "situational_plans": [{"situation": "third_down", "primary": "concept_a", "opponent_responses": ["pressure"], "counters": ["hot"]}], "matchups": [{"player": "WR1", "opponent": "CB1", "plan": "release"}], "contingencies": [{"id": "TRIGGER-ORG-001", "trigger": "pressure_rate>40%", "response": "change protection", "owner": "OC", "evidence_refs": ["SCOUT-REPORT-1"]}], "ownership": {"head_coach": "HC", "offense": "OC", "defense": "DC", "special_teams": "STC"}, "teaching_outputs": [{"role": "QB", "message": "confirm pressure"}], "in_game_update": {"cadence": "series", "owner": "HC"}}


class OrganizationGamePlanTests(unittest.TestCase):
    def test_package_compiles_and_owner_validation_is_non_activating(self):
        package = build_organization_game_plan(package_id="ORG-GAMEPLAN-001", organization_id="ORG-1", season="2026", team_context="TEAM-1", week_context="WEEK-1", plan=valid_plan(), compiler="COACH-1")
        self.assertEqual(package["status"], "under_review")
        approved = approve_organization_game_plan(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-GAMEPLAN-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_missing_teaching_output_is_rejected(self):
        plan = valid_plan()
        plan["teaching_outputs"] = []
        package = build_organization_game_plan(package_id="ORG-GAMEPLAN-002", organization_id="ORG-1", season="2026", team_context="TEAM-1", week_context="WEEK-1", plan=plan, compiler="COACH-1")
        self.assertEqual(package["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
