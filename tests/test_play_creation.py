import unittest

from src.nfl_fidos.play_creation import normalize_term, validate_legality, validate_play_design
from src.nfl_fidos.play_assignment_graph import build_assignment_graph, build_coverage_shell_map, build_gap_ownership_map, build_player_assignment_summary, validate_assignment_graph
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

    def test_route_semantics_require_controlled_vocabulary_and_bounded_depth(self):
        candidate = design()
        candidate["elements"][0].update({"route_family": "dropback", "break_type": "dig", "stem_depth_yards": 12, "break_depth_yards": 14, "finish_direction": "inside", "option_rule": "leverage"})
        self.assertEqual(validate_play_design(candidate), [])

        candidate["elements"][0].update({"route_family": "invented", "break_type": "none", "break_depth_yards": 70, "finish_direction": "sideways", "option_rule": "invented"})
        codes = {issue["code"] for issue in validate_play_design(candidate)}
        self.assertIn("DESIGN-ROUTE-SEMANTIC", codes)
        self.assertIn("DESIGN-ROUTE-DEPTH", codes)
        self.assertIn("DESIGN-ROUTE-BREAK-CONTEXT", codes)

    def test_route_branch_semantics_are_validated_with_parent_compatible_fields(self):
        candidate = design()
        candidate["elements"][0].update({"route_family": "dropback", "break_type": "dig", "stem_depth_yards": 12})
        candidate["elements"][0]["branches"] = [{"id": "OPTION-A", "points": [{"x": 10, "y": 5}, {"x": 20, "y": 20}], "break_type": "made_up", "break_depth_yards": 61}]
        codes = {issue["code"] for issue in validate_play_design(candidate)}
        self.assertIn("DESIGN-ROUTE-SEMANTIC", codes)
        self.assertIn("DESIGN-ROUTE-DEPTH", codes)

    def test_offensive_blocking_primitives_require_valid_targets_and_protection_context(self):
        candidate = design()
        candidate["elements"] = [
            {"id": "PULL", "kind": "block", "player_id": "P1", "blocking_primitive": "pull", "block_target_element_id": "MISSING", "arrow_style": "block", "points": [{"x": 20, "y": 20}, {"x": 30, "y": 20}]},
            {"id": "TRAP", "kind": "block", "player_id": "P3", "blocking_primitive": "trap", "arrow_style": "block", "points": [{"x": 15, "y": 20}, {"x": 25, "y": 20}]},
            {"id": "BAD", "kind": "block", "player_id": "P2", "blocking_primitive": "not_a_block", "protection_mode": "unknown", "arrow_style": "block", "points": [{"x": 30, "y": 20}, {"x": 35, "y": 20}]},
        ]
        codes = {issue["code"] for issue in validate_play_design(candidate)}
        self.assertIn("DESIGN-BLOCK-TARGET", codes)
        self.assertIn("DESIGN-BLOCK-PRIMITIVE", codes)
        self.assertIn("DESIGN-PROTECTION-MODE", codes)
        self.assertIn("DESIGN-BLOCK-TARGET-REF", codes)

        candidate["elements"][0].update({"block_target_element_id": "BAD", "protection_mode": "half_slide_left", "protection_target_element_id": "BAD"})
        candidate["elements"][1].update({"blocking_primitive": "combo", "block_partner_element_id": "PULL", "block_target_element_id": "PULL", "protection_mode": "screen"})
        self.assertNotIn("DESIGN-BLOCK-TARGET", {issue["code"] for issue in validate_play_design(candidate)})
        self.assertNotIn("DESIGN-BLOCK-TARGET-REF", {issue["code"] for issue in validate_play_design(candidate)})

    def test_flag_profile_uses_flag_player_count_in_structural_validation(self):
        candidate = design("offense")
        candidate["rule_profile"] = "flag"
        candidate["players_on_field"] = 5
        candidate["players"] = candidate["players"][:5]
        candidate["players"][0]["position"] = "QB"
        candidate["elements"] = [{"kind": "route", "player_id": "P1", "type": "slant", "points": [{"x": 17, "y": 5}, {"x": 25, "y": 20}], "arrow_style": "route"}]
        issues = validate_play_design(candidate)
        self.assertNotIn("DESIGN-PLAYER-COUNT", {issue["code"] for issue in issues})
        self.assertNotIn("LEGALITY-LINE-COUNT", {issue["code"] for issue in validate_legality(candidate)})

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

    def test_alternate_paths_use_the_same_shape_and_bounds_contract_as_primary_paths(self):
        candidate = design()
        candidate["elements"][0]["branches"] = [{"id": "BRANCH-OOB", "points": [{"x": 10, "y": 20}, {"x": 101, "y": 20}]}]
        issues = validate_play_design(candidate)
        self.assertTrue(any(issue["code"] == "DESIGN-BOUNDS" and issue["path"] == "elements[0].branches[0].points[1]" for issue in issues))

        malformed = design()
        malformed["elements"][0]["branches"] = [{"id": "BRANCH-SHORT", "points": [{"x": 10, "y": 20}]}]
        self.assertIn("DESIGN-BRANCH-PATH", {issue["code"] for issue in validate_play_design(malformed)})

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

    def test_timeline_explains_unsynchronized_events_and_reads(self):
        candidate = design()
        candidate["elements"][0].update({"id": "ROUTE-1", "start_ms": 0, "end_ms": 600})
        candidate["elements"].append({"id": "ROUTE-2", "kind": "route", "player_id": "P1", "type": "dig", "points": [{"x": 17, "y": 5}, {"x": 35, "y": 25}], "arrow_style": "route", "start_ms": 900, "end_ms": 1500})
        candidate["timeline"] = {"snap_ms": 0, "duration_ms": 2000, "events": [
            {"id": "READ-1", "kind": "read", "element_id": "ROUTE-1", "target_element_id": "ROUTE-2", "start_ms": 700, "end_ms": 800, "sync_group": "QB-DECISION"},
            {"id": "THROW-1", "kind": "throw", "element_id": "ROUTE-2", "start_ms": 1200, "end_ms": 1300, "sync_group": "QB-DECISION"},
        ]}
        codes = {issue["code"] for issue in validate_timeline(candidate)}
        self.assertIn("TIMELINE-EVENT-ELEMENT-WINDOW", codes)
        self.assertIn("TIMELINE-READ-TARGET-WINDOW", codes)
        self.assertIn("TIMELINE-SYNC-GROUP-GAP", codes)

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

    def test_assignment_graph_validates_named_tex_partner_positions_and_reciprocal_roles(self):
        candidate = design("defense")
        candidate["assignment_model_version"] = "1.0"
        candidate["players"] = [{"id": "DT", "position": "DT"}, {"id": "DE", "position": "DE"}]
        candidate["elements"] = [
            {"id": "A-TEX", "kind": "stunt", "player_id": "DT", "exchange_with": "B-TEX", "exchange_role": "penetrate_loop", "exchange_concept": "tex", "exchange_trigger": "on_snap", "exchange_communication": "TEX alert"},
            {"id": "B-TEX", "kind": "stunt", "player_id": "DE", "exchange_with": "A-TEX", "exchange_role": "loop_penetrate", "exchange_concept": "tex", "exchange_trigger": "on_snap", "exchange_communication": "TEX alert"},
        ]
        self.assertEqual(validate_assignment_graph(candidate), [])
        candidate["players"][1]["position"] = "CB"
        codes = {issue["code"] for issue in validate_assignment_graph(candidate)}
        self.assertIn("ASSIGNMENT-EXCHANGE-PARTNER-MISMATCH", codes)

    def test_assignment_graph_requires_named_exchange_metadata_on_both_sides(self):
        candidate = design("defense")
        candidate["assignment_model_version"] = "1.0"
        candidate["players"] = [{"id": "MIKE", "position": "MIKE"}, {"id": "WILL", "position": "WILL"}]
        candidate["elements"] = [
            {"id": "A-DOG", "kind": "rush", "player_id": "MIKE", "exchange_with": "B-DOG", "exchange_role": "penetrate_loop", "exchange_concept": "cross_dog"},
            {"id": "B-DOG", "kind": "stunt", "player_id": "WILL", "exchange_with": "A-DOG", "exchange_role": "loop_penetrate", "exchange_concept": "cross_dog"},
        ]
        codes = {issue["code"] for issue in validate_assignment_graph(candidate)}
        self.assertIn("ASSIGNMENT-EXCHANGE-COMMUNICATION-MISSING", codes)

    def test_assignment_graph_rejects_non_reciprocal_named_exchange_concept(self):
        candidate = design("defense")
        candidate["assignment_model_version"] = "1.0"
        candidate["players"] = [{"id": "DT", "position": "DT"}, {"id": "DE", "position": "DE"}]
        candidate["elements"] = [
            {"id": "A-ET", "kind": "stunt", "player_id": "DT", "exchange_with": "B-ET", "exchange_role": "penetrate_loop", "exchange_concept": "et", "exchange_trigger": "on_snap", "exchange_communication": "ET alert"},
            {"id": "B-ET", "kind": "stunt", "player_id": "DE", "exchange_with": "A-ET", "exchange_role": "loop_penetrate"},
        ]
        codes = {issue["code"] for issue in validate_assignment_graph(candidate)}
        self.assertIn("ASSIGNMENT-EXCHANGE-CONCEPT-RECIPROCITY", codes)

    def test_assignment_graph_nodes_preserve_professional_authoring_semantics(self):
        candidate = normalize_timeline_design(design())
        candidate["assignment_model_version"] = "1.0"
        candidate["elements"][0].update({
            "id": "ROUTE-SEMANTIC", "route_family": "dropback", "break_type": "dig",
            "stem_depth_yards": 12, "break_depth_yards": 14, "responsibility": "clear middle",
            "landmark": "near hash", "target_player_id": "P1",
        })
        node = next(item for item in build_assignment_graph(candidate)["nodes"] if item["id"] == "ROUTE-SEMANTIC")
        self.assertEqual(node["route_family"], "dropback")
        self.assertEqual(node["break_type"], "dig")
        self.assertEqual(node["stem_depth_yards"], 12)
        self.assertEqual(node["break_depth_yards"], 14)
        self.assertEqual(node["responsibility"], "clear middle")

    def test_assignment_graph_connects_protection_target_partner_and_threat_edges(self):
        candidate = normalize_timeline_design(design())
        candidate["assignment_model_version"] = "1.0"
        candidate["elements"] = [
            {"id": "BLOCK-1", "kind": "block", "player_id": "P1", "blocking_primitive": "combo", "block_target_element_id": "THREAT", "block_partner_element_id": "BLOCK-2", "protection_target_element_id": "THREAT", "points": [{"x": 10, "y": 5}, {"x": 20, "y": 15}], "arrow_style": "block"},
            {"id": "BLOCK-2", "kind": "block", "player_id": "P2", "blocking_primitive": "combo", "block_target_element_id": "THREAT", "block_partner_element_id": "BLOCK-1", "points": [{"x": 17, "y": 5}, {"x": 25, "y": 15}], "arrow_style": "block"},
            {"id": "THREAT", "kind": "rush", "player_id": "P3", "points": [{"x": 30, "y": 5}, {"x": 25, "y": 15}], "arrow_style": "rush"},
        ]
        relations = {(edge["target"], edge["relation"]) for edge in build_assignment_graph(candidate)["edges"]}
        self.assertIn(("THREAT", "blocks_assignment"), relations)
        self.assertIn(("BLOCK-2", "combo_partner"), relations)
        self.assertIn(("THREAT", "protects_against"), relations)

    def test_player_assignment_summary_reports_assignment_coverage_and_targets(self):
        candidate = design()
        candidate["players"] = [{"id": "QB", "position": "QB"}, {"id": "WR-X", "position": "WR"}]
        candidate["elements"] = [{"id": "READ", "kind": "read", "player_id": "QB", "target_element_id": "ROUTE"}, {"id": "ROUTE", "kind": "route", "player_id": "WR-X", "type": "dig", "points": [{"x": 10, "y": 5}, {"x": 20, "y": 20}], "arrow_style": "route"}]
        result = build_player_assignment_summary(candidate)
        by_player = {item["player_id"]: item for item in result["entries"]}
        self.assertEqual(result["status"], "complete")
        self.assertEqual(by_player["QB"]["targets"], ["ROUTE"])
        self.assertEqual(by_player["WR-X"]["kinds"], ["route"])

    def test_gap_ownership_map_preserves_assigned_unassigned_and_conflicted_states(self):
        candidate = design("defense")
        candidate["declared_gaps"] = ["A", "B", "C"]
        candidate["elements"] = [
            {"id": "FIT-A", "kind": "fit", "player_id": "MIKE", "gap_owner": "A", "responsibility": "spill", "points": [{"x": 20, "y": 20}, {"x": 20, "y": 25}]},
            {"id": "FIT-B1", "kind": "fit", "player_id": "WILL", "gap_owner": "B", "responsibility": "box", "points": [{"x": 30, "y": 20}, {"x": 30, "y": 25}]},
            {"id": "FIT-B2", "kind": "fit", "player_id": "SAM", "gap_owner": "B", "responsibility": "force", "points": [{"x": 35, "y": 20}, {"x": 35, "y": 25}]},
        ]

        result = build_gap_ownership_map(candidate)

        self.assertEqual(result["status"], "conflicted")
        self.assertEqual(result["assigned_count"], 1)
        self.assertEqual(result["unassigned_count"], 1)
        self.assertEqual(result["conflicted_count"], 1)
        by_gap = {item["gap"]: item for item in result["entries"]}
        self.assertEqual(by_gap["A"]["owners"][0]["player_id"], "MIKE")
        self.assertEqual(by_gap["B"]["owner_count"], 2)
        self.assertEqual(by_gap["C"]["status"], "unassigned")

    def test_coverage_shell_map_preserves_rotation_sequence_and_replacement_context(self):
        candidate = design("defense")
        candidate["coverage_zones"] = ["flat_left", "deep_middle"]
        candidate["elements"] = [
            {"id": "DROP-FLAT", "kind": "coverage", "player_id": "CB", "zone": "flat_left", "responsibility": "curl-flat", "points": [{"x": 15, "y": 28}, {"x": 13, "y": 20}]},
            {"id": "ROTATE-MIDDLE", "kind": "rotation", "player_id": "SS", "rotation_to_zone": "deep_middle", "rotation_from_zone": "flat_right", "rotation_sequence": 2, "rotation_trigger": "motion", "rotation_replacement_player_id": "FS", "exchange_with": "DROP-FLAT", "points": [{"x": 65, "y": 15}, {"x": 50, "y": 8}]},
        ]

        result = build_coverage_shell_map(candidate)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["rotation_count"], 1)
        middle = next(item for item in result["entries"] if item["zone"] == "deep_middle")
        self.assertEqual(middle["owners"][0]["rotation_sequence"], 2)
        self.assertEqual(middle["owners"][0]["vacated_zone"], "flat_right")
        self.assertEqual(middle["owners"][0]["replacement_player_id"], "FS")

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
        self.assertEqual(collision["observed"]["corridors"][0]["point"], {"x": 20.0, "y": 17.5})

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
        self.assertEqual(len(collision["observed"]["corridors"]), 1)

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

    def test_local_rule_constraints_make_youth_profile_explicit_and_explainable(self):
        candidate = design()
        candidate["rule_profile"] = "youth"
        candidate["local_rule_constraints"] = {"players_on_field": 8, "minimum_line_players": 5, "max_motion_at_snap": 1, "allow_blocking": True, "qb_direct_run_allowed": True}
        candidate["local_rule_source_ref"] = "ORG-LEAGUE-RULEBOOK-2026"
        findings = validate_advanced_legality(candidate)
        codes = {issue["code"] for issue in findings}
        self.assertIn("LEGALITY-PLAYER-COUNT", codes)
        self.assertNotIn("LEGALITY-LOCAL-RULE-SOURCE", codes)
        player_count = next(issue for issue in findings if issue["code"] == "LEGALITY-PLAYER-COUNT")
        self.assertEqual(player_count["expected"], 8)
        self.assertEqual(player_count["rule_profile"], "youth")

    def test_local_rule_constraints_reject_unknown_or_malformed_fields(self):
        candidate = design()
        candidate["rule_profile"] = "high_school"
        candidate["local_rule_constraints"] = {"players_on_field": "eleven", "unsupported_rule": True}
        codes = {issue["code"] for issue in validate_advanced_legality(candidate)}
        self.assertIn("LEGALITY-LOCAL-CONSTRAINT-FIELD", codes)
        self.assertIn("LEGALITY-LOCAL-CONSTRAINT-TYPE", codes)

    def test_no_contact_profiles_only_reject_explicit_contact_assignments(self):
        candidate = design()
        candidate["rule_profile"] = "youth"
        candidate["local_rule_constraints"] = {"players_on_field": 11, "allow_blocking": None}
        candidate["local_rule_source_ref"] = "ORG-YOUTH-RULEBOOK"
        candidate["elements"].append({"id": "CONTACT-1", "kind": "annotation", "assignment_type": "contact", "player_id": "P1", "points": [{"x": 10, "y": 30}, {"x": 12, "y": 28}]})
        self.assertNotIn("LEGALITY-FLAG-CONTACT", {issue["code"] for issue in validate_advanced_legality(candidate)})

    def test_nfl_number_and_line_end_eligibility_are_explainable(self):
        candidate = design()
        candidate["unit"] = "offense"
        for index, player in enumerate(candidate["players"][:7]):
            player["start"] = {"x": 10 + index * 10, "y": 12}
            player["alignment"] = {"on_line": True, "eligible": index in {1, 6}, "number": 55 if index == 1 else index + 1}
        findings = validate_advanced_legality(candidate)
        codes = {issue["code"] for issue in findings}
        self.assertIn("LEGALITY-FORMATION-END-ELIGIBILITY", codes)
        self.assertIn("LEGALITY-ELIGIBLE-NUMBER", codes)
        eligible_number = next(issue for issue in findings if issue["code"] == "LEGALITY-ELIGIBLE-NUMBER")
        self.assertEqual(eligible_number["rule_profile"], "nfl")
        self.assertIn("reported_eligible", eligible_number["expected"])


if __name__ == "__main__":
    unittest.main()
