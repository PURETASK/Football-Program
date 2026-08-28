import unittest

from nfl_fidos.organization_drill_validation import approve_organization_drill_validation, build_organization_drill_validation


class OrganizationDrillValidationTests(unittest.TestCase):
    def test_valid_selection_is_under_review(self):
        package = build_organization_drill_validation(validation_id="ORG-DRILL-VALIDATION-001", organization_id="ORG-1", season="2026", position="QB", selected_drill_ids=["DRILL-QB-001", "VARIANT-DRILL-QB-OFFSEASON-001"], source_refs=["AUTH-SOURCE-001"], validator="COACH-1")
        self.assertEqual(package["status"], "under_review")
        self.assertTrue(package["human_review_required"])
        self.assertEqual(package["issues"], [])

    def test_unknown_or_mismatched_selection_is_rejected(self):
        package = build_organization_drill_validation(validation_id="ORG-DRILL-VALIDATION-002", organization_id="ORG-1", season="2026", position="QB", selected_drill_ids=["DRILL-DB-001", "DRILL-MISSING-001"], source_refs=["AUTH-SOURCE-001"], validator="COACH-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-DRILL-POSITION-LINK" for issue in package["issues"]))
        self.assertTrue(any(issue["code"] == "ORG-DRILL-UNKNOWN" for issue in package["issues"]))

    def test_only_owner_decision_can_validate_package(self):
        package = build_organization_drill_validation(validation_id="ORG-DRILL-VALIDATION-003", organization_id="ORG-1", season="2026", position="QB", selected_drill_ids=["DRILL-QB-001"], source_refs=["AUTH-SOURCE-001"], validator="COACH-1")
        rejected = approve_organization_drill_validation(package=package, approver="COACH-1", approver_role="coach_staff", decision_ref="DEC-001")
        self.assertEqual(rejected["status"], "under_review")
        validated = approve_organization_drill_validation(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-DRILL-001")
        self.assertEqual(validated["status"], "validated")
        self.assertFalse(validated["production_implementation_allowed"])
        self.assertFalse(validated["stage_advance_authorized"])


if __name__ == "__main__":
    unittest.main()
