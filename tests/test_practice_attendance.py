import tempfile
import unittest
from pathlib import Path

from nfl_fidos.practice_attendance import PracticeAttendanceService, build_attendance_record
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class PracticeAttendanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.tenant = TenantRepository(JsonRepository(self.root / "state.json"), organization_id="ORG-ATTENDANCE", actor="COACH-1")
        self.tenant.put("practice_plans", "PRACTICE-1", {"id": "PRACTICE-1", "organization_id": "ORG-ATTENDANCE", "status": "draft"}, actor="COACH-1", reason="fixture")
        self.tenant.put("roster_players", "PLAYER-1", {"id": "PLAYER-1", "organization_id": "ORG-ATTENDANCE", "display_name": "Jordan Example", "position": "WR", "position_group": "WR", "status": "active"}, actor="COACH-1", reason="fixture")

    def test_record_is_roster_and_practice_linked_and_summary_is_explicit(self):
        service = PracticeAttendanceService(self.tenant)
        record = service.record(attendance_id="ATTENDANCE-1", practice_id="PRACTICE-1", player_id="PLAYER-1", status="limited", recorded_by="COACH-1", minutes_available=24, period_ids=["PERIOD-1"], note="Ramp volume")
        self.assertEqual(record["status"], "limited")
        self.assertEqual(record["player_name"], "Jordan Example")
        self.assertTrue(record["human_review_required"])
        summary = service.workspace(practice_id="PRACTICE-1")
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["counts"]["limited"], 1)
        self.assertEqual(summary["limited_or_absent"][0]["player_id"], "PLAYER-1")
        self.assertFalse(summary["production_implementation_allowed"])

    def test_unknown_player_and_practice_fail_without_persistence(self):
        service = PracticeAttendanceService(self.tenant)
        unknown_player = service.record(attendance_id="ATTENDANCE-2", practice_id="PRACTICE-1", player_id="PLAYER-UNKNOWN", status="present", recorded_by="COACH-1")
        unknown_practice = service.record(attendance_id="ATTENDANCE-3", practice_id="PRACTICE-UNKNOWN", player_id="PLAYER-1", status="present", recorded_by="COACH-1")
        self.assertEqual(unknown_player["status"], "invalid")
        self.assertIn("player must exist", " ".join(unknown_player["issues"]))
        self.assertEqual(unknown_practice["status"], "invalid")
        self.assertEqual(self.tenant.list("practice_attendance"), [])

    def test_builder_rejects_invalid_status(self):
        record = build_attendance_record(attendance_id="ATTENDANCE-4", organization_id="ORG-ATTENDANCE", practice_id="PRACTICE-1", player_id="PLAYER-1", status="unknown", recorded_by="COACH-1", roster_player={"display_name": "Player"})
        self.assertEqual(record["status"], "invalid")
        self.assertIn("status must be one of", " ".join(record["issues"]))


if __name__ == "__main__":
    unittest.main()
