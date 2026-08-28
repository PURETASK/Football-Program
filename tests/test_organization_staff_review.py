import unittest

from nfl_fidos.organization_staff_review import approve_organization_staff_package, build_organization_staff_package


class OrganizationStaffReviewTests(unittest.TestCase):
    def test_staff_package_and_observable_evaluation_validate(self):
        package = build_organization_staff_package(package_id="ORG-STAFF-001", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", staff=[{"person_id": "STAFF-1", "role": "head_coach", "review_owner": "OWNER-1"}], evaluations=[{"evaluation_id": "EVAL-COACH-001", "coach_id": "STAFF-1", "role": "head_coach", "ratings": {"leadership": 4, "culture": 4, "decision_quality": 3, "staff_alignment": 4, "program_evaluation": 3}, "evidence": [{"source_ref": "AUTH-SOURCE-001", "observation": "weekly review artifact"}], "evaluator": "OWNER-1"}], compiler="COACH-1")
        self.assertEqual(package["status"], "under_review")
        self.assertEqual(package["evaluations"][0]["status"], "under_review")
        approved = approve_organization_staff_package(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-STAFF-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_incomplete_evaluation_is_rejected(self):
        package = build_organization_staff_package(package_id="ORG-STAFF-002", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", staff=[{"person_id": "STAFF-1", "role": "head_coach", "review_owner": "OWNER-1"}], evaluations=[{"coach_id": "STAFF-1", "role": "head_coach", "ratings": {}, "evidence": []}], compiler="COACH-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "COACH-EVAL-DIMENSIONS" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
