import unittest

from nfl_fidos.organization_performance import approve_organization_performance, build_organization_performance


class OrganizationPerformanceTests(unittest.TestCase):
    def _records(self):
        return [{"organization_id": "ORG-1", "observation_id": "PERF-OBS-001", "athlete_id": "PLAYER-1", "session_type": "practice", "duration_minutes": 30, "repetitions": 20, "quality_score": 0.9, "season_phase": "regular_season", "position": "WR", "observed_at": "2026-08-23T10:00:00Z"}]

    def test_package_and_owner_validation_preserve_non_medical_boundary(self):
        package = build_organization_performance(package_id="ORG-PERFORMANCE-001", organization_id="ORG-1", season="2026", batch_id="PERF-BATCH-001", records=self._records(), source_manifest={"kind": "practice_tracking", "ref": "SOURCE-PRACTICE-001", "captured_at": "2026-08-23T12:00:00Z"}, readiness_summaries=[{"summary_id": "READINESS-001", "athlete_id": "PLAYER-1", "signals": ["monitor workload"]}], compiler="PERF-STAFF-1")
        self.assertEqual(package["status"], "under_review")
        self.assertFalse(package["medical_decision_performed"])
        approved = approve_organization_performance(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-PERF-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_medical_field_is_rejected(self):
        records = self._records()
        records[0]["diagnosis"] = "not accepted"
        package = build_organization_performance(package_id="ORG-PERFORMANCE-002", organization_id="ORG-1", season="2026", batch_id="PERF-BATCH-002", records=records, source_manifest={"kind": "practice_tracking", "ref": "SOURCE-PRACTICE-001", "captured_at": "2026-08-23T12:00:00Z"}, readiness_summaries=[], compiler="PERF-STAFF-1")
        self.assertEqual(package["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
