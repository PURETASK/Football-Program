import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import authorize


class AccessTests(unittest.TestCase):
    def test_player_can_read_assigned_playbook(self):
        decision = authorize(decision_id="ACCESS-001", requester_role="player", action="read_assigned_playbook", resource="PLAY-001")
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["status"], "allowed")

    def test_player_cannot_lock_artifact(self):
        decision = authorize(decision_id="ACCESS-002", requester_role="player", action="lock_artifact", resource="PLAY-001")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["status"], "denied")

    def test_locked_artifact_requires_human_approval(self):
        pending = authorize(decision_id="ACCESS-003", requester_role="coach_staff", action="draft_play", resource="PLAY-001", locked=True)
        self.assertFalse(pending["allowed"])
        self.assertEqual(pending["status"], "pending_human_approval")
        approved = authorize(decision_id="ACCESS-004", requester_role="program_owner", action="unlock_artifact", resource="PLAY-001", locked=True, human_approved=True)
        self.assertTrue(approved["allowed"])

    def test_high_impact_action_requires_approval(self):
        pending = authorize(decision_id="ACCESS-005", requester_role="program_owner", action="lock_artifact", resource="PLAY-001")
        self.assertEqual(pending["status"], "pending_human_approval")
        approved = authorize(decision_id="ACCESS-006", requester_role="program_owner", action="lock_artifact", resource="PLAY-001", human_approved=True)
        self.assertEqual(approved["status"], "allowed")

    def test_performance_staff_can_record_practice_outcomes(self):
        decision = authorize(decision_id="ACCESS-007", requester_role="performance_staff", action="record_outcome", resource="PERIOD-001")
        self.assertTrue(decision["allowed"])


if __name__ == "__main__":
    unittest.main()
