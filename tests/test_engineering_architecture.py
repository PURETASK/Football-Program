import json
import unittest
from pathlib import Path

from nfl_fidos.engineering_architecture import validate_engineering_architecture


class EngineeringArchitectureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "engineering" / "engineering-architecture.json"
        self.architecture = json.loads(path.read_text(encoding="utf-8"))

    def test_engineering_architecture_is_complete(self):
        result = validate_engineering_architecture(self.architecture)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["repo_area_count"], 6)
        self.assertGreaterEqual(result["runtime_boundary_count"], 6)

    def test_missing_governance_ci_gate_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["ci_cd"].remove("require governance audit and approval")
        self.assertEqual(validate_engineering_architecture(architecture)["status"], "invalid")

    def test_observability_fields_are_required(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["observability"]["required_fields"].remove("request_id")
        self.assertEqual(validate_engineering_architecture(architecture)["status"], "invalid")
