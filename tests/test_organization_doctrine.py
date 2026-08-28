import unittest

from nfl_fidos.organization_doctrine import approve_organization_doctrine, build_organization_doctrine


class OrganizationDoctrineTests(unittest.TestCase):
    def test_reference_package_compiles_and_owner_validation_is_non_activating(self):
        package = build_organization_doctrine(doctrine_id="ORG-DOCTRINE-001", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", scheme_family_ids=["SCHEME-FAM-OFF-001", "SCHEME-FAM-DEF-001"], special_teams_unit_ids=["ST-UNIT-001"], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(package["status"], "under_review")
        self.assertEqual(len(package["entries"]), 3)
        approved = approve_organization_doctrine(doctrine=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-DOCTRINE-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_unknown_reference_is_rejected(self):
        package = build_organization_doctrine(doctrine_id="ORG-DOCTRINE-002", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", scheme_family_ids=["SCHEME-UNKNOWN"], special_teams_unit_ids=[], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-DOCTRINE-SCHEME" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
