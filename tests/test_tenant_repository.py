import tempfile
import unittest
from pathlib import Path

from nfl_fidos.repository import JsonRepository
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


class TenantRepositoryTests(unittest.TestCase):
    def test_json_repository_isolated_by_organization(self):
        with tempfile.TemporaryDirectory() as directory:
            base = JsonRepository(Path(directory) / "state.json")
            one = TenantRepository(base, organization_id="ORG-1", actor="coach-1")
            two = TenantRepository(base, organization_id="ORG-2", actor="coach-2")
            one.put("plays", "PLAY-1", {"id":"PLAY-1", "organization_id":"ORG-1", "status":"draft"})
            with self.assertRaises(PermissionError):
                two.put("plays", "PLAY-2", {"id":"PLAY-2", "organization_id":"ORG-1"})
            self.assertIsNone(two.get("plays", "PLAY-1"))
            self.assertEqual(one.get("plays", "PLAY-1")["organization_id"], "ORG-1")

    def test_sqlite_repository_preserves_scope_and_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            base = SqliteRepository(Path(directory) / "state.db")
            scoped = TenantRepository(base, organization_id="ORG-1", actor="owner-1")
            scoped.put("game_plans", "GAMEPLAN-1", {"id":"GAMEPLAN-1", "organization_id":"ORG-1", "status":"under_review"})
            self.assertEqual(len(scoped.history(collection="game_plans")), 1)
            base.close()

    def test_history_uses_collection_and_record_identity_for_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = JsonRepository(Path(directory) / "state.json")
            one = TenantRepository(base, organization_id="ORG-1", actor="coach-1")
            two = TenantRepository(base, organization_id="ORG-2", actor="coach-2")
            one.put("plays", "SHARED-ID", {"id": "SHARED-ID", "organization_id": "ORG-1"})
            two.put("game_plans", "SHARED-ID", {"id": "SHARED-ID", "organization_id": "ORG-2"})

            visible = one.history()

            self.assertEqual([(event["collection"], event["record_id"]) for event in visible], [("plays", "SHARED-ID")])


if __name__ == "__main__":
    unittest.main()
