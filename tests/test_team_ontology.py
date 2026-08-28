import unittest
import tempfile
from pathlib import Path

from nfl_fidos import JsonRepository, TeamOntologyService, TenantRepository, validate_team_alias_record


class TeamOntologyTests(unittest.TestCase):
    def test_team_alias_is_persistent_scoped_and_conflict_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(repository, organization_id="ORG-TEAM", actor="OWNER")
            service = TeamOntologyService(tenant)
            saved = service.lock_alias(team_id="TEAM-A", alias="Blue Right", term_id="TERM-FORMATION-SHOTGUN", owner="OWNER", reason="playbook terminology", source_refs=["ORG-SOURCE-1"], approval_ref="APPROVAL-1", actor="OWNER")
            self.assertEqual(saved["status"], "locked")
            self.assertEqual(validate_team_alias_record(saved), [])
            resolved = service.resolve(team_id="TEAM-A", value="blue right")
            self.assertEqual(resolved["status"], "resolved_team_alias")
            self.assertEqual(service.list_aliases(team_id="TEAM-A")[0]["id"], saved["id"])
            with self.assertRaises(ValueError):
                service.lock_alias(team_id="TEAM-A", alias="Blue Right", term_id="TERM-CONCEPT-MESH", owner="OWNER", reason="conflict", source_refs=["ORG-SOURCE-1"], approval_ref="APPROVAL-2", actor="OWNER")

    def test_lock_requires_source_and_approval_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            service = TeamOntologyService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-TEAM", actor="OWNER"))
            with self.assertRaises(ValueError):
                service.lock_alias(team_id="TEAM-A", alias="Blue Right", term_id="TERM-FORMATION-SHOTGUN", owner="OWNER", reason="missing evidence", source_refs=[], approval_ref="", actor="OWNER")


if __name__ == "__main__":
    unittest.main()
