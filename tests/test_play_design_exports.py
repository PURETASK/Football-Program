import base64
import json
import tempfile
import unittest
from pathlib import Path

from src.nfl_fidos.play_design_exports import build_export, build_export_preflight, validate_export_design, verify_export_artifact
from src.nfl_fidos.play_design_service import PlayDesignService
from src.nfl_fidos.repository import JsonRepository
from src.nfl_fidos.tenant_repository import TenantRepository
from tests.test_play_creation import design


class PlayDesignExportTests(unittest.TestCase):
    def service(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        temporary.close()
        path = Path(temporary.name)
        path.unlink()
        return PlayDesignService(TenantRepository(JsonRepository(path), organization_id="ORG-EXPORT", actor="coach"))

    def test_production_formats_have_checksums_and_validation(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        svg = service.export_artifact([saved["id"]], kind="play_card", format="svg", actor="coach")
        self.assertEqual(svg["validation"]["status"], "valid")
        self.assertEqual(svg["source_manifest"][0]["design_id"], saved["id"])
        self.assertEqual(len(svg["source_manifest_hash"]), 64)
        self.assertEqual(svg["role"], "coach")
        self.assertIn("marker-end", base64.b64decode(svg["content_base64"]).decode("utf-8"))
        pdf = service.export_artifact([saved["id"]], kind="play_card", format="pdf", actor="coach", black_white=True)
        self.assertTrue(base64.b64decode(pdf["content_base64"]).startswith(b"%PDF"))
        self.assertEqual(len(pdf["sha256"]), 64)
        png = service.export_artifact([saved["id"]], kind="play_card", format="png", actor="coach")
        self.assertTrue(base64.b64decode(png["content_base64"]).startswith(b"\x89PNG"))

    def test_call_sheet_wristband_and_install_exports(self):
        service = self.service()
        first = service.save(design=design(), actor="coach")
        second_candidate = design()
        second_candidate["id"] = "DESIGN-EXPORT-002"
        second_candidate["concept"] = "flood"
        second = service.save(design=second_candidate, actor="coach")
        call_sheet = service.export_artifact([first["id"], second["id"]], kind="call_sheet", format="csv", actor="coach")
        self.assertIn("slot,code,call", base64.b64decode(call_sheet["content_base64"]).decode("utf-8"))
        wristband = service.export_artifact([first["id"], second["id"]], kind="wristband", format="pdf", actor="coach")
        self.assertTrue(base64.b64decode(wristband["content_base64"]).startswith(b"%PDF"))
        self.assertEqual(wristband["layout"], "wristband_2col")
        self.assertEqual(len(wristband["source_manifest"]), 2)
        compact_wristband = service.export_artifact([first["id"], second["id"]], kind="wristband", format="pdf", actor="coach", layout="wristband_3col")
        self.assertTrue(base64.b64decode(compact_wristband["content_base64"]).startswith(b"%PDF"))
        self.assertEqual(compact_wristband["layout"], "wristband_3col")
        sideline_wristband = service.export_artifact([first["id"], second["id"]], kind="wristband", format="pdf", actor="coach", layout="wristband_4col")
        self.assertEqual(sideline_wristband["layout"], "wristband_4col")
        grid = service.export_artifact([first["id"], second["id"]], kind="play_card", format="pdf", actor="coach", layout="grid_2x2")
        self.assertTrue(base64.b64decode(grid["content_base64"]).startswith(b"%PDF"))
        self.assertEqual(grid["layout"], "grid_2x2")
        install = service.export_artifact([first["id"]], kind="install_sheet", format="csv", actor="coach")
        self.assertIn("player_id,assignment", base64.b64decode(install["content_base64"]).decode("utf-8"))
        install_pdf = service.export_artifact([first["id"], second["id"]], kind="install_sheet", format="pdf", actor="coach", black_white=True, role="P1")
        self.assertTrue(base64.b64decode(install_pdf["content_base64"]).startswith(b"%PDF"))
        self.assertEqual(install_pdf["layout"], "single")
        focused = service.export_artifact([first["id"]], kind="play_card", format="json", actor="coach", role="P1")
        self.assertEqual(focused["role"], "P1")

    def test_export_selection_rejects_duplicate_and_malformed_design_ids(self):
        service = self.service()
        first = service.save(design(), actor="coach")
        with self.assertRaisesRegex(ValueError, "Duplicate export design id"):
            service.export_preflight([first["id"], first["id"]], kind="play_card", format="pdf")
        with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
            service.export_artifact([first["id"], None], kind="play_card", format="pdf", actor="coach")

    def test_export_validation_explains_invalid_design(self):
        candidate = design()
        candidate["validation"] = {"status": "invalid"}
        issues = validate_export_design(candidate, kind="play_card", format="pdf")
        self.assertIn("EXPORT-DESIGN-INVALID", {issue["code"] for issue in issues})
        self.assertIn("EXPORT-LAYOUT-FORMAT", {issue["code"] for issue in validate_export_design(candidate, kind="play_card", format="svg", layout="grid_2x2")})
        self.assertIn("EXPORT-LAYOUT-FORMAT", {issue["code"] for issue in validate_export_design(candidate, kind="wristband", format="png", layout="wristband_4col")})
        self.assertIn("EXPORT-LAYOUT-KIND", {issue["code"] for issue in validate_export_design(candidate, kind="play_card", format="pdf", layout="wristband_3col")})
        with self.assertRaises(ValueError):
            build_export(designs=[candidate], kind="play_card", format="pdf")

    def test_export_validation_rejects_geometry_that_would_be_clipped(self):
        candidate = design()
        candidate["players"][0]["start"] = {"x": 101, "y": 20}
        candidate["elements"][0]["points"] = [{"x": 10, "y": 10}, {"x": 30, "y": 54}]
        candidate["elements"][0]["branches"] = [{"id": "BRANCH-OOB", "points": [{"x": -1, "y": 22}, {"x": 40, "y": 12}]}]
        issues = validate_export_design(candidate, kind="play_card", format="pdf")
        bounds = [issue for issue in issues if issue["code"] == "EXPORT-GEOMETRY-BOUNDS"]
        self.assertEqual(len(bounds), 3)
        self.assertIn("players[0].start", {issue["path"] for issue in bounds})
        self.assertIn("elements[0].points[1]", {issue["path"] for issue in bounds})
        self.assertIn("elements[0].branches[0].points[0]", {issue["path"] for issue in bounds})
        self.assertFalse(build_export_preflight(designs=[candidate], kind="play_card", format="pdf")["can_render"])

    def test_preflight_matches_render_layout_and_returns_source_lock_without_content(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        preflight = service.export_preflight([saved["id"]], kind="wristband", format="pdf", role="P1", layout="wristband_4col")
        self.assertEqual(preflight["validation"]["status"], "valid")
        self.assertTrue(preflight["can_render"])
        self.assertEqual(preflight["layout"], "wristband_4col")
        self.assertEqual(preflight["role"], "P1")
        self.assertEqual(preflight["design_count"], 1)
        self.assertNotIn("content_base64", preflight)
        rendered = service.export_artifact([saved["id"]], kind="wristband", format="pdf", actor="coach", role="P1", layout="wristband_4col")
        self.assertEqual(preflight["source_manifest_hash"], rendered["source_manifest_hash"])
        self.assertEqual(preflight["source_manifest"], rendered["source_manifest"])

    def test_preflight_exposes_blockers_without_throwing(self):
        candidate = design()
        candidate["players"] = candidate["players"][:10]
        preflight = build_export_preflight(designs=[candidate], kind="play_card", format="pdf")
        self.assertFalse(preflight["can_render"])
        self.assertEqual(preflight["validation"]["status"], "invalid")
        self.assertIn("EXPORT-PLAYER-COUNT", {issue["code"] for issue in preflight["validation"]["issues"]})

    def test_export_player_count_follows_selected_rule_profile(self):
        candidate = design()
        candidate["rule_profile"] = "flag"
        candidate["players"] = candidate["players"][:5]
        self.assertNotIn("EXPORT-PLAYER-COUNT", {issue["code"] for issue in validate_export_design(candidate, kind="play_card", format="pdf")})
        youth = design()
        youth["rule_profile"] = "youth"
        self.assertIn("EXPORT-RULE-PROFILE-UNRESOLVED", {issue["code"] for issue in validate_export_design(youth, kind="play_card", format="pdf")})

    def test_svg_export_preserves_branch_paths_and_drawing_semantics(self):
        candidate = design()
        candidate["elements"][0].update({
            "line_style": "dashed",
            "line_weight": 1.4,
            "line_cap": "square",
            "branches": [{"id": "BRANCH-1", "label": "Break out", "condition": "versus outside leverage", "points": [{"x": 20, "y": 30}, {"x": 35, "y": 20}, {"x": 42, "y": 24}]}],
        })
        rendered = build_export(designs=[candidate], kind="play_card", format="svg")
        payload = base64.b64decode(rendered["content_base64"]).decode("utf-8")
        self.assertIn('data-branch-id="BRANCH-1"', payload)
        self.assertIn('stroke-dasharray="6 3"', payload)
        self.assertIn('stroke-width="1.40"', payload)
        self.assertIn("versus outside leverage", payload)
        self.assertIn("Alternate path", payload)

    def test_raster_and_pdf_exports_include_branch_geometry(self):
        candidate = design()
        candidate["elements"][0]["branches"] = [{"id": "BRANCH-RASTER", "label": "Pressure answer", "condition": "versus pressure", "points": [{"x": 20, "y": 30}, {"x": 30, "y": 18}]}]
        service = self.service()
        saved = service.save(design=candidate, actor="coach")
        png = service.export_artifact([saved["id"]], kind="play_card", format="png", actor="coach")
        pdf = service.export_artifact([saved["id"]], kind="play_card", format="pdf", actor="coach")
        self.assertTrue(base64.b64decode(png["content_base64"]).startswith(b"\x89PNG"))
        self.assertGreater(len(base64.b64decode(pdf["content_base64"])), 500)

    def test_direct_export_normalizes_legacy_timeline_and_preserves_authored_phases(self):
        candidate = design()
        candidate["timeline"] = {
            "duration_ms": 1600,
            "events": [{"id": "READ-LEGACY", "type": "qb_read", "at_ms": 425, "end_ms": 700, "element_id": "E1"}],
        }
        candidate["elements"][0]["timing"] = {
            "start_ms": 100,
            "end_ms": 1100,
            "phases": [{"id": "custom-stem", "label": "Custom stem", "start_ms": 280, "end_ms": 640}],
        }
        rendered = build_export(designs=[candidate], kind="play_card", format="json")
        payload = json.loads(base64.b64decode(rendered["content_base64"]))
        normalized = payload["designs"][0]
        self.assertEqual(normalized["timeline"]["events"][0]["kind"], "read")
        self.assertEqual(normalized["timeline"]["events"][0]["start_ms"], 425)
        self.assertEqual(normalized["elements"][0]["timing"]["phases"][0]["label"], "Custom stem")

    def test_preflight_uses_same_normalized_timeline_contract_as_render(self):
        candidate = design()
        candidate["timeline"] = {"events": [{"type": "coverage_rotation", "at_ms": 300}]}
        preflight = build_export_preflight(designs=[candidate], kind="play_card", format="json")
        rendered = build_export(designs=[candidate], kind="play_card", format="json")
        payload = json.loads(base64.b64decode(rendered["content_base64"]))
        self.assertTrue(preflight["can_render"])
        self.assertEqual(payload["designs"][0]["timeline"]["events"][0]["kind"], "rotation")

    def test_accessible_export_text_includes_synchronized_events_and_narration(self):
        candidate = design()
        candidate["timeline"] = {
            "events": [{"type": "qb_read", "at_ms": 300, "label": "Read the apex defender"}],
            "narration": [{"start_ms": 350, "end_ms": 900, "role": "coach", "text": "Confirm the flat defender widens."}],
        }
        rendered = build_export(designs=[candidate], kind="play_card", format="svg")
        payload = base64.b64decode(rendered["content_base64"]).decode("utf-8")
        self.assertIn("Timeline read: Read the apex defender; 300-800 ms.", payload)
        self.assertIn("Narration (coach) 350-900 ms: Confirm the flat defender widens.", payload)

    def test_accessible_export_text_identifies_branch_specific_timeline_events(self):
        candidate = design()
        candidate["elements"][0]["id"] = "ROUTE-CHOICE"
        candidate["elements"][0]["branches"] = [{
            "id": "BR-ALERT", "label": "Alert path", "condition": "If the safety rotates",
            "points": [{"x": 30, "y": 30}, {"x": 50, "y": 12}],
        }]
        candidate["timeline"]["events"] = [{
            "id": "READ-ALERT", "kind": "read", "element_id": "ROUTE-CHOICE", "branch_id": "BR-ALERT",
            "start_ms": 400, "end_ms": 800, "label": "Choose the answer",
        }]
        rendered = build_export(designs=[candidate], kind="play_card", format="svg")
        payload = base64.b64decode(rendered["content_base64"]).decode("utf-8")
        self.assertIn("Timeline read: Choose the answer; path Alert path (condition: If the safety rotates); 400-800 ms.", payload)

    def test_defensive_export_preserves_technique_and_alignment_labels(self):
        candidate = design()
        candidate["unit"] = "defense"
        candidate["players"][0].update({"position": "DT", "defensive_technique": "3", "defensive_alignment": "outside_eye"})
        rendered = build_export(designs=[candidate], kind="play_card", format="svg")
        payload = base64.b64decode(rendered["content_base64"]).decode("utf-8")
        self.assertIn("3-tech · outside eye", payload)

    def test_artifact_integrity_is_verified_and_exposes_print_metadata(self):
        rendered = build_export(designs=[design()], kind="play_card", format="svg")
        self.assertEqual(rendered["integrity"]["status"], "verified")
        self.assertEqual(rendered["page_size"], "letter")
        self.assertEqual(rendered["page_count"], 1)
        self.assertTrue(rendered["printer_safe"])
        self.assertEqual(rendered["print_profile"], "letter_portrait")
        self.assertEqual(rendered["print_orientation"], "portrait")
        self.assertEqual(rendered["safe_area_in"], 0.35)
        self.assertEqual(rendered["color_mode"], "color")
        self.assertTrue(rendered["accessibility"]["has_alt_text"])
        self.assertEqual(rendered["source_lock"]["status"], "review")

    def test_data_exports_declare_non_printing_profile_and_visual_exports_reject_it(self):
        data_export = build_export(designs=[design()], kind="play_card", format="json")
        self.assertFalse(data_export["printer_safe"])
        self.assertEqual(data_export["print_profile"], "data_export")
        self.assertIsNone(data_export["safe_area_in"])
        tampered = dict(data_export)
        tampered["print_profile"] = "letter_portrait"
        self.assertEqual(verify_export_artifact(tampered)["status"], "invalid")

    def test_artifact_verifier_detects_tampering(self):
        rendered = build_export(designs=[design()], kind="play_card", format="json")
        rendered["content_base64"] = base64.b64encode(b"tampered").decode("ascii")
        verification = verify_export_artifact(rendered)
        self.assertEqual(verification["status"], "invalid")
        self.assertIn("EXPORT-ARTIFACT-HASH", {issue["code"] for issue in verification["issues"]})
        self.assertIn("EXPORT-ARTIFACT-BYTES", {issue["code"] for issue in verification["issues"]})

    def test_artifact_verifier_detects_metadata_tampering(self):
        rendered = build_export(designs=[design()], kind="play_card", format="pdf")
        rendered["format"] = "png"
        verification = verify_export_artifact(rendered)
        self.assertEqual(verification["status"], "invalid")
        self.assertIn("EXPORT-FORMAT-SIGNATURE", {issue["code"] for issue in verification["issues"]})

    def test_packet_metadata_uses_layout_capacity(self):
        designs = []
        for index in range(5):
            candidate = design()
            candidate["id"] = f"DESIGN-PACKET-{index:02d}"
            designs.append(candidate)
        grid = build_export(designs=designs, kind="play_card", format="pdf", layout="grid_2x2")
        self.assertEqual(grid["page_count"], 2)
        wristband = build_export(designs=designs, kind="wristband", format="pdf", layout="wristband_4col")
        self.assertEqual(wristband["page_count"], 1)


if __name__ == "__main__":
    unittest.main()
