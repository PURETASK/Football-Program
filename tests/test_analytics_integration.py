import unittest

from nfl_fidos.analytics_integration import calculate_provider_batch


class AnalyticsIntegrationTests(unittest.TestCase):
    def definition(self):
        return {"id":"METRIC-DEF-TEST-RATE", "name":"Test rate", "unit":"rate", "definition":"successful eligible plays", "required_data":["play_id"], "formula":"numerator / denominator", "context_dimensions":["situation"], "caveats":["sample size"], "validation_method":"manual review", "consumers":["coach_staff"]}

    def payload(self):
        return {"organization_id":"ORG-ANALYTICS-INTEGRATION", "provider":{"kind":"play_charting", "mode":"read_only", "source_ref":"SOURCE-CHART-001"}, "batch_id":"ANALYTICS-BATCH-001", "records":[{"definition":self.definition(), "numerator":8, "denominator":10, "context":{"situation":"third_down"}, "observation_ids":["PLAY-001"]}], "source_manifest":{"kind":"charting_export", "ref":"SOURCE-CHART-001"}, "actor":"ANALYST"}

    def test_provider_batch_calculates_lineage_and_uncertainty(self):
        result = calculate_provider_batch(**self.payload())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["accepted_count"], 1)
        observation = result["accepted"][0]
        self.assertEqual(observation["organization_id"], "ORG-ANALYTICS-INTEGRATION")
        self.assertIn("uncertainty", observation)
        self.assertFalse(result["external_provider_called"])
        self.assertFalse(result["external_state_changed"])

    def test_bad_provider_mode_and_source_are_blocked(self):
        payload = self.payload()
        payload["provider"] = {"kind":"play_charting", "mode":"write", "source_ref":"https://provider.example"}
        result = calculate_provider_batch(**payload)
        self.assertEqual(result["status"], "rejected")
        self.assertTrue(result["batch_issues"])


if __name__ == "__main__":
    unittest.main()
