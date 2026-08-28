import json
import unittest
from pathlib import Path

from nfl_fidos.ux_architecture import validate_ux_architecture


class UXArchitectureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "ux" / "ux-architecture.json"
        self.architecture = json.loads(path.read_text(encoding="utf-8"))

    def test_ux_has_screens_journeys_permissions_and_accessibility(self):
        result = validate_ux_architecture(self.architecture)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["screen_count"], 8)
        self.assertGreaterEqual(result["journey_count"], 4)

    def test_unknown_permission_surface_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["permissions_to_ui"][0]["ui_surfaces"] = ["SCREEN-MISSING"]
        self.assertEqual(validate_ux_architecture(architecture)["status"], "invalid")

    def test_missing_restricted_state_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["screen_inventory"][0]["states"].remove("restricted")
        self.assertEqual(validate_ux_architecture(architecture)["status"], "invalid")
