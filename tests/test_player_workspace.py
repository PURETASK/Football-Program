import tempfile
import unittest
from pathlib import Path

from nfl_fidos.player_workspace import PlayerWorkspaceService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class PlayerWorkspaceTests(unittest.TestCase):
    def test_assignment_and_today_workspace_are_player_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            service = PlayerWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-PLAYER", actor="COACH"))
            assignment = service.create_assignment(assignment_id="ASSIGNMENT-001", player_id="PLAYER-1", title="Third-down protection", assignment_type="playbook", artifact_id="PLAY-1", due_date="2026-08-30", owner="COACH", source_refs=["PLAY-1"], actor="COACH")
            self.assertEqual(assignment["status"], "assigned")
            service.repository.put("lessons", "LESSON-1", {"id":"LESSON-1", "organization_id":"ORG-PLAYER", "learner_id":"PLAYER-1", "title":"Protection lesson"}, reason="fixture")
            service.repository.put("lessons", "LESSON-2", {"id":"LESSON-2", "organization_id":"ORG-PLAYER", "learner_id":"PLAYER-2", "title":"Other player lesson"}, reason="fixture")
            today = service.today(player_id="PLAYER-1")
            self.assertEqual(today["status"], "ready")
            self.assertEqual(len(today["assignments"]), 1)
            self.assertEqual([item["id"] for item in today["lessons"]], ["LESSON-1"])
            self.assertEqual(today["next_step"]["id"], "ASSIGNMENT-001")


if __name__ == "__main__":
    unittest.main()
