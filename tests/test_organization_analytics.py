import unittest

from nfl_fidos.organization_analytics import approve_organization_analytics_package, build_organization_analytics_package


class OrganizationAnalyticsTests(unittest.TestCase):
    def _definition(self):
        return {"id": "METRIC-DEF-RATE", "name": "Success rate", "unit": "rate", "definition": "successes", "required_data": ["play_id"], "formula": "numerator / denominator", "context_dimensions": ["situation"], "caveats": ["sample"], "validation_method": "review", "consumers": ["coach_staff"]}

    def test_package_compiles_and_owner_validation_is_non_activating(self):
        package = build_organization_analytics_package(package_id="ORG-ANALYTICS-001", organization_id="ORG-1", season="2026", source_refs=["PROVIDER-001"], observations=[{"observation_id": "METRIC-OBS-001", "definition": self._definition(), "numerator": 5, "denominator": 10, "context": {"situation": "third_down"}, "source_ref": "PROVIDER-001", "observation_ids": ["PLAY-1"]}], reports=[{"id": "ANALYTICS-REPORT-001", "audience": "coach_staff", "observation_ids": ["METRIC-OBS-001"], "context": {"situation": "third_down"}, "caveats": ["sample"]}], analyst="ANALYST-1")
        self.assertEqual(package["status"], "under_review")
        approved = approve_organization_analytics_package(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-ANALYTICS-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_unknown_report_observation_is_rejected(self):
        package = build_organization_analytics_package(package_id="ORG-ANALYTICS-002", organization_id="ORG-1", season="2026", source_refs=["PROVIDER-001"], observations=[{"observation_id": "METRIC-OBS-001", "definition": self._definition(), "numerator": 5, "denominator": 10, "context": {"situation": "third_down"}, "source_ref": "PROVIDER-001", "observation_ids": ["PLAY-1"]}], reports=[{"id": "ANALYTICS-REPORT-002", "audience": "coach_staff", "observation_ids": ["METRIC-OBS-UNKNOWN"], "context": {"situation": "third_down"}, "caveats": ["sample"]}], analyst="ANALYST-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-ANALYTICS-REPORT-LINK" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
