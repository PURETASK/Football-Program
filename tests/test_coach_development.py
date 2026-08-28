import unittest

from nfl_fidos.coach_development import (
    COACH_ROLES,
    build_coach_development_pathway,
    build_coaching_staff_architecture,
    evaluate_coach_performance,
)


class CoachDevelopmentTests(unittest.TestCase):
    def test_staff_architecture_maps_role_dimensions_and_interfaces(self):
        result = build_coaching_staff_architecture(
            architecture_id="STAFF-001", season="2026", team_context="TEAM-1",
            staff=[{"person_id":"COACH-1", "role":"head_coach", "review_owner":"OWNER"}],
        )
        self.assertEqual(result["status"], "draft")
        self.assertEqual(result["staff"][0]["dimensions"], list(COACH_ROLES["head_coach"]))
        self.assertTrue(result["interfaces"])

    def test_pathway_requires_all_role_dimensions(self):
        result = build_coach_development_pathway(
            pathway_id="PATH-COACH-001", coach_id="COACH-1", role="position_coach", mentor_id="COACH-2",
            objectives=[{"dimension":"technique_teaching", "measure":"observed lesson", "evidence_source":"film"}],
        )
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(issue["code"] == "PATHWAY-DIMENSIONS" for issue in result["issues"]))

    def test_evaluation_is_observable_and_bounded(self):
        ratings = {dimension: 4 for dimension in COACH_ROLES["analyst"]}
        result = evaluate_coach_performance(
            evaluation_id="EVAL-COACH-001", coach_id="COACH-1", role="analyst", ratings=ratings,
            evidence=[{"source":"OBS-1", "observation":"explained denominator"}], evaluator="OWNER",
        )
        self.assertEqual(result["status"], "under_review")
        self.assertTrue(result["human_review_required"])
