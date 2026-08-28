import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class ReleaseAndDeliveryWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.secret = "release-delivery-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret

    def tearDown(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_release_snapshot_requires_owner_approval_and_supports_rollback(self):
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-RELEASE", role="coach_staff", organization_id="ORG-RELEASE", secret=self.secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-RELEASE", role="program_owner", organization_id="ORG-RELEASE", secret=self.secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("game_plans", "GAMEPLAN-RELEASE-1", {"id": "GAMEPLAN-RELEASE-1", "organization_id": "ORG-RELEASE", "week": "WEEK-1", "status": "under_review", "offense": {"base_calls": ["Dagger"]}}, actor="COACH-RELEASE", reason="fixture")
            service.repository.put("play_designs", "PLAY-RELEASE-1", {"id": "PLAY-RELEASE-1", "organization_id": "ORG-RELEASE", "version": "1.2.0", "status": "published"}, actor="COACH-RELEASE", reason="fixture")
            service.repository.put("film_observations", "FILM-OBS-RELEASE-1", {"id": "FILM-OBS-RELEASE-1", "organization_id": "ORG-RELEASE", "status": "reviewed"}, actor="COACH-RELEASE", reason="fixture")
            body = {"organization_id": "ORG-RELEASE", "snapshot_id": "RELEASE-SNAPSHOT-1", "plan_id": "GAMEPLAN-RELEASE-1", "week": "WEEK-1", "note": "First staff release", "artifact_refs": ["PLAY-RELEASE-1", "FILM-OBS-RELEASE-1", "SOURCE-EXTERNAL-1"]}
            status, payload = handle_request(method="POST", path="/v1/game-plan/release-room/snapshots", body=body, headers=coach, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["status"], "pending_approval")
            self.assertEqual(payload["data"]["dependency_manifest"]["linked_count"], 2)
            self.assertEqual(payload["data"]["dependency_manifest"]["unresolved_refs"], ["SOURCE-EXTERNAL-1"])
            self.assertEqual(payload["data"]["dependency_manifest"]["status"], "needs_review")
            self.assertTrue(payload["data"]["release_manifest_hash"])
            self.assertEqual(handle_request(method="POST", path="/v1/game-plan/release-room/approve", body={"organization_id":"ORG-RELEASE", "snapshot_id":"RELEASE-SNAPSHOT-1", "decision_ref":"DEC-RELEASE-1"}, headers=coach, service=service)[0], 403)
            status, payload = handle_request(method="POST", path="/v1/game-plan/release-room/approve", body={"organization_id":"ORG-RELEASE", "snapshot_id":"RELEASE-SNAPSHOT-1", "decision_ref":"DEC-RELEASE-1"}, headers=owner, service=service)
            self.assertEqual(status, 200)
            self.assertTrue(payload["data"]["locked"])
            status, payload = handle_request(method="POST", path="/v1/game-plan/release-room/rollback", body={"organization_id":"ORG-RELEASE", "snapshot_id":"RELEASE-SNAPSHOT-1", "decision_ref":"DEC-RELEASE-2"}, headers=owner, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "rolled_back")

    def test_delivery_tasks_are_scoped_and_computed_in_workspace(self):
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-DELIVERY", role="coach_staff", organization_id="ORG-DELIVERY", secret=self.secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-DELIVERY", role="player", organization_id="ORG-DELIVERY", secret=self.secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/delivery/tasks", body={"organization_id":"ORG-DELIVERY", "task_id":"DELIVERY-TASK-1", "title":"Review install packet", "category":"install", "owner":"COACH-DELIVERY", "due_at":"2099-08-25T12:00:00+00:00", "week":"WEEK-1", "linked_records":["GAMEPLAN-1"], "priority":"high"}, headers=coach, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["notification_id"], "NOTIFY-DELIVERY-DELIVERY-TASK-1")
            notification = service.repository.get("notifications", "NOTIFY-DELIVERY-DELIVERY-TASK-1")
            self.assertEqual(notification["recipient"], "COACH-DELIVERY")
            self.assertEqual(notification["deep_link"], "/app/delivery?record=DELIVERY-TASK-1")
            status, payload = handle_request(method="GET", path="/v1/delivery/workspace?organization_id=ORG-DELIVERY&week=WEEK-1", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["counts"]["tasks"], 1)
            self.assertEqual({item["id"] for item in payload["data"]["packet_readiness"]}, {"coach_packet", "player_install_packet", "coordinator_call_sheet", "wristband_layout", "administrator_audit_packet"})
            self.assertEqual(payload["data"]["packet_readiness"][0]["status"], "blocked")
            self.assertIn("missing:game_plan", payload["data"]["packet_readiness"][0]["blockers"])
            status, payload = handle_request(method="POST", path="/v1/delivery/packets", body={"organization_id":"ORG-DELIVERY", "packet_id":"DELIVERY-PACKET-1", "packet_type":"coach_packet", "week":"WEEK-1", "linked_records":["GAMEPLAN-1"]}, headers=coach, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["status"], "blocked")
            self.assertEqual(payload["data"]["packet_type"], "coach_packet")
            inbox_status, inbox_payload = handle_request(method="GET", path="/v1/operations/inbox?organization_id=ORG-DELIVERY&category=delivery", headers=coach, service=service)
            self.assertEqual(inbox_status, 200)
            self.assertEqual(inbox_payload["data"]["items"][0]["collection"], "delivery_packets")
            self.assertEqual(handle_request(method="GET", path="/v1/delivery/workspace?organization_id=ORG-DELIVERY", headers=player, service=service)[0], 403)
            status, payload = handle_request(method="POST", path="/v1/delivery/tasks/complete", body={"organization_id":"ORG-DELIVERY", "task_id":"DELIVERY-TASK-1"}, headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
