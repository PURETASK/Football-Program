import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import FootballIntelligenceService, JsonRepository
from test_play_compiler import valid_play


class RepositoryServiceTests(unittest.TestCase):
    def test_repository_round_trip_revision_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            saved = repository.put("objects", "OBJ-1", {"value": "first"}, actor="test", reason="create")
            self.assertEqual(saved["_revision"], 1)
            updated = repository.put("objects", "OBJ-1", {"value": "second"}, actor="test", reason="update")
            self.assertEqual(updated["_revision"], 2)
            reopened = JsonRepository(Path(directory) / "state.json")
            self.assertEqual(reopened.get("objects", "OBJ-1")["value"], "second")
            self.assertEqual(len(reopened.history(record_id="OBJ-1")), 2)

    def test_service_publishes_play_and_creates_traceable_lesson(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            play = service.publish_play(valid_play(), actor="coach-1")
            self.assertEqual(play["_revision"], 1)
            lesson = service.create_lesson(play_id="PLAY-001", learner_role="QB", actor="coach-1")
            self.assertEqual(lesson["source_play_id"], "PLAY-001")
            self.assertEqual(len(repository.history(collection="lessons")), 1)

    def test_service_rejects_invalid_play_and_records_audit_event(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            play = valid_play()
            play["assignments"] = []
            with self.assertRaises(ValueError):
                service.publish_play(play, actor="coach-1")
            self.assertEqual(len(repository.list("compile_rejections")), 1)
            self.assertEqual(repository.history(collection="compile_rejections")[0]["reason"], "play_compiler_rejection")

    def test_service_persists_permission_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            handoff = service.create_handoff(
                handoff_id="HANDOFF-100", from_agent="AGT-001", to_agent="AGT-007", workflow_id="WF-004",
                payload={"play_id": "PLAY-001"}, actor="orchestrator", requested_permissions={"lock_playbook"},
            )
            self.assertEqual(handoff["status"], "rejected")
            self.assertEqual(repository.get("handoffs", "HANDOFF-100")["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
