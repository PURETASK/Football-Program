import json
import unittest
from pathlib import Path

from nfl_fidos.stage0_owner_packet import build_stage0_owner_packet


class Stage0OwnerPacketTests(unittest.TestCase):
    def test_packet_is_ready_but_cannot_approve_or_advance(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
        gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
        packet = build_stage0_owner_packet(registry=registry, gap_audit=gap_audit)
        self.assertEqual(packet["review_status"], "ready_for_owner_review")
        self.assertEqual(packet["gate"]["status"], "ready_for_approval")
        self.assertFalse(packet["safety"]["approval_recorded"])
        self.assertFalse(packet["safety"]["stage_advance_authorized"])
        self.assertFalse(packet["safety"]["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
