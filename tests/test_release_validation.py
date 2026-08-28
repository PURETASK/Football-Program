import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.release_validation import validate_release_artifacts


class ReleaseValidationTests(unittest.TestCase):
    def test_current_repository_artifacts_are_complete_but_stage_gate_blocks_release(self):
        root = Path(__file__).resolve().parents[1]
        result = validate_release_artifacts(root=root, eval_result={"status":"passed"})
        self.assertEqual(result["artifact_status"], "complete")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["human_approval_required"])
        self.assertFalse(result["deploy_performed"])

    def test_missing_artifact_is_reported_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "control").mkdir()
            (root / "control" / "manifest.json").write_text(json.dumps({"current_stage":"STAGE-0", "production_implementation_allowed":False}), encoding="utf-8")
            result = validate_release_artifacts(root=root, eval_result={"status":"passed"})
            self.assertEqual(result["artifact_status"], "incomplete")
            self.assertTrue(result["missing_artifacts"])


if __name__ == "__main__":
    unittest.main()
