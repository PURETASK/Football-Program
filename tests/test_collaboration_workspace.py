import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.collaboration_workspace import CollaborationWorkspaceService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.tenant_repository import TenantRepository


class CollaborationWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = JsonRepository(Path(self.temporary.name) / "state.json")
        self.tenant = TenantRepository(self.repository, organization_id="ORG-COLLAB", actor="OWNER-COLLAB")
        self.service = CollaborationWorkspaceService(self.tenant)

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        self.temporary.cleanup()

    def test_thread_assignment_notification_resolution_and_visibility(self):
        thread = self.service.create_thread(
            thread_id="COLLAB-THREAD-001",
            title="Confirm pressure answer",
            body="Need coordinator decision before install.",
            entity_type="game_plan",
            entity_id="GAMEPLAN-001",
            deep_link="/game-plan",
            author="OWNER-COLLAB",
            role="program_owner",
            assignee="COACH-1",
            mentions=["ANALYST-1"],
            priority="high",
        )
        self.assertEqual(thread["status"], "open")
        self.assertEqual(thread["assigned_to"], "COACH-1")
        self.assertGreaterEqual(len(self.tenant.list("notifications")), 2)

        replayed = self.service.create_thread(
            thread_id="COLLAB-THREAD-001",
            title="Confirm pressure answer",
            body="Need coordinator decision before install.",
            entity_type="game_plan",
            entity_id="GAMEPLAN-001",
            deep_link="/game-plan",
            author="OWNER-COLLAB",
            role="program_owner",
            assignee="COACH-1",
            mentions=["ANALYST-1"],
            priority="high",
        )
        self.assertEqual(replayed["id"], thread["id"])
        self.assertEqual(len(self.tenant.list("collaboration_activity")), 1)

        thread = self.service.append_comment(thread_id=thread["id"], comment_id="COMMENT-001", body="Film evidence attached.", mentions=["COACH-1"], author="ANALYST-1", role="analyst")
        self.assertEqual(len(thread["comments"]), 2)
        replayed = self.service.append_comment(thread_id=thread["id"], comment_id="COMMENT-001", body="Film evidence attached.", mentions=["COACH-1"], author="ANALYST-1", role="analyst")
        self.assertEqual(len(replayed["comments"]), 2)
        thread = self.service.assign_thread(thread_id=thread["id"], assignee="COACH-2", due_at="2026-08-28T16:00:00Z", priority="critical", actor="OWNER-COLLAB", role="program_owner")
        self.assertEqual(thread["priority"], "critical")
        thread = self.service.resolve_thread(thread_id=thread["id"], decision="resolved", rationale="Coordinator accepted the answer.", actor="OWNER-COLLAB", role="program_owner")
        self.assertEqual(thread["status"], "resolved")

        events = self.service.events()
        self.assertGreaterEqual(len(events), 4)
        self.assertEqual([event["sequence"] for event in events], sorted(event["sequence"] for event in events))
        self.assertEqual(self.service.events(since_sequence=events[0]["sequence"])[0]["sequence"], events[1]["sequence"])

        workspace = self.service.workspace(actor="COACH-2", role="coach_staff")
        self.assertEqual(workspace["counts"]["open_threads"], 0)
        self.assertTrue(workspace["notifications"])
        player_workspace = self.service.workspace(actor="PLAYER-1", role="player")
        self.assertEqual(player_workspace["threads"], [])

    def test_presence_expires_and_notification_read_is_recipient_scoped(self):
        self.service.heartbeat(session_id="SESSION-1", actor="COACH-1", role="coach_staff", display_name="Coach 1", color="#fff")
        self.assertEqual(self.service.workspace(actor="COACH-1", role="coach_staff")["counts"]["active_presence"], 1)
        self.tenant.put("notifications", "NOTIFY-PRIVATE", {"id": "NOTIFY-PRIVATE", "organization_id": "ORG-COLLAB", "recipient": "COACH-1", "status": "unread"}, actor="SEED", reason="fixture")
        self.assertEqual(self.service.mark_notifications_read(notification_ids=["NOTIFY-PRIVATE"], actor="COACH-2")["marked_count"], 0)
        self.assertEqual(self.service.mark_notifications_read(notification_ids=["NOTIFY-PRIVATE"], actor="COACH-1")["marked_count"], 1)

    def test_http_api_requires_scope_and_exposes_workspace(self):
        secret = "collaboration-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        token = issue_token(subject="OWNER-COLLAB", role="program_owner", organization_id="ORG-COLLAB", secret=secret)
        headers = {"Authorization": "Bearer " + token}
        service = FootballIntelligenceService(self.repository)
        status, payload = handle_request(method="POST", path="/v1/collaboration/threads", headers=headers, service=service, body={"organization_id": "ORG-COLLAB", "thread_id": "COLLAB-THREAD-API", "title": "API thread", "body": "Review the game plan.", "entity_type": "game_plan", "entity_id": "GAMEPLAN-API", "deep_link": "/game-plan", "assignee": "COACH-1"})
        self.assertEqual(status, 201)
        status, payload = handle_request(method="GET", path="/v1/collaboration/workspace?organization_id=ORG-COLLAB", headers=headers, service=service)
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["counts"]["open_threads"], 1)
        status, payload = handle_request(method="GET", path="/v1/collaboration/events?organization_id=ORG-COLLAB&since=0", headers=headers, service=service)
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["events"][0]["event_type"], "thread_created")
        status, _ = handle_request(method="GET", path="/v1/collaboration/workspace?organization_id=ORG-OTHER", headers=headers, service=service)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
