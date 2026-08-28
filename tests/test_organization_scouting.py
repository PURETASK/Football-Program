import unittest

from nfl_fidos.organization_scouting import approve_organization_scouting_package, build_organization_scouting_package


class OrganizationScoutingTests(unittest.TestCase):
    def _profile(self):
        return {"id": "OPP-PROFILE-001", "schedule_context": {"week": 1}, "roster_context": {"status": "review"}, "offense": {"status": "review"}, "defense": {"status": "review"}, "special_teams": {"status": "review"}, "sources": [{"kind": "team_film", "ref": "AUTH-SOURCE-001", "captured_at": "2026-08-23T00:00:00Z"}]}

    def test_package_compiles_and_owner_validation_is_non_activating(self):
        package = build_organization_scouting_package(package_id="ORG-SCOUT-001", organization_id="ORG-1", opponent="TEAM-OPP-1", season="2026", source_refs=["AUTH-SOURCE-001"], profile=self._profile(), reports=[{"id": "SCOUT-REPORT-001", "situation": {"down": 3}, "claims": [{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample"], "evidence_refs": ["AUTH-SOURCE-001"]}], "sample_size": 4, "source_refs": ["AUTH-SOURCE-001"]}], matchups=[], evolutions=[], analyst="ANALYST-1")
        self.assertEqual(package["status"], "under_review")
        approved = approve_organization_scouting_package(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-SCOUT-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_report_source_outside_package_is_rejected(self):
        profile = self._profile()
        package = build_organization_scouting_package(package_id="ORG-SCOUT-002", organization_id="ORG-1", opponent="TEAM-OPP-1", season="2026", source_refs=["AUTH-SOURCE-001"], profile=profile, reports=[{"id": "SCOUT-REPORT-002", "situation": {"down": 3}, "claims": [{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample"], "evidence_refs": ["AUTH-SOURCE-002"]}], "sample_size": 4, "source_refs": ["AUTH-SOURCE-002"]}], matchups=[], evolutions=[], analyst="ANALYST-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-SCOUT-SOURCE-LINK" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
