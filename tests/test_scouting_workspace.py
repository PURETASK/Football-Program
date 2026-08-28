import tempfile
import unittest
from pathlib import Path

from nfl_fidos.repository import JsonRepository
from nfl_fidos.scouting_workspace import ScoutingWorkspaceService
from nfl_fidos.tenant_repository import TenantRepository


class ScoutingWorkspaceTests(unittest.TestCase):
    def test_workspace_surfaces_sample_and_adaptation_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            service = ScoutingWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCOUT", actor="ANALYST"))
            service.repository.put("scouting_reports", "SCOUT-001", {"id":"SCOUT-001", "organization_id":"ORG-SCOUT", "opponent":"OPP-1", "sample_size":4, "status":"under_review"}, reason="fixture")
            service.repository.put("opponent_evolutions", "EVOLUTION-001", {"id":"EVOLUTION-001", "organization_id":"ORG-SCOUT", "opponent":"OPP-1", "status":"warning"}, reason="fixture")
            result = service.workspace(opponent="OPP-1")
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["low_sample_count"], 1)
            self.assertEqual(result["adaptation_warning_count"], 1)
            self.assertTrue(result["human_review_required"])


if __name__ == "__main__":
    unittest.main()
