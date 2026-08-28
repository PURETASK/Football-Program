import tempfile
import unittest
from pathlib import Path

from nfl_fidos.approval_inbox import build_approval_inbox
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class ApprovalInboxTests(unittest.TestCase):
    def test_inbox_surfaces_pending_records_and_approval_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-INBOX", actor="ANALYST")
            repository.put("game_plans", "GAMEPLAN-INBOX", {"id":"GAMEPLAN-INBOX", "organization_id":"ORG-INBOX", "status":"under_review", "source_refs":["SCOUT-1"]}, reason="fixture")
            owner = build_approval_inbox(repository=repository, role="program_owner")
            analyst = build_approval_inbox(repository=repository, role="analyst")
            self.assertEqual(owner["count"], 1)
            self.assertTrue(owner["items"][0]["can_approve"])
            self.assertFalse(analyst["items"][0]["can_approve"])
            self.assertEqual(owner["items"][0]["evidence_refs"], ["SCOUT-1"])


if __name__ == "__main__":
    unittest.main()
