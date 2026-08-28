import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import (
    build_game_plan_options,
    build_practice_plan,
    build_tendency_record,
    qualify_claim,
)


def evidence(sample_size=3):
    return {
        "id": "EVD-001",
        "claim": "Opponent tendency observed in film.",
        "classification": "observed_tendency",
        "source": {"kind": "film", "ref": "FILM-001", "captured_at": "2026-08-23"},
        "context": {"team": "TEAM-A", "opponent": "TEAM-B", "situations": ["third_and_medium"]},
        "sample_size": sample_size,
        "confidence": "low" if sample_size < 5 else "moderate",
    }


class IntelligenceWorkflowTests(unittest.TestCase):
    def test_small_sample_is_not_generalized(self):
        result = qualify_claim(evidence())
        self.assertTrue(result["valid"])
        self.assertFalse(result["generalization_allowed"])
        self.assertTrue(result["limitations"])

    def test_scouting_is_contextual_and_provenance_linked(self):
        record = build_tendency_record(
            record_id="EVD-002", team="TEAM-A", opponent="TEAM-B",
            observations=[
                {"situations": ["third_and_medium"], "response": "pressure"},
                {"situations": ["third_and_medium"], "response": "pressure"},
                {"situations": ["red_zone"], "response": "coverage"},
            ], situation="third_and_medium", source_ref="FILM-SET-1", captured_at="2026-08-23",
        )
        self.assertEqual(record["sample_size"], 2)
        self.assertEqual(record["distribution"], {"pressure": 2})
        self.assertEqual(record["source"]["ref"], "FILM-SET-1")
        self.assertFalse(record["generalization_allowed"])

    def test_practice_requires_measurable_drills(self):
        plan = build_practice_plan(
            plan_id="PRACTICE-001", team_context="TEAM-A", objective="Improve protection communication",
            drills=[{"id": "DRILL-001", "skill": "point identification", "evaluation": "correct point on 4 of 5 reps"}],
            constraints=["no-huddle"],
        )
        self.assertEqual(plan["capability_id"], "CAP-013")
        self.assertEqual(plan["evaluation"][0]["measure"], "correct point on 4 of 5 reps")
        with self.assertRaises(ValueError):
            build_practice_plan(plan_id="PRACTICE-002", team_context="TEAM-A", objective="x", drills=[{"id": "DRILL-002"}])

    def test_game_plan_keeps_human_decision_boundary(self):
        draft = build_game_plan_options(
            problem="Handle third-down pressure",
            evidence=[evidence()],
            options=[{"id": "OPTION-1", "response": "change protection"}, {"id": "OPTION-2", "response": "check to answer"}],
        )
        self.assertEqual(draft["status"], "draft")
        self.assertTrue(draft["countermeasures_required"])
        self.assertTrue(draft["human_decision_required"])
        self.assertEqual(len(draft["evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
