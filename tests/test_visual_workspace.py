import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.tenant_repository import TenantRepository
from nfl_fidos.visual_workspace import VisualWorkspaceService


def visual():
    return {"id":"VISUAL-API-001", "play_id":"PLAY-API-001", "source_play_version":"1.0.0", "players":[{"id":"P-QB", "role":"QB", "position":{"x":10, "y":26.6}}], "paths":[{"player_id":"P-QB", "points":[{"x":10, "y":26.6},{"x":20, "y":26.6}]}], "timeline":[{"time_ms":0, "event":"snap"}], "role_views":["QB","coach"], "accessibility":["QB takes snap and rolls right"]}


class VisualWorkspaceTests(unittest.TestCase):
    def test_visual_is_persisted_and_rendered_for_role(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-VISUAL", actor="coach")
            service = VisualWorkspaceService(tenant)
            saved = service.save_visual(visual(), actor="coach")
            rendered = service.get_visual(saved["id"], role="QB")
            self.assertEqual(saved["status"], "renderable")
            self.assertIn('data-mode="canonical"', rendered["svg"])
            self.assertIn("QB", rendered["svg"])

    def test_invalid_visual_is_not_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-VISUAL", actor="coach")
            record = visual()
            record["paths"][0]["points"] = [{"x":10, "y":26.6}]
            result = VisualWorkspaceService(tenant).save_visual(record, actor="coach")
            self.assertEqual(result["status"], "invalid")
            self.assertIsNone(tenant.get("visual_plays", record["id"]))

    def test_authenticated_api_enforces_tenancy_and_role_boundary(self):
        secret = "visual-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization":"Bearer " + issue_token(subject="COACH-VISUAL", role="coach_staff", organization_id="ORG-VISUAL", secret=secret)}
        player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-VISUAL", role="player", organization_id="ORG-OTHER", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            created = handle_request(method="POST", path="/v1/playbook/visuals", body={"organization_id":"ORG-VISUAL", "visual":visual()}, headers=coach, service=service)
            fetched = handle_request(method="GET", path="/v1/playbook/visual?organization_id=ORG-VISUAL&visual_id=VISUAL-API-001&role=QB", headers=coach, service=service)
            denied = handle_request(method="GET", path="/v1/playbook/visual?organization_id=ORG-VISUAL&visual_id=VISUAL-API-001", headers=player, service=service)
            self.assertEqual(created[0], 201)
            self.assertEqual(fetched[0], 200)
            self.assertIn("<svg", fetched[1]["data"]["svg"])
            self.assertEqual(denied[0], 403)
            scenario = handle_request(method="POST", path="/v1/playbook/visuals/VISUAL-API-001/what-if", body={"organization_id":"ORG-VISUAL", "simulation_id":"SIM-API-001", "adjustment":{"type":"rotate_coverage"}}, headers=coach, service=service)
            self.assertEqual(scenario[0], 201)
            self.assertTrue(scenario[1]["data"]["canonical_unchanged"])
            self.assertIsNone(service.repository.get("visual_plays", "SIM-API-001"))
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
