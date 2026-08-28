import unittest

from nfl_fidos.master_spec_acceptance import load_master_spec
from nfl_fidos.stage25_acceptance_packet import build_stage25_acceptance_packet


class Stage25AcceptancePacketTests(unittest.TestCase):
    def test_packet_is_ready_but_does_not_accept_or_advance(self):
        packet = build_stage25_acceptance_packet(spec=load_master_spec())
        self.assertEqual(packet["review_status"], "ready_for_owner_review")
        self.assertEqual(packet["spec_validation"]["status"], "valid")
        self.assertFalse(packet["safety"]["acceptance_recorded"])
        self.assertFalse(packet["safety"]["stage_advance_authorized"])
        self.assertFalse(packet["safety"]["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
