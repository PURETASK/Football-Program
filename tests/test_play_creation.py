import unittest

from src.nfl_fidos.play_creation import normalize_term, validate_legality, validate_play_design
from src.nfl_fidos.play_assignment_graph import build_assignment_graph, validate_assignment_graph
from src.nfl_fidos.play_legality import profile_metadata, validate_advanced_legality, validate_rule_profile_catalog
from src.nfl_fidos.play_timeline import default_phases, normalize_timeline_design, validate_timeline


def design(unit="offense"):
    players = [{"id": f"P{i}", "position": "WR", "start": {"x": 10 + i * 7, "y": 5}} for i in range(11)]
    elements = [{"kind": "route", "player_id": "P0", "type": "post", "points": [{"x": 10, "y": 5}, {"x": 30, "y": 30}], "arrow_style": "route"}]
    output = {"id": "DESIGN-001", "version": "1.0.0", "unit": unit, "personnel": "11", "formation": "trips_right", "players": players, "elements": elements, "timeline": {"snap_ms": 0}}
    if unit == "offense":
        output["concept"] = "dagger"
    else:
        output["front"] = "4-2-5_over"
        output["coverage"] = "cover_3"
    return output


class PlayCreationTests(unittest.TestCase):
    def test_normalize_term_is_stable(self):
        self.assertEqual(normalize_term(" Cover-3 "), "cover_3")

    def test_valid_offensive_design(self):
        self.assertEqual(validate_play_design(design("offense")), [])

    def test_defense_requires_front_and_coverage(self):
        candidate = design("defense")
        candidate.pop("coverage")
        issues = validate_play_design(candidate)
        self.assertIn("DEFENSE-COVERAGE", {issue["code"] for issue in issues})

    def test_invalid_path_and_arrow_are_reported(self):
        candidate = design()
        candidate["elements"][0]["points"] = [{"x": 10, "y": 5}]
        candidate["elements"][0]["arrow_style"] = "wrong"
        codes = {issue["code"] for issue in validate_play_design(candidate)}
        self.assertIn("DESIGN-PATH", codes)
        self.assertIn("DESIGN-ARROW", codes)

    def test_legality_lints_motion_and_timeline(self):
        candidate = design()
        candidate["rule_profile"] = "nfl"
        candidate["elements"].append({"id": "E-MOTION", "kind": "motion", "type": "jet", "player_id": "P1", "points": [{"x": 10, "y": 5}, {"x": 30, "y": 5}], "arrow_style": "motion", "snap_direction": "toward_los", "requires_reset": True, "reset_complete": False, "start_ms": -5001})
        codes = {issue["code"] for issue in validate_legality(candidate)}
        self.assertIn("LEGALITY-MOTION-DIRECTION", codes)
        self.assertIn("LEGALITY-MOTION-RESET", codes)
        self.assertIn("LEGALITY-TIMELINE", codes)

    def test_timeline_normalization_adds_phases_and_duration(self):
        candidate = design()
        normalized = normalize_timeline_design(candidate)
        self.assertGreaterEqual(normalized["timeline"]["duration_ms"], 3000)
        self.assertEqual(normalized["elements"][0]["timing"]["phases"], default_phases("route", 0, 1200))

    def test_timeline_preserves_pre_snap_motion_and_migrates_event_aliases(self):
        candidate = design()
        candidate["elements"].append({"id": "E-MOTION", "kind": "motion", "type": "jet", "player_id": "P1", "points": [{"x": 20, "y": 5}, {"x": 40, "y": 5}], "arrow_style": "motion", "start_ms": -900, "end_ms": -100})
        candidate["timeline"]["markers"] = [{"id": "MOTION-CUE", "label": "Send jet", "kind": "cue", "ms": -900}]
        candidate["timeline"]["narration"] = [{"id": "N-MOTION", "text": "Send the jet before the snap.", "start_ms": -900, "end_ms": -100}]
        candidate["timeline"]["events"] = [{"id": "READ-1", "type": "qb_read", "at_ms": -100, "label": "Confirm rotation"}]
        normalized = normalize_timeline_design(candidate)
        motion = normalized["elements"][-1]
        self.assertEqual((motion["start_ms"], motion["end_ms"]), (-900, -100))
        self.assertEqual(normalized["timeline"]["markers"][0]["ms"], -900)
        self.assertEqual(normalized["timeline"]["events"][0]["kind"], "read")
        self.assertEqual(normalized["timeline"]["events"][0]["start_ms"], -100)
        self.assertEqual(normalized["timeline"]["events"][0]["end_ms"], 400)
        self.assertEqual(validate_timeline(normalized), [])

    def test_timeline_accepts_explicit_block_and_rush_exchange_cues(self):
        candidate = design()
        candidate["elements"][0]["id"] = "ROUTE-1"
        candidate["timeline"]["events"] = [
            {"id": "BLOCK-X", "kind": "block_exchange", "element_id": candidate["elements"][0]["id"], "start_ms": 300, "end_ms": 700},
            {"id": "RUSH-X", "kind": "rush_exchange", "element_id": candidate["elements"][0]["id"], "start_ms": 700, "end_ms": 1100},
        ]
        normalized = normalize_timeline_design(candidate)
        self.assertEqual([event["kind"] for event in normalized["timeline"]["events"]], ["block_exchange", "rush_exchange"])
        self.assertEqual(validate_timeline(normalized), [])

    def test_timeline_validation_explains_phase_and_exchange_errors(self):
        candidate = normalize_timeline_design(design())
        candidate["elements"][0]["exchange_with"] = "E-MISSING"
        candidate["elements"][0]["timing"]["phases"][0]["end_ms"] = -1
        codes = {issue["code"] for issue in validate_timeline(candidate)}
        self.assertIn("TIMELINE-EXCHANGE-REF", codes)
        self.assertIn("TIMELINE-PHASE-END", codes)

    def test_assignment_graph_reports_cycles_references_and_exclusive_conflicts(self):
        candidate = normalize_timeline_design(design())
        candidate["assignment_model_version"] = "1.0"
        candidate["elements"][0].update({"id": "E-ROUTE-1", "depends_on": ["E-READ"], "target_player_id": "P-MISSING", "exclusive_assignment": True, "phase": "development", "landmark": "seam"})
        candidate["elements"].append({
            "id": "E-READ", "kind": "read", "player_id": "P1", "type": "safety_key", "read_key": "post safety", "target_player_id": "P-MISSING",
            "depends_on": ["E-ROUTE-1"], "exclusive_assignment": True, "phase": "development", "landmark": "seam", "start_ms": 0, "end_ms": 900,
        })
        findings = validate_assignment_graph(candidate)
        codes = {issue["code"] for issue in findings}
        self.assertIn("ASSIGNMENT-TARGET-PLAYER", codes)
        self.assertIn("ASSIGNMENT-DEPENDENCY-CYCLE", codes)
        self.assertIn("ASSIGNMENT-EXCLUSIVE-CONFLICT", codes)
        graph = build_assignment_graph(candidate)
        self.assertEqual(graph["summary"]["node_count"], 2)
        self.assertGreaterEqual(graph["summary"]["edge_count"], 2)

    def test_assignment_graph_accepts_valid_read_and_exchange_relationships(self):
        candidate = normalize_timeline_design(design())
        candidate["assignment_model_version"] = "1.0"
        candidate["elements"][0].update({"id": "E-ROUTE", "objective": "Clear the middle", "landmark": "near upright", "depth_yards": 18})
        candidate["elements"].append({
            "id": "E-READ", "kind": "read", "player_id": "P1", "type": "safety_key", "read_key": "middle-field safety",
            "target_element_id": "E-ROUTE", "depends_on": [], "start_ms": 0, "end_ms": 500,
        })
        self.assertEqual(validate_assignment_graph(candidate), [])

    def test_advanced_legality_reports_route_collision_with_policy(self):
        candidate = design()
        candidate["elements"].append({"id": "E-ROUTE-2", "kind": "route", "player_id": "P1", "type": "post", "points": [{"x": 10, "y": 30}, {"x": 30, "y": 5}], "arrow_style": "route"})
        warning_codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-ROUTE-COLLISION", warning_codes)
        candidate["route_collision_policy"] = "error"
        findings = validate_advanced_legality(candidate)
        collision = next(issue for issue in findings if issue["code"] == "LEGALITY-ROUTE-COLLISION")
        self.assertEqual(collision["severity"], "error")
        self.assertTrue(collision["overrideable"])

    def test_route_collision_requires_both_intentional_crossing_explanations(self):
        candidate = design()
        candidate["elements"].append({"id": "E-ROUTE-2", "kind": "route", "player_id": "P1", "type": "post", "points": [{"x": 30, "y": 5}, {"x": 10, "y": 30}], "arrow_style": "route", "collision_intent": "intentional"})
        candidate["elements"][0]["collision_intent"] = "intentional"
        findings = validate_advanced_legality(candidate)
        explanation = next(issue for issue in findings if issue["code"] == "LEGALITY-ROUTE-CROSSING-EXPLANATION")
        self.assertEqual(explanation["severity"], "warning")
        candidate["elements"][0]["collision_intent"] = "intentional"
        candidate["elements"][0]["collision_note"] = "Mesh crossing by design."
        candidate["elements"][1]["collision_note"] = "Mesh crossing by design."
        findings = validate_advanced_legality(candidate)
        self.assertNotIn("LEGALITY-ROUTE-CROSSING-EXPLANATION", {issue["code"] for issue in findings})
        collision = next(issue for issue in findings if issue["code"] == "LEGALITY-ROUTE-COLLISION")
        self.assertTrue(collision["observed"]["documented"])

    def test_advanced_legality_reports_defensive_coverage_protection_and_fit_conflicts(self):
        candidate = design("defense")
        candidate["coverage_zones"] = ["deep_left", "deep_middle"]
        candidate["elements"] += [
            {"id": "COVER-L", "kind": "coverage", "player_id": "P1", "zone": "deep_left", "points": [{"x": 10, "y": 5}, {"x": 15, "y": 20}], "arrow_style": "coverage"},
            {"id": "BLOCK-1", "kind": "block", "player_id": "P2", "gap": "A", "points": [{"x": 20, "y": 5}, {"x": 20, "y": 20}], "arrow_style": "block"},
            {"id": "BLOCK-2", "kind": "block", "player_id": "P3", "gap": "A", "points": [{"x": 25, "y": 5}, {"x": 25, "y": 20}], "arrow_style": "block"},
            {"id": "FIT-1", "kind": "fit", "player_id": "P4", "fit_gap": "B", "responsibility": "spill", "points": [{"x": 30, "y": 5}, {"x": 30, "y": 20}], "arrow_style": "fit"},
            {"id": "FIT-2", "kind": "fit", "player_id": "P5", "fit_gap": "B", "responsibility": "box", "points": [{"x": 35, "y": 5}, {"x": 35, "y": 20}], "arrow_style": "fit"},
        ]
        codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-COVERAGE-GAP", codes)
        self.assertIn("LEGALITY-PROTECTION-CONFLICT", codes)
        self.assertIn("LEGALITY-FIT-CONFLICT", codes)

    def test_advanced_legality_explains_incomplete_defensive_semantics(self):
        candidate = design("defense")
        candidate["elements"] += [
            {"id": "FIT-INCOMPLETE", "kind": "fit", "player_id": "P1", "fit_gap": "C", "points": [{"x": 10, "y": 5}, {"x": 10, "y": 20}]},
            {"id": "COVER-INCOMPLETE", "kind": "coverage", "player_id": "P2", "points": [{"x": 20, "y": 5}, {"x": 20, "y": 20}]},
            {"id": "STUNT-INCOMPLETE", "kind": "stunt", "player_id": "P3", "points": [{"x": 30, "y": 5}, {"x": 30, "y": 20}]},
            {"id": "ROTATION-INCOMPLETE", "kind": "rotation", "player_id": "P4", "points": [{"x": 40, "y": 5}, {"x": 40, "y": 20}]},
        ]
        codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-FIT-RULE-UNDECLARED", codes)
        self.assertIn("LEGALITY-COVERAGE-RESPONSIBILITY-UNDECLARED", codes)
        self.assertIn("LEGALITY-RUSH-LANE-UNDECLARED", codes)
        self.assertIn("LEGALITY-STUNT-EXCHANGE-UNDECLARED", codes)
        self.assertIn("LEGALITY-ROTATION-TARGET-UNDECLARED", codes)

    def test_flag_profile_is_explicit_about_contact_rush_and_qb_constraints(self):
        candidate = design()
        candidate["rule_profile"] = "flag"
        candidate["players_on_field"] = 5
        candidate["players"][0]["position"] = "QB"
        candidate["elements"] += [
            {"id": "FLAG-BLOCK", "kind": "block", "player_id": "P1", "points": [{"x": 10, "y": 5}, {"x": 10, "y": 20}], "arrow_style": "block"},
            {"id": "FLAG-RUSH", "kind": "rush", "player_id": "P2", "rush_distance_yards": "malformed", "points": [{"x": 20, "y": 5}, {"x": 20, "y": 20}], "arrow_style": "rush"},
            {"id": "FLAG-QB-RUN", "kind": "run", "player_id": "P0", "points": [{"x": 30, "y": 5}, {"x": 30, "y": 20}], "arrow_style": "run"},
        ]
        codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-FLAG-CONTACT", codes)
        self.assertIn("LEGALITY-FLAG-RUSH-DISTANCE", codes)
        self.assertIn("LEGALITY-FLAG-QB-RUN", codes)

    def test_advanced_legality_checks_flag_count_declared_alignment_and_motion_reference(self):
        candidate = design()
        candidate["rule_profile"] = "flag"
        candidate["players_on_field"] = 5
        candidate["formation_constraints"] = {"on_line_count": 3, "eligible_count": 2, "backfield_count": 2}
        candidate["players"][0]["alignment"] = {"on_line": True, "eligible": True, "number": 1}
        candidate["elements"].append({"id": "MOTION-MISSING", "kind": "motion", "player_id": "P-MISSING", "points": [{"x": 10, "y": 5}, {"x": 20, "y": 5}], "snap_ms": 0, "start_ms": 100, "end_ms": 50})
        codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-FLAG-PLAYER-COUNT", codes)
        self.assertIn("LEGALITY-FORMATION-DECLARATION", codes)
        self.assertIn("LEGALITY-MOTION-PLAYER-REF", codes)
        self.assertIn("LEGALITY-MOTION-TIMING", codes)

    def test_rule_profile_metadata_preserves_authoritative_source_basis(self):
        profile = profile_metadata("nfl")
        self.assertEqual(profile["id"], "nfl")
        self.assertTrue(profile["source"]["uri"].startswith("https://"))
        self.assertIn("Rule 7-4-8", profile["source"]["rule_refs"])

    def test_declarative_rule_profile_catalog_matches_executable_policy(self):
        result = validate_rule_profile_catalog()
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["profile_count"], 5)
        self.assertEqual(result["issues"], [])


if __name__ == "__main__":
    unittest.main()
