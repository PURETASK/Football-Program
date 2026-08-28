import unittest

from nfl_fidos.performance_ingestion import ingest_performance_batch


class PerformanceIngestionTests(unittest.TestCase):
    def source(self):
        return {"kind":"wearable_export","ref":"WEARABLE-EXPORT-001","captured_at":"2026-08-23T12:00:00Z"}

    def record(self, **overrides):
        record = {"organization_id":"ORG-PERF","observation_id":"PERF-OBS-BATCH-001","athlete_id":"PLAYER-1","session_type":"practice","duration_minutes":60,"repetitions":40,"quality_score":0.8,"season_phase":"regular_season","position":"QB","observed_at":"2026-08-23T10:00:00Z"}
        record.update(overrides)
        return record

    def test_authorized_batch_preserves_provenance_and_no_medical_action(self):
        result = ingest_performance_batch(batch_id="PERF-BATCH-001", organization_id="ORG-PERF", records=[self.record(health_signal=True)], source_manifest=self.source(), actor="PERF-STAFF")
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["accepted_count"], 1)
        self.assertTrue(result["accepted"][0]["staff_review_required"])
        self.assertFalse(result["medical_decision_performed"])
        self.assertFalse(result["external_provider_called"])

    def test_scope_and_medical_fields_are_rejected(self):
        result = ingest_performance_batch(batch_id="PERF-BATCH-002", organization_id="ORG-PERF", records=[self.record(organization_id="ORG-OTHER", diagnosis="not accepted")], source_manifest=self.source(), actor="PERF-STAFF")
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["accepted_count"], 0)
        self.assertTrue(any("medical decision" in issue for issue in result["rejected"][0]["issues"]))

    def test_unauthorized_source_is_visible_as_batch_issue(self):
        result = ingest_performance_batch(batch_id="PERF-BATCH-003", organization_id="ORG-PERF", records=[self.record()], source_manifest={"kind":"medical_record","ref":"MED-1","captured_at":"2026-08-23T12:00:00Z"}, actor="PERF-STAFF")
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["batch_issues"])


if __name__ == "__main__":
    unittest.main()
