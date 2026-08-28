import tempfile
import unittest
from pathlib import Path

from nfl_fidos.film_intelligence import build_film_observation
from nfl_fidos.film_room_service import FilmRoomService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


def record(record_id="FILM-FTS-001", organization_id="ORG-FTS"):
    output = build_film_observation(observation_id=record_id, clip_id="CLIP-FTS-001", asset_id="ASSET-FTS-001", domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="ANALYST", evidence="rotation visible")
    output["organization_id"] = organization_id
    return output


class FilmSearchTests(unittest.TestCase):
    def test_sqlite_fts_search_persists_and_filters_by_tenant(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "film.sqlite3"
            first_repository = SqliteRepository(database)
            second_repository = SqliteRepository(database)
            other_repository = SqliteRepository(database)
            try:
                first = FilmRoomService(TenantRepository(first_repository, organization_id="ORG-FTS", actor="ANALYST"))
                first.save_observation(record(), actor="ANALYST")
                second = FilmRoomService(TenantRepository(second_repository, organization_id="ORG-FTS", actor="COACH"))
                self.assertEqual([item["id"] for item in second.search(query="rotation", opponent="TEAM-2")], ["FILM-FTS-001"])
                other = FilmRoomService(TenantRepository(other_repository, organization_id="ORG-OTHER", actor="COACH"))
                self.assertEqual(other.search(query="rotation"), [])
            finally:
                first_repository.close()
                second_repository.close()
                other_repository.close()

    def test_json_repository_retains_safe_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FilmRoomService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-FTS", actor="ANALYST"))
            service.save_observation(record(), actor="ANALYST")
            self.assertEqual(len(service.search(query="rotation")), 1)


if __name__ == "__main__":
    unittest.main()
