import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.operations_inbox import build_operations_inbox
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository
from nfl_fidos.service import FootballIntelligenceService


class OperationsInboxTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = JsonRepository(Path(self.temporary.name) / "state.json")
        self.tenant = TenantRepository(self.repository, organization_id="ORG-INBOX", actor="OWNER-INBOX")
        self.now = datetime(2026, 8, 25, 12, tzinfo=timezone.utc)

    def tearDown(self):
        self.temporary.cleanup()

    def put(self, collection, record_id, record):
        self.tenant.put(collection, record_id, {"id": record_id, "organization_id": "ORG-INBOX", **record}, actor="SEED", reason="fixture")

    def test_owner_inbox_aggregates_reviews_tasks_sources_and_notifications(self):
        self.put("game_plans", "GAMEPLAN-INBOX-001", {"name": "Third-down package", "status": "under_review", "assigned_to": "COACH-1", "source_refs": ["SCOUT-1"]})
        self.put("tasks", "TASK-INBOX-001", {"title": "Verify practice load", "status": "open", "assigned_to": "OWNER-INBOX", "due_at": "2026-08-25T10:00:00Z", "priority": "high", "deep_link": "/practice"})
        self.put("knowledge_sources", "SOURCE-INBOX-001", {"name": "Opponent feed", "status": "stale", "owner": "ANALYST-1"})
        self.put("notifications", "NOTIFY-INBOX-001", {"title": "Game-plan thread needs your decision", "recipient": "OWNER-INBOX", "status": "unread"})

        result = build_operations_inbox(repository=self.tenant, role="program_owner", actor="OWNER-INBOX", now=self.now)

        self.assertEqual(result["count"], 4)
        self.assertEqual(result["counts"]["overdue"], 1)
        self.assertEqual(result["counts"]["unread_notifications"], 1)
        self.assertTrue(any(item["category"] == "review" for item in result["items"]))
        self.assertTrue(any(item["deep_link"] == "/practice" for item in result["items"]))
        self.assertEqual(build_operations_inbox(repository=self.tenant, role="program_owner", actor="OWNER-INBOX", filters={"due_state": "overdue"}, now=self.now)["count"], 1)

    def test_player_inbox_is_limited_to_player_owned_work(self):
        self.put("player_assignments", "ASSIGNMENT-PLAYER-1", {"title": "Install motion check", "player_id": "PLAYER-1", "assigned_to": "PLAYER-1", "status": "assigned"})
        self.put("player_assignments", "ASSIGNMENT-PLAYER-2", {"title": "Private assignment", "player_id": "PLAYER-2", "assigned_to": "PLAYER-2", "status": "assigned"})

        result = build_operations_inbox(repository=self.tenant, role="player", actor="PLAYER-1", now=self.now)

        self.assertEqual([item["record_id"] for item in result["items"]], ["ASSIGNMENT-PLAYER-1"])

    def test_inbox_promotes_open_collaboration_threads_and_hides_resolved_by_default(self):
        self.put("collaboration_threads", "COLLAB-THREAD-INBOX-1", {"title": "Confirm pressure answer", "body": "Attach the latest film clip.", "status": "open", "priority": "high", "assigned_to": "OWNER-INBOX", "entity_type": "game_plan", "entity_id": "GAMEPLAN-1", "deep_link": "/game-plan", "evidence_refs": ["FILM-1"]})
        self.put("collaboration_threads", "COLLAB-THREAD-INBOX-2", {"title": "Closed note", "body": "Already resolved.", "status": "resolved", "assigned_to": "OWNER-INBOX"})

        result = build_operations_inbox(repository=self.tenant, role="program_owner", actor="OWNER-INBOX", now=self.now)

        self.assertEqual([item["record_id"] for item in result["items"]], ["COLLAB-THREAD-INBOX-1"])
        self.assertEqual(result["items"][0]["category"], "review")
        self.assertEqual(result["items"][0]["deep_link"], "/game-plan")
        self.assertTrue(result["items"][0]["assigned_to_me"])

    def test_media_job_inbox_item_exposes_processing_guidance(self):
        self.put("media_processing_jobs", "MEDIA-JOB-INBOX-1", {
            "asset_id": "FILM-ASSET-INBOX-1", "operation": "thumbnail", "status": "retryable",
            "attempt": 1, "last_error": {"code": "MEDIA-THUMBNAIL-FAILED", "message": "ffmpeg unavailable"},
            "next_action": "retry_or_review_failed_jobs", "output_refs": [],
        })

        result = build_operations_inbox(repository=self.tenant, role="program_owner", actor="OWNER-INBOX", filters={"origin_category": "media"}, now=self.now)

        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["operation"], "thumbnail")
        self.assertEqual(item["origin_category"], "media")
        self.assertEqual(item["category"], "review")
        self.assertEqual(item["asset_id"], "FILM-ASSET-INBOX-1")
        self.assertEqual(item["last_error"]["code"], "MEDIA-THUMBNAIL-FAILED")
        self.assertEqual(item["next_action"], "retry_or_review_failed_jobs")

    def test_api_filters_and_marks_notifications_read(self):
        secret = "operations-inbox-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        token = issue_token(subject="OWNER-INBOX", role="program_owner", organization_id="ORG-INBOX", secret=secret)
        self.put("notifications", "NOTIFY-API-001", {"title": "Read this", "recipient": "OWNER-INBOX", "status": "unread"})
        service = FootballIntelligenceService(self.repository)
        headers = {"Authorization": "Bearer " + token}
        status, payload = handle_request(method="GET", path="/v1/operations/inbox?organization_id=ORG-INBOX&category=notification&unread_only=true", headers=headers, service=service)
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["count"], 1)
        status, payload = handle_request(method="POST", path="/v1/operations/inbox/notifications/read", headers=headers, body={"organization_id": "ORG-INBOX", "notification_ids": ["NOTIFY-API-001"]}, service=service)
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["marked_count"], 1)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
