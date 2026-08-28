import tempfile
import unittest
from pathlib import Path

from nfl_fidos.playbook_workspace import PlaybookWorkspaceService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class PlaybookWorkspaceTests(unittest.TestCase):
    def play(self):
        return {"id":"PLAY-WORKSPACE-001", "version":"0.1.0", "unit":"offense", "status":"draft", "team_context":"TEAM-WORKSPACE", "situation":{"down":3,"distance":6,"field_zone":"open_field"}, "personnel":"11", "formation":"shotgun", "motion":None, "assignments":[{"role":"QB","assignment":"read coverage","responsibility":"read coverage"},{"role":"RB","assignment":"check release","responsibility":"check release"},{"role":"WR1","assignment":"win leverage","responsibility":"win leverage"},{"role":"C","assignment":"set protection","responsibility":"set protection"}], "source":{"kind":"team_playbook","ref":"PB-WORKSPACE-001"}}

    def service(self, directory):
        return PlaybookWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-WORKSPACE", actor="COACH"))

    def test_draft_request_and_owner_lock_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            draft = service.create_draft(play=self.play(), play_family_id="PLAY-FAM-WORKSPACE-001", install_level="review", checks=[{"role":"QB","text":"confirm rotation"}], situational_variants=[{"situation":"third_down","variant":"hot"}], opponent_notes=["check pressure"], coaching_notes=["eyes before feet"], dependencies=["SCHEME-WORKSPACE-001"], actor="COACH")
            self.assertEqual(draft["status"], "draft")
            requested = service.request_approval(play_id="PLAY-WORKSPACE-001", requester="COACH", decision_ref="DEC-PLAY-WORKSPACE-001")
            self.assertEqual(requested["approval"]["state"], "pending_approval")
            locked = service.approve(play_id="PLAY-WORKSPACE-001", approver="OWNER", decision_ref="DEC-PLAY-WORKSPACE-002")
            self.assertEqual(locked["status"], "locked")
            self.assertEqual(service.role_view(play_id="PLAY-WORKSPACE-001", role="QB")["status"], "renderable")

    def test_invalid_draft_is_not_persisted_as_publishable(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            result = service.create_draft(play={"id":"PLAY-BAD"}, play_family_id="PLAY-FAM-BAD", install_level="review", checks=[], situational_variants=[], opponent_notes=[], coaching_notes=[], dependencies=[], actor="COACH")
            self.assertEqual(result["status"], "rejected")
            self.assertEqual(service.workspace()["status"], "empty")


if __name__ == "__main__":
    unittest.main()
