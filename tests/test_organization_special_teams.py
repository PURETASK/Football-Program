import unittest

from nfl_fidos.organization_special_teams import approve_organization_special_teams, build_organization_special_teams


class OrganizationSpecialTeamsTests(unittest.TestCase):
    def test_assignment_package_and_owner_validation_are_non_activating(self):
        package = build_organization_special_teams(package_id="ORG-SPECIAL-TEAMS-001", organization_id="ORG-1", team_context="TEAM-1", season="2026", assignments=[{"assignment_id": "ST-ASSIGNMENT-001", "specialist_id": "PLAYER-1", "unit_id": "ST-UNIT-001", "role": "kicker", "responsibilities": ["execute location and trajectory"], "mastery_evidence": [{"source_ref": "AUTH-SOURCE-001", "observation": "practice result"}], "source_ref": "AUTH-SOURCE-001", "review_owner": "COACH-1"}], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(package["status"], "under_review")
        approved = approve_organization_special_teams(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-ST-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_unknown_unit_is_rejected(self):
        package = build_organization_special_teams(package_id="ORG-SPECIAL-TEAMS-002", organization_id="ORG-1", team_context="TEAM-1", season="2026", assignments=[{"assignment_id": "ST-ASSIGNMENT-002", "specialist_id": "PLAYER-1", "unit_id": "ST-UNKNOWN", "role": "kicker", "responsibilities": ["kick"], "mastery_evidence": [{"source_ref": "AUTH-SOURCE-001"}], "source_ref": "AUTH-SOURCE-001", "review_owner": "COACH-1"}], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-ST-UNIT" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
