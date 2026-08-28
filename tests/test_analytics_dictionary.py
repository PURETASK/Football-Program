import json
import unittest
from pathlib import Path

from nfl_fidos.analytics_dictionary import build_analytics_report, calculate_metric, validate_metrics_dictionary


class AnalyticsDictionaryTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "analytics" / "metrics-dictionary.json"
        self.dictionary = json.loads(path.read_text(encoding="utf-8"))

    def test_dictionary_has_complete_metric_definitions(self):
        result = validate_metrics_dictionary(self.dictionary)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["metric_count"], 12)

    def test_metric_calculation_preserves_context_and_uncertainty(self):
        definition = self.dictionary["metrics"][0]
        result = calculate_metric(definition=definition, numerator=5, denominator=9, context={"team":"TEAM-1","situation":"third_down"}, source={"kind":"charting","ref":"DATA-1"}, observation_ids=["PLAY-1"])
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["rate"], 5 / 9)
        self.assertIn("interval", result["uncertainty"])
        self.assertFalse(result["generalization_allowed"])

    def test_report_rejects_invalid_observations(self):
        result = build_analytics_report(report_id="ANALYTICS-REPORT-001", audience="coach_staff", metric_observations=[{"id":"METRIC-OBS-1","status":"invalid"}], context={"season":"2026"}, caveats=["small sample"], analyst="ANALYST")
        self.assertEqual(result["status"], "invalid")
