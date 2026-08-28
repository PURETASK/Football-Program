import json
import unittest
from pathlib import Path

from nfl_fidos.architecture import validate_system_architecture


class ArchitectureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "architecture" / "system-architecture.json"
        self.architecture = json.loads(path.read_text(encoding="utf-8"))

    def test_system_architecture_is_valid(self):
        result = validate_system_architecture(self.architecture)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["component_count"], 10)
        self.assertGreaterEqual(result["flow_count"], 8)

    def test_unknown_flow_endpoint_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["information_flows"][0]["to"] = "SVC-MISSING"
        result = validate_system_architecture(architecture)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unknown components" in error for error in result["errors"]))

    def test_missing_human_authority_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["human_authority_points"].remove("authoritative rules")
        result = validate_system_architecture(architecture)
        self.assertEqual(result["status"], "invalid")
