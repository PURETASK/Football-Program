import tempfile
import unittest
from pathlib import Path

from nfl_fidos.repository import JsonRepository
from nfl_fidos.scheme_workspace import SchemeWorkspaceService
from nfl_fidos.tenant_repository import TenantRepository


class SchemeWorkspaceTests(unittest.TestCase):
    def test_scheme_workspace_persists_valid_compositional_scheme(self):
        with tempfile.TemporaryDirectory() as directory:
            service = SchemeWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEME", actor="COACH"))
            scheme = {"id":"SCHEME-WORKSPACE-001", "version":"0.1.0", "unit":"offense", "name":"Eval offense", "components":[{"id":"C-1", "kind":"personnel", "label":"11 personnel"},{"id":"C-2", "kind":"formation", "label":"shotgun"},{"id":"C-3", "kind":"concept", "label":"inside_zone"}], "assignments":[{"role":"QB", "responsibility":"read"}], "constraints":[], "source":{"kind":"team_playbook", "ref":"PB-1"}}
            saved = service.save_scheme(scheme=scheme, actor="COACH")
            self.assertEqual(saved["status"], "validated")
            workspace = service.workspace(unit="offense")
            self.assertEqual(workspace["status"], "ready")
            self.assertEqual(workspace["pending_review_count"], 0)


if __name__ == "__main__":
    unittest.main()
