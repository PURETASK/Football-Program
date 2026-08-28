import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import (
    answer_rule_request,
    build_metric_observation,
    build_performance_note,
)


def authoritative_rule():
    return {
        "id": "RULE-001",
        "jurisdiction": "NFL",
        "rule_text": "Authoritative rule text supplied by the registered source.",
        "source": {"kind": "official_rulebook", "ref": "NFL-RULEBOOK-001", "retrieved_at": "2026-08-23"},
        "effective_date": "2026-01-01",
        "authority_level": "authoritative",
    }


class RulesPerformanceAnalyticsTests(unittest.TestCase):
    def test_authoritative_rule_answer_is_source_linked(self):
        answer = answer_rule_request(
            request_id="RULE-REQUEST-001", question="What is the registered rule?",
            rule=authoritative_rule(), requester_role="coach_staff",
        )
        self.assertEqual(answer["status"], "answered")
        self.assertEqual(answer["source"]["ref"], "NFL-RULEBOOK-001")
        self.assertFalse(answer["human_escalation_required"])

    def test_secondary_rule_source_escalates(self):
        rule = authoritative_rule()
        rule["authority_level"] = "secondary"
        answer = answer_rule_request(
            request_id="RULE-REQUEST-002", question="Question", rule=rule, requester_role="player",
        )
        self.assertEqual(answer["status"], "escalate")
        self.assertTrue(answer["human_escalation_required"])

    def test_performance_note_escalates_health_signals(self):
        note = build_performance_note(
            note_id="PERF-001", athlete_context="individual practice",
            observations=["Reduced repetition quality observed"], recommendations=["Review workload with qualified staff"],
            health_signal_present=True,
        )
        self.assertEqual(note["status"], "requires_staff_review")
        self.assertTrue(note["escalation_required"])
        self.assertEqual(len(note["boundaries"]), 3)

    def test_metric_preserves_denominator_context_and_sample_confidence(self):
        observation = build_metric_observation(
            observation_id="METRIC-001", metric_id="METRIC-DEF-THIRD-DOWN-RATE",
            numerator=4, denominator=8, team="TEAM-A", season="2026",
            situations=["third_and_medium"], source={"kind": "team_dataset", "ref": "DATA-001"},
        )
        self.assertEqual(observation["status"], "valid")
        self.assertEqual(observation["rate"], 0.5)
        self.assertEqual(observation["confidence"], "low")
        self.assertFalse(observation["generalization_allowed"])

    def test_metric_rejects_numerator_above_denominator(self):
        observation = build_metric_observation(
            observation_id="METRIC-002", metric_id="METRIC-DEF-RATE", numerator=9, denominator=4,
            team="TEAM-A", season="2026", situations=["red_zone"], source={"kind": "dataset", "ref": "DATA-002"},
        )
        self.assertEqual(observation["status"], "invalid")
        self.assertEqual(observation["issues"][0]["code"], "METRIC-BOUNDS")


if __name__ == "__main__":
    unittest.main()
