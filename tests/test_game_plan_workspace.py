import tempfile
import unittest
from pathlib import Path

from nfl_fidos.game_plan_workspace import build_game_plan_workspace
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class GamePlanWorkspaceTests(unittest.TestCase):
    def test_workspace_aggregates_evidence_and_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-PLAN", actor="COACH")
            repository.put("game_plans", "GAMEPLAN-001", {"id":"GAMEPLAN-001", "organization_id":"ORG-PLAN", "week":"WEEK-1", "status":"under_review", "primary_calls":["CALL-1"]}, reason="fixture")
            repository.put("scouting_reports", "SCOUT-001", {"id":"SCOUT-001", "organization_id":"ORG-PLAN", "status":"under_review"}, reason="fixture")
            repository.put("metric_observations", "METRIC-001", {"id":"METRIC-001", "organization_id":"ORG-PLAN", "status":"valid"}, reason="fixture")
            repository.put("release_candidates", "RC-001", {"id":"RC-001", "organization_id":"ORG-PLAN", "status":"blocked", "blockers":["approval required"]}, reason="fixture")
            result = build_game_plan_workspace(repository=repository, week="WEEK-1")
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["pending_review_count"], 2)
            self.assertIn("approval required", result["blockers"])
            self.assertTrue(result["human_approval_required"])


if __name__ == "__main__":
    unittest.main()
