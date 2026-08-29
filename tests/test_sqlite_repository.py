import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
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

    def test_compare_and_swap_is_atomic_across_independent_connections(self):
        """Separate worker connections must converge on one stale-save winner."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shared.db"
            first = SqliteRepository(path)
            second = SqliteRepository(path)
            try:
                created = first.put("objects", "OBJ-RACE", {"value": "base"}, actor="seed", reason="create")
                barrier = threading.Barrier(2)

                def attempt(repository, value):
                    barrier.wait(timeout=3)
                    try:
                        return ("saved", repository.put_if_revision("objects", "OBJ-RACE", {"value": value}, expected_revision=created["_revision"], actor=value, reason="race"))
                    except ValueError as exc:
                        return ("conflict", exc.args[0])

                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda args: attempt(*args), ((first, "worker-a"), (second, "worker-b"))))
                self.assertEqual(sorted(result[0] for result in results), ["conflict", "saved"])
                winner = next(result[1] for result in results if result[0] == "saved")
                conflict = next(result[1] for result in results if result[0] == "conflict")
                self.assertEqual(winner["_revision"], 2)
                self.assertEqual(conflict["code"], "DESIGN-CONFLICT")
                self.assertEqual(conflict["actual_revision"], winner["_revision"])
                self.assertEqual(first.get("objects", "OBJ-RACE")["value"], winner["value"])
            finally:
                first.close()
                second.close()


if __name__ == "__main__":
    unittest.main()
