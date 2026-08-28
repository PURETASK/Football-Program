import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import create_handoff


class AgentContractTests(unittest.TestCase):
    def test_allowed_handoff_is_ready_and_auditable(self):
        handoff = create_handoff(
            handoff_id="HANDOFF-001", from_agent="AGT-001", to_agent="AGT-007",
            workflow_id="WF-004", payload={"play_id": "PLAY-001"}, requested_permissions={"validate"},
        )
        self.assertEqual(handoff["status"], "ready")
        self.assertEqual(handoff["requested_permissions"], ["validate"])
        self.assertTrue(handoff["created_at"])

    def test_disallowed_permission_is_rejected(self):
        handoff = create_handoff(
            handoff_id="HANDOFF-002", from_agent="AGT-001", to_agent="AGT-007",
            workflow_id="WF-004", payload={"play_id": "PLAY-001"}, requested_permissions={"lock_playbook"},
        )
        self.assertEqual(handoff["status"], "rejected")
        self.assertEqual(handoff["issues"][0]["code"], "HANDOFF-PERMISSION")

    def test_empty_payload_is_rejected(self):
        handoff = create_handoff(
            handoff_id="HANDOFF-003", from_agent="AGT-001", to_agent="AGT-014",
            workflow_id="WF-008", payload={}, requested_permissions={"review"}, human_review_required=True,
        )
        self.assertEqual(handoff["status"], "rejected")
        self.assertTrue(any(issue["code"] == "HANDOFF-PAYLOAD" for issue in handoff["issues"]))


if __name__ == "__main__":
    unittest.main()
