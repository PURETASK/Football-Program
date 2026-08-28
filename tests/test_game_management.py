import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_game_decision, build_game_situation


class GameManagementTests(unittest.TestCase):
    def situation(self):
        return build_game_situation(
            situation_id="SITUATION-001", quarter=4, clock_seconds=120, score_differential=-3,
            down=4, distance=2, timeouts={"TEAM-A": 1, "TEAM-B": 2}, field_zone="opponent_territory",
            possession="TEAM-A", rule_refs=["RULE-001"],
        )

    def test_situation_requires_complete_context(self):
        situation = self.situation()
        self.assertEqual(situation["status"], "ready")
        self.assertEqual(situation["rule_refs"], ["RULE-001"])

    def test_decision_preserves_options_risk_rules_and_human_review(self):
        decision = build_game_decision(
            decision_id="DECISION-001", situation=self.situation(),
            options=[{"id": "OPTION-A", "action": "attempt conversion", "rationale": "score context", "risk": "turnover"}, {"id": "OPTION-B", "action": "punt", "rationale": "field position", "risk": "possession loss"}],
            rule_refs=["RULE-001"], evidence_refs=["EVD-001"],
        )
        self.assertEqual(decision["status"], "draft")
        self.assertTrue(decision["human_review_required"])
        self.assertEqual(len(decision["options"]), 2)

    def test_decision_rejects_invalid_situation_and_incomplete_option(self):
        situation = self.situation()
        situation["status"] = "invalid"
        decision = build_game_decision(decision_id="DECISION-002", situation=situation, options=[{"id": "OPTION-A"}], rule_refs=["RULE-001"], evidence_refs=[])
        self.assertEqual(decision["status"], "rejected")
        codes = {issue["code"] for issue in decision["issues"]}
        self.assertTrue({"DECISION-SITUATION", "DECISION-OPTION"}.issubset(codes))

    def test_situation_rejects_invalid_clock(self):
        situation = self.situation()
        situation["clock_seconds"] = 901
        invalid = build_game_situation(
            situation_id=situation["id"], quarter=situation["quarter"], clock_seconds=situation["clock_seconds"],
            score_differential=situation["score_differential"], down=situation["down"], distance=situation["distance"],
            timeouts=situation["timeouts"], field_zone=situation["field_zone"], possession=situation["possession"], rule_refs=situation["rule_refs"],
        )
        self.assertEqual(invalid["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
