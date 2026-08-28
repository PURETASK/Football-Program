import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import FootballIntelligenceService, SqliteRepository
from test_play_compiler import valid_play


class SqliteRepositoryTests(unittest.TestCase):
    def test_sqlite_round_trip_revisions_and_audit_events(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteRepository(Path(directory) / "fidos.db")
            try:
                first = repository.put("objects", "OBJ-1", {"value": "one"}, actor="test", reason="create")
                second = repository.put("objects", "OBJ-1", {"value": "two"}, actor="test", reason="update")
                self.assertEqual(first["_revision"], 1)
                self.assertEqual(second["_revision"], 2)
                self.assertEqual(repository.get("objects", "OBJ-1")["value"], "two")
                self.assertEqual(len(repository.history(record_id="OBJ-1")), 2)
            finally:
                repository.close()

    def test_service_works_with_sqlite_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SqliteRepository(Path(directory) / "fidos.db")
            try:
                service = FootballIntelligenceService(repository)
                service.publish_play(valid_play(), actor="coach-1")
                lesson = service.create_lesson(play_id="PLAY-001", learner_role="QB", actor="coach-1")
                self.assertEqual(lesson["source_play_id"], "PLAY-001")
                self.assertEqual(repository.get("lessons", lesson["id"])["workflow_id"], "WF-001")
            finally:
                repository.close()


if __name__ == "__main__":
    unittest.main()
