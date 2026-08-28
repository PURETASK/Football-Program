import unittest

from nfl_fidos.organization_onboarding import approve_onboarding_package, build_onboarding_package


class OrganizationOnboardingTests(unittest.TestCase):
    def test_onboarding_creates_draft_context_and_bundle_without_activation(self):
        package = build_onboarding_package(
            organization_id="ORG-ONBOARD", name="Evaluation Club", season="2026", team_id="TEAM-ONBOARD",
            people=[{"id":"PLAYER-1", "name":"Player One", "type":"player", "position":"QB"}, {"id":"COACH-1", "name":"Coach One", "type":"coach", "staff_role":"head_coach"}],
            terminology_version="TERM-0.1.0", owner="OWNER-1", source={"kind":"team_system", "ref":"ORG-SOURCE-1"},
        )
        self.assertEqual(package["status"], "draft")
        self.assertEqual(package["organization"]["league"], "NFL")
        self.assertEqual(package["terminology_bundle"]["status"], "draft")
        self.assertTrue(package["approval_required"])
        self.assertFalse(package["production_implementation_allowed"])

    def test_invalid_team_or_invalid_approved_bundle_is_rejected(self):
        package = build_onboarding_package(
            organization_id="ORG-ONBOARD", name="Evaluation Club", season="2026", team_id="BAD-TEAM",
            people=[], terminology_version="TERM-0.1.0", owner="OWNER-1", source={"kind":"team_system", "ref":"ORG-SOURCE-1"},
            terminology_bundle={"id":"TERM-BUNDLE-1", "organization_id":"ORG-ONBOARD", "team_id":"BAD-TEAM", "season":"2026", "version":"TERM-0.1.0", "owner":"OWNER-1", "source_refs":[], "approval_ref":"", "aliases":[], "status":"approved"},
        )
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(package["issues"])

    def test_approval_requires_decision_record_and_activates_only_context(self):
        package = build_onboarding_package(
            organization_id="ORG-ONBOARD", name="Evaluation Club", season="2026", team_id="TEAM-ONBOARD",
            people=[], terminology_version="TERM-0.1.0", owner="OWNER-1", source={"kind":"team_system", "ref":"ORG-SOURCE-1"},
        )
        rejected = approve_onboarding_package(organization=package["organization"], terminology_bundle=package["terminology_bundle"], approver="OWNER-1", decision_ref="BAD")
        self.assertEqual(rejected["status"], "rejected")
        approved = approve_onboarding_package(organization=package["organization"], terminology_bundle=package["terminology_bundle"], approver="OWNER-1", decision_ref="DEC-ORG-001")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(approved["organization"]["status"], "active")
        self.assertEqual(approved["terminology_bundle"]["status"], "approved")
        self.assertFalse(approved["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
