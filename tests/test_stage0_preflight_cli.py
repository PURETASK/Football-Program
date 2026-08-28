import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


class Stage0PreflightCliTests(unittest.TestCase):
    def test_owner_packet_can_be_persisted_without_approval(self):
        from scripts import stage0_owner_approval_preflight

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "stage0-owner-packet.json"
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                exit_code = stage0_owner_approval_preflight.main([
                    "--root", str(root),
                    "--output", str(output),
                ])

            self.assertEqual(exit_code, 0)
            printed = json.loads(captured.getvalue())
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(printed, persisted)
            self.assertEqual(persisted["review_status"], "ready_for_owner_review")
            self.assertEqual(persisted["packet_output"], str(output.resolve()))
            self.assertFalse(persisted["safety"]["approval_recorded"])
            self.assertFalse(persisted["safety"]["stage_advance_authorized"])
            self.assertFalse(persisted["safety"]["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
