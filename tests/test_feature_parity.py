import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.feature_parity import audit_feature_parity


class FeatureParityTests(unittest.TestCase):
    def test_repository_manifest_maps_every_legacy_anchor_without_authorizing_retirement(self):
        report = audit_feature_parity()
        self.assertEqual(report["status"], "ready_for_human_review")
        self.assertEqual(report["entry_count"], 22)
        self.assertEqual(report["state_counts"]["deferred"], 0)
        self.assertFalse(report["retirement_authorized"])
        self.assertEqual(report["errors"], [])

    def test_missing_react_route_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"retirement_decision": "not_authorized", "entries": [{"id": "P-1", "legacy_anchor": "today", "react_route_token": "missing", "react_file": "Missing.tsx", "migration_state": "migrated"}]}), encoding="utf-8")
            legacy = root / "legacy.html"
            legacy.write_text('<section id="today"></section>', encoding="utf-8")
            react = root / "App.tsx"
            react.write_text('<Route index element={null} />', encoding="utf-8")
            report = audit_feature_parity(manifest_path=manifest, legacy_path=legacy, react_app_path=react)
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(any("React file is missing" in error for error in report["errors"]))

    def test_deferred_entry_requires_follow_up(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"retirement_decision": "not_authorized", "entries": [{"id": "P-1", "legacy_anchor": "today", "react_route_token": "index", "react_file": "App.tsx", "migration_state": "deferred"}]}), encoding="utf-8")
            legacy = root / "legacy.html"
            legacy.write_text('<section id="today"></section>', encoding="utf-8")
            react = root / "App.tsx"
            react.write_text('<Route index element={null} />', encoding="utf-8")
            report = audit_feature_parity(manifest_path=manifest, legacy_path=legacy, react_app_path=react)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["state_counts"]["deferred"], 1)

    def test_new_legacy_anchor_without_manifest_entry_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"retirement_decision": "not_authorized", "entries": [{"id": "P-1", "legacy_anchor": "today", "react_route_token": "index", "react_file": "App.tsx", "migration_state": "migrated"}]}), encoding="utf-8")
            legacy = root / "legacy.html"
            legacy.write_text('<section id="today"></section><section id="new-section"></section>', encoding="utf-8")
            react = root / "App.tsx"
            react.write_text('<Route index element={null} />', encoding="utf-8")
            report = audit_feature_parity(manifest_path=manifest, legacy_path=legacy, react_app_path=react)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["unmapped_legacy_anchors"], ["new-section"])


if __name__ == "__main__":
    unittest.main()
