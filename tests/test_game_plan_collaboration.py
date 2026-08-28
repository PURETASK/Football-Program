import tempfile
import unittest
from pathlib import Path

from nfl_fidos.game_plan_collaboration import GamePlanCollaborationService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class GamePlanCollaborationTests(unittest.TestCase):
    def service(self, directory):
        return GamePlanCollaborationService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-COLLAB", actor="COACH"))

    def test_evidence_linked_thread_comment_and_decision_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            thread = service.create_thread(thread_id="GAMEPLAN-THREAD-001", plan_id="GAMEPLAN-001", week="WEEK-1", topic="pressure answer", comment="Confirm the simulated pressure answer.", evidence_refs=["CLIP-001", "SCOUT-001"], author="COACH", role="coach_staff")
            self.assertEqual(thread["status"], "open")
            thread = service.append_comment(thread_id="GAMEPLAN-THREAD-001", comment_id="COMMENT-002", comment="Analyst evidence supports the adjustment.", evidence_refs=["SCOUT-002"], author="ANALYST", role="analyst")
            self.assertEqual(len(thread["comments"]), 2)
            resolved = service.resolve_thread(thread_id="GAMEPLAN-THREAD-001", decision="accepted", decision_ref="DEC-GAMEPLAN-001", resolver="OWNER", role="program_owner", rationale="Staff reviewed the cited evidence.")
            self.assertEqual(resolved["status"], "resolved")
            self.assertFalse(resolved["human_decision_required"])

    def test_weak_thread_and_unauthorized_resolution_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.service(directory)
            rejected = service.create_thread(thread_id="BAD", plan_id="GAMEPLAN-001", week="WEEK-1", topic="", comment="", evidence_refs=[], author="PLAYER", role="player")
            self.assertEqual(rejected["status"], "rejected")
            service.create_thread(thread_id="GAMEPLAN-THREAD-002", plan_id="GAMEPLAN-001", week="WEEK-1", topic="coverage", comment="Review coverage.", evidence_refs=["CLIP-1"], author="COACH", role="coach_staff")
            with self.assertRaises(PermissionError):
                service.resolve_thread(thread_id="GAMEPLAN-THREAD-002", decision="accepted", decision_ref="DEC-2", resolver="ANALYST", role="analyst", rationale="not authorized")


if __name__ == "__main__":
    unittest.main()
