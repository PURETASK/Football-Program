import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


class Stage0ReviewBundleTests(unittest.TestCase):
    def test_bundle_composes_control_audit_and_synthetic_inventory_without_activation(self):
        from scripts.stage0_review_bundle import build_bundle

        root = Path(__file__).resolve().parents[1]
        with contextlib.redirect_stdout(io.StringIO()):
            result = build_bundle(root=root, run_evals=False)

        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["checks"]["review_files_present"])
        self.assertTrue(result["checks"]["owner_packet_ready"])
        self.assertTrue(result["synthetic_demo"]["present"])
        self.assertGreater(result["synthetic_demo"]["record_counts"].get("organizations", 0), 0)
        self.assertFalse(result["safety"]["seed_performed"])
        self.assertFalse(result["safety"]["approval_recorded"])
        self.assertFalse(result["safety"]["stage_advance_authorized"])
        self.assertFalse(result["safety"]["production_implementation_allowed"])
        self.assertFalse(result["safety"]["external_state_changed"])

    def test_bundle_can_be_persisted(self):
        from scripts import stage0_review_bundle

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "stage0-review-bundle.json"
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                exit_code = stage0_review_bundle.main([
                    "--root", str(root),
                    "--skip-evals",
                    "--output", str(output),
                ])
            self.assertEqual(exit_code, 0)
            printed = json.loads(captured.getvalue())
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(printed, persisted)
            self.assertEqual(persisted["evidence_output"], str(output.resolve()))


if __name__ == "__main__":
    unittest.main()
