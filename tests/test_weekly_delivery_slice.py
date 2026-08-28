import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository
from nfl_fidos.game_plan_architecture import build_weekly_game_plan
from nfl_fidos.rules_knowledge import build_rule_aware_recommendation


def plan():
    return build_weekly_game_plan(
        plan_id="GAMEPLAN-SLICE-001", team_context="TEAM-1", week_context="week_1",
        identity={"offense":"wide_zone", "defense":"match"}, assumptions=["sample is current"], evidence_refs=["SCOUT-REPORT-1"],
        offense={"base_calls":["run"]}, defense={"base_calls":["fit"]}, special_teams={"base_calls":["punt"]},
        opening_script=[{"call":"run", "owner":"OC"}], base_calls=[{"call":"run", "owner":"OC"}], shot_plan=[{"call":"play_action", "owner":"OC"}],
        pressure_answers=[{"threat":"pressure", "answer":"hot", "owner":"OC"}],
        situational_plans=[{"situation":"third_down", "primary":"concept_a", "opponent_responses":["pressure"], "counters":["hot"]}],
        matchups=[{"player":"WR1", "opponent":"CB1", "plan":"release"}],
        contingencies=[{"id":"TRIGGER-SLICE-001", "trigger":"pressure_rate>40%", "response":"change protection", "owner":"OC", "evidence_refs":["SCOUT-REPORT-1"]}],
        ownership={"head_coach":"HC", "offense":"OC", "defense":"DC", "special_teams":"STC"},
        teaching_outputs=[{"role":"QB", "message":"confirm pressure"}], in_game_update={"cadence":"series", "owner":"HC"},
    )


def rule_recommendation():
    return build_rule_aware_recommendation(
        recommendation_id="RULE-REC-SLICE-001", question="fourth down decision", rule_facts=[{"id":"RULE-KB-005", "authority":"authoritative", "fact":"rule fact"}],
        strategy_recommendation="compare options", situation={"down":4, "distance":2, "clock":90}, requester_role="coach_staff", rule_refs=["RULE-KB-005"], evidence_refs=["SCOUT-REPORT-1"],
    )


class WeeklyDeliverySliceTests(unittest.TestCase):
    def test_package_blocks_without_human_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            package = service.create_weekly_delivery_package(
                game_plan=plan(), rule_recommendation=rule_recommendation(), eval_result={"status":"passed"},
                capability_ids=["CAP-018"], feature_gates=[{"id":"GATE-CAP-018", "capability_id":"CAP-018", "status":"complete"}], actor="COACH-1",
            )
            self.assertEqual(package["status"], "blocked")
            self.assertTrue(package["human_approval_required"])
            self.assertIsNotNone(service.repository.get("governance_audits", package["audit_id"]))

    def test_package_becomes_approved_only_with_gates_and_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            package = service.create_weekly_delivery_package(
                game_plan=plan(), rule_recommendation=rule_recommendation(), eval_result={"status":"passed"},
                capability_ids=["CAP-018"], feature_gates=[{"id":"GATE-CAP-018", "capability_id":"CAP-018", "status":"complete"}], actor="COACH-1", human_approval="APPROVAL-OWNER-1",
            )
            self.assertEqual(package["status"], "approved")
            self.assertEqual(service.repository.get("release_candidates", package["release_id"])["status"], "approved")


if __name__ == "__main__":
    unittest.main()
