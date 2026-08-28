import tempfile
import unittest
from pathlib import Path

from nfl_fidos.scouting_workspace import ScoutingWorkspaceService, build_tendency_explorer
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class ScoutingTendencyExplorerTests(unittest.TestCase):
    def test_server_explorer_normalizes_dimensions_and_detects_explicit_stance_conflict(self):
        reports = [{
            "id": "SCOUT-REPORT-1", "organization_id": "ORG-SCOUT", "opponent": "OPP-1", "sample_size": 12,
            "situation": {"down": 3, "distance": "medium", "coverage": "match"},
            "claims": [
                {"statement": "Trips creates a match check", "stance": "increase", "confidence": "high", "evidence_refs": ["FILM-OBS-1"]},
                {"statement": "Trips is not a match check", "stance": "decrease", "confidence": "high", "evidence_refs": ["FILM-OBS-2"]},
            ],
        }]
        result = build_tendency_explorer(reports=reports, opponent="OPP-1", filters={"down": "3", "coverage": "match"})
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["sample_size_total"], 24)
        self.assertEqual({record["review_gate"] for record in result["records"]}, {"contradiction"})
        self.assertTrue(all(record["evidence_refs"] for record in result["records"]))

    def test_workspace_query_keeps_low_sample_claims_review_gated(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCOUT", actor="ANALYST-1")
            tenant.put("scouting_reports", "SCOUT-REPORT-2", {"id": "SCOUT-REPORT-2", "organization_id": "ORG-SCOUT", "opponent": "OPP-1", "sample_size": 4, "situation": {"down": 3}, "claims": [{"statement": "Pressure tendency", "confidence": "high", "evidence_refs": ["FILM-OBS-3"]}]}, actor="ANALYST-1", reason="fixture")
            result = ScoutingWorkspaceService(tenant).tendency_explorer(opponent="OPP-1", filters={"down": "3"})
            self.assertEqual(result["records"][0]["review_gate"], "low_sample")
            self.assertFalse(result["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
