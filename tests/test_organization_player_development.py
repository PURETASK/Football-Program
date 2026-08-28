import unittest

from nfl_fidos.organization_player_development import approve_organization_player_development, build_organization_player_development


class OrganizationPlayerDevelopmentTests(unittest.TestCase):
    def test_player_package_and_owner_validation_are_non_activating(self):
        package = build_organization_player_development(package_id="ORG-PLAYER-DEV-001", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", players=[{"player_id": "PLAYER-1", "position": "QB", "owner": "COACH-1", "objectives": [{"capability_id": "CAP-001", "outcome": "execute assignment", "measure": "4 of 5 reps"}], "mastery_records": [{"record_id": "MASTERY-PLAYER-1-001", "capability_id": "CAP-001", "current_level": "developing", "target_level": "functional", "evidence": [{"source_ref": "AUTH-SOURCE-001", "observation": "practice rep"}], "next_actions": ["repeat read progression"]}]}], compiler="COACH-1")
        self.assertEqual(package["status"], "under_review")
        approved = approve_organization_player_development(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-PLAYER-DEV-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_incomplete_plan_is_rejected(self):
        package = build_organization_player_development(package_id="ORG-PLAYER-DEV-002", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", players=[{"player_id": "PLAYER-1", "position": "QB", "objectives": [{"capability_id": "CAP-001", "outcome": "execute"}]}], compiler="COACH-1")
        self.assertEqual(package["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
