import json
import unittest
from pathlib import Path

from nfl_fidos.master_spec import validate_master_spec


class MasterSpecTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "control" / "master-codex-build-spec.json"
        self.spec = json.loads(path.read_text(encoding="utf-8"))

    def test_master_spec_covers_all_stages_and_controls(self):
        result = validate_master_spec(self.spec)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["stage_count"], 26)

    def test_missing_stage_is_rejected(self):
        spec = json.loads(json.dumps(self.spec))
        spec["stage_sequence"] = [stage for stage in spec["stage_sequence"] if stage["stage"] != "STAGE-25"]
        self.assertEqual(validate_master_spec(spec)["status"], "invalid")

    def test_missing_prohibited_change_policy_is_rejected(self):
        spec = json.loads(json.dumps(self.spec))
        spec["prohibited_changes"] = []
        self.assertEqual(validate_master_spec(spec)["status"], "invalid")
