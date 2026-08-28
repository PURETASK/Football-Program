import tempfile
from copy import deepcopy
import json
import unittest
from pathlib import Path

from src.nfl_fidos.play_design_service import PlayDesignService, load_asset_registry, validate_asset_registry
from src.nfl_fidos.play_design_versioning import build_snapshot, verify_design_integrity, verify_release_integrity
from src.nfl_fidos.play_design_collaboration import PlayDesignCollaborationService
from src.nfl_fidos.repository import JsonRepository
from src.nfl_fidos.tenant_repository import TenantRepository
from tests.test_play_creation import design


class PlayDesignServiceTests(unittest.TestCase):
    def service(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        temporary.close()
        path = Path(temporary.name)
        path.unlink()
        repository = JsonRepository(path)
        return PlayDesignService(TenantRepository(repository, organization_id="ORG-PLAY", actor="coach"))

    def test_variant_contract_describes_bounded_batch_and_assignment_transformations(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads((root / "contracts" / "play-design-variant.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(contract["properties"]["variants"]["maxItems"], 32)
        variant = contract["$defs"]["variant"]
        self.assertEqual(variant["required"], ["label", "patch"])
        assignment = contract["$defs"]["assignmentPatch"]
        self.assertEqual(variant["properties"]["assignment_patches"]["maxItems"], 64)
        self.assertEqual(assignment["properties"]["patch"]["additionalProperties"], False)
        self.assertEqual(assignment["properties"]["element_id"]["minLength"], 1)
        self.assertIn("route_family", assignment["properties"]["patch"]["properties"])

    def test_registry_exposes_assets_and_templates(self):
        service = self.service()
        self.assertGreaterEqual(len(service.assets()), 60)
        self.assertTrue(any(item["term"] == "cover_3" for item in service.assets(unit="defense")))
        self.assertTrue(any(item["unit"] == "offense" for item in service.templates()))
        dagger = next(item for item in service.templates() if item["id"] == "TPL-OFF-DAGGER-2X2")
        self.assertGreaterEqual(len(dagger["assignments"]), 5)
        self.assertEqual(len(dagger["alignment"]["slots"]), 11)
        self.assertEqual(dagger["template_kind"], "concept_layer")
        self.assertTrue(any("jet" in alias for item in service.assets(query="jet") for alias in item.get("aliases", [])))

    def test_professional_asset_registry_contract_is_complete_and_unique(self):
        report = validate_asset_registry(load_asset_registry())
        self.assertEqual(report["status"], "valid", report["errors"])
        self.assertGreaterEqual(report["asset_count"], 60)
        self.assertTrue({"formation", "route", "protection", "run", "front", "coverage", "pressure", "stunt", "rotation", "check", "teaching"}.issubset(set(report["categories"])))

    def test_saved_design_can_be_captured_as_org_scoped_relative_template(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-POST"
        saved = service.save(design=candidate, actor="coach")
        template = service.create_template(saved["id"], name="Boundary Post Package", actor="coach", description="Organization teaching standard.", tags=["third-down", "boundary"])
        self.assertEqual(template["scope"], "organization")
        self.assertEqual(template["source_design_id"], saved["id"])
        self.assertEqual(template["source_snapshot_id"], saved["latest_snapshot_id"])
        self.assertEqual(template["assignments"][0]["slot"], "WR")
        self.assertEqual(template["assignments"][0]["points"][0], {"dx": 0.0, "dy": 0.0})
        self.assertIn(template["id"], {item["id"] for item in service.templates()})

    def test_selected_assignments_can_be_captured_as_a_partial_stencil(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        temporary.close()
        path = Path(temporary.name)
        path.unlink()
        repository = JsonRepository(path)
        service = PlayDesignService(TenantRepository(repository, organization_id="ORG-TEST", actor="coach"))
        saved = service.save({
            "id": "DESIGN-STENCIL-1", "name": "Trips flood", "unit": "offense", "formation": "shotgun_trips",
            "players": [{"id": "X", "alignment_key": "X", "position": "WR", "start": {"x": 10, "y": 32}}],
            "elements": [
                {"id": "E-ROUTE", "kind": "route", "type": "go", "player_id": "X", "points": [{"x": 10, "y": 32}, {"x": 10, "y": 10}]},
                {"id": "E-NOTE", "kind": "annotation", "type": "clear", "depends_on": ["E-ROUTE"], "points": [{"x": 20, "y": 20}]},
            ],
        }, actor="coach")
        stencil = service.create_template(saved["id"], name="Selected clear-out", actor="coach", template_kind="concept_layer", layer="route_concept", element_ids=["E-ROUTE"])
        self.assertEqual(stencil["capture_scope"], "selection")
        self.assertEqual(stencil["source_element_ids"], ["E-ROUTE"])
        self.assertEqual([item["key"] for item in stencil["assignments"]], ["A-01"])
        self.assertEqual(stencil["assignments"][0]["slot"], "X")

    def test_template_can_inherit_a_parent_assignment_package(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-CHILD"
        saved = service.save(design=candidate, actor="coach")
        parent = service.create_template(saved["id"], name="Base package", actor="coach")
        child = service.create_template(saved["id"], name="Child variation", actor="coach", parent_template_id=parent["id"])
        self.assertEqual(child["parent_template_id"], parent["id"])
        self.assertEqual(len(child["inherited_assignments"]), len(parent["assignments"]))

    def test_batch_variants_are_draft_children_with_look_lineage(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-TRANSFORM"
        source = service.save(design=candidate, actor="coach")
        report = service.create_batch_variants(source["id"], actor="coach", variants=[
            {"label": "Cover 3", "patch": {"coverage": "cover_3"}},
            {"label": "Quarters", "patch": {"coverage": "quarters"}},
        ])
        self.assertEqual(report["count"], 2)
        self.assertTrue(report["id"].startswith("VARIANT-BATCH-"))
        self.assertEqual(len(report["variants"]), 2)
        self.assertTrue(all(item["parent_design_id"] == source["id"] for item in report["variants"]))
        self.assertEqual(report["variants"][0]["variant_look"]["patch"], {"coverage": "cover_3"})
        self.assertTrue(all(item["status"] == "draft" for item in report["variants"]))

    def test_batch_variants_apply_bounded_assignment_transformations(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-TRANSFORM"
        source = service.save(design=candidate, actor="coach")
        element_id = source["elements"][0]["id"]
        report = service.create_batch_variants(source["id"], actor="coach", variants=[
            {"label": "Alert variation", "patch": {"coverage": "cover_3"}, "assignment_patches": [{"element_id": element_id, "patch": {"type": "corner", "note": "Convert versus squat corner."}}]},
        ])
        child = report["variants"][0]
        changed = next(item for item in child["elements"] if item["id"] == element_id)
        self.assertEqual(changed["type"], "corner")
        self.assertEqual(changed["note"], "Convert versus squat corner.")
        self.assertEqual(child["variant_look"]["assignment_patches"][0]["element_id"], element_id)

    def test_batch_variants_reject_unknown_assignment_patch_targets(self):
        service = self.service()
        source = service.save(design=design(), actor="coach")
        with self.assertRaises(ValueError):
            service.create_batch_variants(source["id"], actor="coach", variants=[
                {"label": "Invalid", "patch": {"coverage": "cover_3"}, "assignment_patches": [{"element_id": "MISSING", "patch": {"type": "corner"}}]},
            ])

    def test_registry_returns_authoritative_compatibility_and_alignment_presets(self):
        service = self.service()
        assets = service.assets(unit="offense", context_formation="shotgun_trips", personnel="11", rule_profile="nfl")
        post = next(item for item in assets if item["term"] == "post")
        angle = next(item for item in assets if item["term"] == "angle")
        trips = next(item for item in assets if item["term"] == "shotgun_trips")
        self.assertTrue(post["compatibility"]["compatible"])
        self.assertFalse(angle["compatibility"]["compatible"])
        self.assertIn("formation", " ".join(angle["compatibility"]["reasons"]).lower())
        self.assertEqual(len(trips["alignment"]["slots"]), 11)
        self.assertEqual(trips["alignment"]["ball"]["y"], 26.5)

    def test_save_persists_design_and_builds_role_view(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        self.assertEqual(saved["organization_id"], "ORG-PLAY")
        self.assertEqual(saved["validation"]["status"], "valid")
        self.assertGreaterEqual(saved["timeline"]["duration_ms"], 3000)
        self.assertTrue(saved["elements"][0]["timing"]["phases"])
        view = service.role_view(saved["id"], role="WR")
        self.assertEqual(view["status"], "renderable")

    def test_snapshot_integrity_rejects_stale_checksum_and_verifies_published_release(self):
        candidate = design()
        candidate["checksum"] = "0" * 64
        integrity = verify_design_integrity(candidate)
        self.assertFalse(integrity["valid"])
        with self.assertRaises(ValueError):
            build_snapshot(candidate, actor="coach")

        service = self.service()
        saved = service.save(design=design(), actor="coach")
        service.request_review(saved["id"], actor="coach", decision_ref="DEC-REVIEW-INTEGRITY")
        service.publish(saved["id"], actor="owner", decision_ref="DEC-PUBLISH-INTEGRITY")
        release = service.repository.get("play_design_releases", "RELEASE-DESIGN-001-1.0.0")
        self.assertIsNotNone(release)
        self.assertTrue(verify_release_integrity(release)["valid"])

        tampered_release = deepcopy(release)
        tampered_release["bundle_manifest"]["content_checksum"] = "tampered"
        self.assertFalse(verify_release_integrity(tampered_release)["valid"])

    def test_role_view_normalizes_legacy_persisted_timeline_records(self):
        service = self.service()
        legacy = design()
        legacy["id"] = "DESIGN-LEGACY-TIMELINE"
        legacy["organization_id"] = "ORG-PLAY"
        legacy["timeline"] = {"duration_ms": 1400, "events": [{"id": "READ-1", "type": "qb_read", "at_ms": 350}]}
        legacy["elements"][0]["timing"] = {"start_ms": 100, "end_ms": 900, "phases": [{"id": "stem", "label": "Stem", "start_ms": 250, "end_ms": 600}]}
        service.repository.put("play_designs", legacy["id"], legacy, actor="migration", reason="legacy_fixture")
        view = service.role_view(legacy["id"], role="WR")
        self.assertEqual(view["timeline"]["events"][0]["kind"], "read")
        self.assertEqual(view["timeline"]["events"][0]["start_ms"], 350)
        self.assertEqual(view["steps"][0]["label"].split(" · ")[-1], "Stem")

    def test_save_detects_optimistic_revision_conflict(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        with self.assertRaises(ValueError):
            service.save(design=design(), actor="analyst", expected_revision=saved["_revision"] - 1)

    def test_review_publish_branch_and_comment_lifecycle(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        reviewed = service.request_review(saved["id"], actor="coach", decision_ref="DEC-REVIEW-1")
        self.assertEqual(reviewed["status"], "under_review")
        published = service.publish(saved["id"], actor="owner", decision_ref="DEC-PUBLISH-1")
        self.assertEqual(published["status"], "published")
        self.assertTrue(published["release_bundle"]["immutable"])
        self.assertEqual(published["latest_snapshot_id"], published["release_bundle"]["snapshot_id"])
        self.assertEqual(service.versions(saved["id"])["releases"][0]["snapshot_id"], published["latest_snapshot_id"])
        branch = service.branch(saved["id"], branch_id="DESIGN-BRANCH-1", actor="analyst")
        self.assertEqual(branch["parent_design_id"], saved["id"])
        comment = service.add_comment(branch["id"], actor="coach", text="Check the post depth.", element_id="E1")
        self.assertEqual(service.comments(branch["id"])[0]["id"], comment["id"])

    def test_version_diff_three_way_merge_and_draft_rollback(self):
        service = self.service()
        first = service.save(design=design(), actor="coach")
        edited = deepcopy(first)
        edited["elements"][0]["points"][1]["x"] = 44
        second = service.save(design=edited, actor="coach", expected_revision=first["_revision"])
        versions = service.versions(second["id"])
        self.assertGreaterEqual(len(versions["snapshots"]), 2)
        diff = service.diff(second["id"], base_snapshot_id=versions["snapshots"][0]["id"], compare_snapshot_id=versions["snapshots"][1]["id"])
        self.assertTrue(diff["diff"]["elements"]["changed"])
        self.assertEqual(diff["base_design"]["id"], second["id"])
        self.assertEqual(diff["compare_design"]["id"], second["id"])
        self.assertEqual(diff["compare_design"]["elements"][0]["points"][1]["x"], 44)
        self.assertNotEqual(versions["snapshots"][0]["id"], versions["snapshots"][1]["id"])

        branch = service.branch(second["id"], branch_id="DESIGN-MERGE-BRANCH", actor="analyst")
        branch_edit = deepcopy(branch)
        branch_edit["elements"][0]["points"][0]["x"] = 14
        branch_saved = service.save(branch_edit, actor="analyst", expected_revision=branch["_revision"])
        merged = service.merge(second["id"], branch_id=branch_saved["id"], actor="coach", expected_revision=second["_revision"])
        self.assertEqual(merged["status"], "merged")
        self.assertEqual(merged["design"]["elements"][0]["points"][0]["x"], 14)

        rollback_snapshot = versions["snapshots"][0]
        rolled_back = service.rollback(second["id"], snapshot_id=rollback_snapshot["id"], actor="owner", decision_ref="DEC-ROLLBACK-1", expected_revision=merged["design"]["_revision"])
        self.assertEqual(rolled_back["status"], "draft_rollback")
        self.assertEqual(rolled_back["design"]["status"], "draft")
        self.assertEqual(rolled_back["design"]["rolled_back_from_snapshot_id"], rollback_snapshot["id"])

    def test_asset_lifecycle_and_migration_are_scoped(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["asset_id"] = "ASSET-ROUTE-POST"
        service.save(design=candidate, actor="coach")
        override = service.update_asset_lifecycle("ASSET-ROUTE-POST", status="deprecated", actor="owner", replacement_id="ASSET-ROUTE-DIG", reason="catalog refresh")
        self.assertEqual(override["status"], "deprecated")
        migration = service.migrate_asset("ASSET-ROUTE-POST", "ASSET-ROUTE-DIG", actor="owner")
        self.assertEqual(migration["designs_migrated"], 1)
        deprecated = service.assets(query="post")[0]
        self.assertEqual(deprecated["status"], "deprecated")
        self.assertFalse(deprecated["compatibility"]["selectable"])
        self.assertEqual(deprecated["compatibility"]["replacement_id"], "ASSET-ROUTE-DIG")

    def test_teaching_views_filter_reveal_accessible_text_and_track_mastery(self):
        service = self.service()
        candidate = design()
        candidate["teaching"] = {"quizzes": [{"id": "QUIZ-1", "question": "What is the first read?", "options": ["Post", "Flat"], "answer": "Post"}]}
        candidate["practice_linkage"] = {"drill_ids": ["DRILL-READ-1"], "practice_refs": ["PRACTICE-WEEK-1"]}
        candidate["elements"][0]["read_key"] = "Safety"
        saved = service.save(design=candidate, actor="coach")
        view = service.role_view(saved["id"], role="WR", mode="player", step=0, user_id="PLAYER-1")
        self.assertEqual(view["status"], "renderable")
        self.assertIn("filtered_diagram", view)
        self.assertIn("Step 1", view["accessible_text"])
        self.assertTrue(view["read_reveal"])
        self.assertNotIn("answer", view["quizzes"][0])
        self.assertEqual(view["practice_linkage"]["drill_ids"], ["DRILL-READ-1"])
        mastery = service.record_mastery(saved["id"], role="WR", user_id="PLAYER-1", step_id=view["steps"][0]["id"], score=0.9, result="passed", actor="coach", practice_ref="DRILL-READ-1")
        self.assertEqual(mastery["status"], "mastered")
        mastered_view = service.role_view(saved["id"], role="WR", mode="player", step=0, user_id="PLAYER-1")
        self.assertTrue(mastered_view["steps"][0]["mastered"])
        quiz = service.submit_quiz(saved["id"], role="WR", user_id="PLAYER-1", quiz_id="QUIZ-1", answer="Post", actor="coach")
        self.assertTrue(quiz["correct"])
        self.assertNotIn("answer", quiz)
        summary = service.mastery(saved["id"], role="WR", user_id="PLAYER-1")
        self.assertEqual(summary["summary"]["mastered_step_count"], 2)

    def test_defensive_teaching_steps_include_exchange_gap_and_replacement_context(self):
        service = self.service()
        candidate = {
            "id": "DEF-TEACH-CONTEXT", "name": "Pressure Replace", "unit": "defense", "formation": "4-2-5_over", "personnel": "nickel",
            "players": [{"id": "DE-1", "position": "DE", "start": {"x": 36, "y": 20}}, {"id": "LB-1", "position": "WLB", "start": {"x": 48, "y": 20}}],
            "coverage_zones": ["flat_left"],
            "elements": [
                {"id": "RUSH-1", "kind": "rush", "type": "edge", "player_id": "DE-1", "gap_owner": "left_c", "exchange_with": "DROP-1", "exchange_role": "rush_replace", "timing": {"phases": [{"id": "exchange", "label": "Exchange", "start_ms": 250, "end_ms": 700}]}},
                {"id": "DROP-1", "kind": "coverage", "type": "hot_drop", "player_id": "LB-1", "exchange_with": "RUSH-1", "exchange_role": "drop_replace", "rotation_to_zone": "flat_left", "zone": "flat_left", "timing": {"phases": [{"id": "replace", "label": "Replace", "start_ms": 250, "end_ms": 850}]}},
            ],
            "timeline": {"duration_ms": 2000, "events": [{"id": "EX-1", "kind": "exchange", "element_id": "RUSH-1", "start_ms": 250, "end_ms": 700}]},
        }
        saved = service.save(design=candidate, actor="coach")
        view = service.role_view(saved["id"], role="WLB", mode="player", step=4, user_id="PLAYER-1")
        instructions = " ".join(item["instruction"] for item in view["steps"])
        self.assertIn("drop replace with RUSH-1", instructions)
        self.assertIn("Replace flat_left", instructions)
        self.assertIn("Replace", " ".join(item["label"] for item in view["steps"]))
        coach_view = service.role_view(saved["id"], role="coach", mode="coach")
        self.assertIn("Own left_c", " ".join(item["instruction"] for item in coach_view["steps"]))

    def test_collaboration_presence_events_and_thread_resolution_are_scoped(self):
        service = self.service()
        saved = service.save(design=design(), actor="coach")
        collaboration = PlayDesignCollaborationService(service.repository)
        presence = collaboration.heartbeat(design_id=saved["id"], session_id="SESSION-1", subject="COACH", role="coach_staff", display_name="Coach", color="#2563eb", cursor={"x": 42, "y": 18})
        self.assertEqual(collaboration.active_presence(design_id=saved["id"])[0]["session_id"], presence["session_id"])
        root = service.add_comment(saved["id"], actor="coach", text="Confirm the safety key.")
        reply = service.reply_comment(saved["id"], comment_id=root["id"], actor="analyst", text="Tagged in the install note.")
        resolved = service.resolve_comment(saved["id"], comment_id=root["id"], actor="coach")
        self.assertEqual(reply["thread_id"], root["id"])
        self.assertEqual(resolved["status"], "resolved")
        event = collaboration.record_event(design_id=saved["id"], event_type="comment_resolved", actor="coach", payload={"comment_id": root["id"]})
        self.assertEqual(collaboration.events(design_id=saved["id"])[0]["id"], event["id"])

    def test_legality_report_requires_owner_approved_expiring_override(self):
        service = self.service()
        candidate = design()
        candidate["route_collision_policy"] = "error"
        candidate["elements"].append({"id": "E-ROUTE-2", "kind": "route", "player_id": "P1", "type": "post", "points": [{"x": 10, "y": 30}, {"x": 30, "y": 5}], "arrow_style": "route"})
        saved = service.save(design=candidate, actor="coach")
        self.assertEqual(saved["validation"]["status"], "invalid")
        report = service.legality_report(saved["id"])
        self.assertEqual(report["status"], "invalid")
        request = service.request_legality_override(saved["id"], issue_code="LEGALITY-ROUTE-COLLISION", rationale="Crossing is a coached switch release in this install family.", decision_ref="DEC-REQUEST-1", evidence_refs=["film://clip/123", "install://switch-release"], expires_at="2099-01-01T00:00:00Z", actor="coach")
        self.assertEqual(request["status"], "pending_owner_approval")
        self.assertEqual(service.legality_report(saved["id"])["status"], "invalid")
        approved = service.approve_legality_override(saved["id"], override_id=request["id"], decision_ref="DEC-OWNER-1", actor="owner")
        self.assertEqual(approved["status"], "approved")
        revised = service.save(design=candidate, actor="coach", expected_revision=saved["_revision"])
        self.assertEqual(revised["validation"]["status"], "valid")
        collision = next(issue for issue in revised["validation"]["issues"] if issue["code"] == "LEGALITY-ROUTE-COLLISION")
        self.assertEqual(collision["status"], "overridden")
        self.assertEqual(collision["override"]["decision_ref"], "DEC-OWNER-1")

    def test_legality_override_rejects_malformed_or_expired_requests(self):
        service = self.service()
        candidate = design()
        candidate["route_collision_policy"] = "error"
        candidate["elements"].append({"id": "E-ROUTE-2", "kind": "route", "player_id": "P1", "type": "post", "points": [{"x": 10, "y": 30}, {"x": 30, "y": 5}], "arrow_style": "route"})
        saved = service.save(design=candidate, actor="coach")
        with self.assertRaises(ValueError):
            service.request_legality_override(saved["id"], issue_code="LEGALITY-ROUTE-COLLISION", rationale="", decision_ref="DEC-1", evidence_refs=["film://1"], expires_at="2099-01-01T00:00:00Z", actor="coach")
        with self.assertRaises(ValueError):
            service.request_legality_override(saved["id"], issue_code="LEGALITY-ROUTE-COLLISION", rationale="Documented reason", decision_ref="DEC-1", evidence_refs=["film://1"], expires_at="2000-01-01T00:00:00Z", actor="coach")


if __name__ == "__main__":
    unittest.main()
