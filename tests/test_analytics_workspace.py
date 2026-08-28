import tempfile
import unittest
from pathlib import Path

from nfl_fidos.analytics_workspace import AnalyticsWorkspaceService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class AnalyticsWorkspaceTests(unittest.TestCase):
    def test_report_workspace_preserves_lineage_and_uncertainty(self):
        with tempfile.TemporaryDirectory() as directory:
            service = AnalyticsWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-ANALYTICS", actor="ANALYST"))
            observation = {"id":"METRIC-OBS-001", "metric_id":"METRIC-DEF-001", "numerator":6, "denominator":10, "rate":0.6, "confidence":"moderate", "uncertainty":{"method":"wilson", "interval":[0.3,0.8]}, "context":{"situation":"third_down"}, "source":{"kind":"charting", "ref":"FILM-1"}, "observation_ids":["PLAY-1"], "status":"valid"}
            report = service.create_report(report_id="ANALYTICS-REPORT-001", audience="coach_staff", metric_observations=[observation], context={"situation":"third_down"}, caveats=["sample only"], analyst="ANALYST", actor="ANALYST")
            self.assertEqual(report["status"], "draft")
            workspace = service.workspace(situation="third_down")
            self.assertEqual(workspace["status"], "ready")
            self.assertEqual(workspace["lineage_complete_count"], 1)
            self.assertEqual(workspace["uncertainty_count"], 1)
            self.assertEqual(workspace["review_count"], 1)


if __name__ == "__main__":
    unittest.main()
