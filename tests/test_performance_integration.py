import unittest

from nfl_fidos.performance_integration import ingest_provider_batch


class PerformanceIntegrationTests(unittest.TestCase):
    def record(self, **overrides):
        value = {"organization_id":"ORG-PERF-INTEGRATION", "observation_id":"PERF-OBS-INTEGRATION-001", "athlete_id":"PLAYER-1", "session_type":"practice", "duration_minutes":60, "repetitions":40, "quality_score":0.8, "season_phase":"regular_season", "position":"QB", "observed_at":"2026-08-23T10:00:00Z"}
        value.update(overrides)
        return value

    def payload(self):
        return {"organization_id":"ORG-PERF-INTEGRATION", "provider":{"kind":"performance_platform", "mode":"read_only", "source_ref":"PROVIDER-PERF-001"}, "batch_id":"PERF-BATCH-INTEGRATION-001", "records":[self.record()], "source_manifest":{"kind":"authorized_analytics", "ref":"SOURCE-PERF-001", "captured_at":"2026-08-23T12:00:00Z"}, "actor":"PERF-STAFF"}

    def test_approved_read_only_provider_batch_is_ingested_without_external_action(self):
        result = ingest_provider_batch(**self.payload())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["accepted_count"], 1)
        self.assertFalse(result["external_provider_called"])
        self.assertFalse(result["external_state_changed"])
        self.assertFalse(result["medical_decision_performed"])

    def test_unapproved_provider_mode_is_rejected_before_ingestion(self):
        payload = self.payload()
        payload["provider"] = {"kind":"performance_platform", "mode":"write", "source_ref":"https://provider.example"}
        result = ingest_provider_batch(**payload)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["accepted_count"], 0)
        self.assertTrue(any("read_only" in issue for issue in result["integration_issues"]))


if __name__ == "__main__":
    unittest.main()
