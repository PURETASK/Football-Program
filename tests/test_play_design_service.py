import tempfile
from copy import deepcopy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.nfl_fidos.play_design_service import PROFESSIONAL_ASSIGNMENT_PATCH_FIELDS, PlayDesignService, load_asset_registry, validate_asset_registry
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

    def test_position_options_rank_compatible_assets_and_templates(self):
        result = self.service().position_options(position="QB", unit="offense", formation="shotgun_2x2", limit=8)
        self.assertEqual(result["family"], "qb")
        self.assertEqual(result["status"], "ready")
        self.assertLessEqual(len(result["assets"]), 8)
        self.assertTrue(result["assets"])
        self.assertIn("recommendation", result["assets"][0])

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
        for field in ("exchange_concept", "penetration_lane", "loop_landmark", "block_target_element_id", "protection_scan_order", "collision_note"):
            self.assertIn(field, assignment["properties"]["patch"]["properties"])

    def test_variant_schema_covers_every_runtime_assignment_patch_field(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads((root / "contracts" / "play-design-variant.schema.json").read_text(encoding="utf-8"))
        declared = set(contract["$defs"]["assignmentPatch"]["properties"]["patch"]["properties"])
        self.assertEqual(set(PROFESSIONAL_ASSIGNMENT_PATCH_FIELDS), declared)

    def test_canonical_play_schema_declares_every_runtime_assignment_field(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads((root / "contracts" / "play-design.schema.json").read_text(encoding="utf-8"))
        declared = set(contract["$defs"]["element"]["properties"])
        self.assertTrue(set(PROFESSIONAL_ASSIGNMENT_PATCH_FIELDS).issubset(declared))

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
        templates = {item["id"]: item for item in service.templates()}
        self.assertTrue({"TPL-OFF-EMPTY-QUICK", "TPL-OFF-COUNTER-GT", "TPL-DEF-TEX-ET"}.issubset(templates))
        self.assertTrue({"TPL-OFF-SMASH-2X2", "TPL-OFF-STICK-TRIPS", "TPL-OFF-FOUR-VERTICALS", "TPL-OFF-POWER-O", "TPL-DEF-C1-ROBBER", "TPL-DEF-C2-TRAP"}.issubset(templates))
        self.assertGreaterEqual(len(templates), 17)
        self.assertEqual(templates["TPL-OFF-EMPTY-QUICK"]["formation"], "shotgun_empty")
        self.assertEqual(templates["TPL-OFF-COUNTER-GT"]["assignments"][1]["type"], "pull")
        tex = templates["TPL-DEF-TEX-ET"]
        self.assertEqual(tex["assignments"][0]["partner_id"], "DE-L-ET")
        self.assertEqual(tex["assignments"][1]["exchange_role"], "looper")

    def test_template_registry_filters_by_play_context_and_search(self):
        service = self.service()
        trips = service.templates(unit="offense", formation="shotgun_trips")
        self.assertTrue(trips)
        self.assertTrue(all(item.get("formation") == "shotgun_trips" for item in trips))
        self.assertEqual(service.templates(unit="offense", formation="shotgun_trips", query="flood")[0]["concept"], "Flood")
        defensive = service.templates(unit="defense", front="4-2-5_over", coverage="cover_3")
        self.assertTrue(defensive)
        self.assertTrue(all(item.get("front") == "4-2-5_over" and item.get("coverage") == "cover_3" for item in defensive))
        self.assertIn("TPL-DEF-TEX-ET", {item["id"] for item in defensive})
        self.assertTrue(all(item.get("unit") == "offense" for item in service.templates(unit="offense", status="approved")))

    def test_professional_asset_registry_contract_is_complete_and_unique(self):
        report = validate_asset_registry(load_asset_registry())
        self.assertEqual(report["status"], "valid", report["errors"])
        self.assertGreaterEqual(report["asset_count"], 60)
        self.assertTrue({"formation", "route", "motion", "protection", "block", "run", "front", "coverage", "pressure", "stunt", "rotation", "check", "teaching"}.issubset(set(report["categories"])))
        terms = {asset["term"] for asset in load_asset_registry()}
        self.assertTrue({"under", "odd", "nickel", "dime", "tampa_2", "match_3", "quarters", "overload", "green_dog", "spin_rotation", "reach", "trap", "full_slide", "screen"}.issubset(terms))

    def test_asset_registry_rejects_orphaned_replacements_and_malformed_compatibility(self):
        invalid = [
            {"id": "ASSET-OLD", "category": "route", "kind": "route", "term": "old", "unit": "offense", "description": "Old", "accessibility": "Old", "version": "1.0.0", "status": "deprecated", "aliases": [], "replacement_id": "ASSET-MISSING", "compatible_formations": "shotgun"},
        ]
        report = validate_asset_registry(invalid)
        codes = {error["code"] for error in report["errors"]}
        self.assertIn("ASSET-CATEGORIES-MISSING", codes)
        self.assertIn("ASSET-REPLACEMENT-MISSING", codes)
        self.assertIn("ASSET-COMPATIBILITY-INVALID", codes)

    def test_concept_template_loader_rejects_invalid_timeline_and_exchange_references(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8")
        try:
            invalid = {
                "id": "TPL-INVALID", "name": "Invalid", "unit": "defense", "front": "4-2-5_over",
                "assignments": [{"key": "A", "kind": "stunt", "partner_id": "MISSING", "timing": {"start_ms": 500, "end_ms": 100}}],
                "timeline": {"duration_ms": 1000, "markers": [{"id": "DUP", "label": "One", "kind": "cue", "ms": 100}, {"id": "DUP", "label": "Two", "kind": "cue", "ms": 200}]},
            }
            json.dump({"templates": [invalid]}, temporary)
            temporary.close()
            from src.nfl_fidos import play_design_service as module
            with patch.object(module, "CONCEPT_TEMPLATES_PATH", Path(temporary.name)):
                with self.assertRaisesRegex(ValueError, "invalid timing bounds"):
                    module.load_concept_templates()
                invalid["assignments"][0]["timing"] = {"start_ms": 0, "end_ms": 100}
                Path(temporary.name).write_text(json.dumps({"templates": [invalid]}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unknown assignment key"):
                    module.load_concept_templates()
                invalid["assignments"][0]["partner_id"] = "A"
                Path(temporary.name).write_text(json.dumps({"templates": [invalid]}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate timeline marker"):
                    module.load_concept_templates()
            json.loads(Path(temporary.name).read_text(encoding="utf-8"))
        finally:
            Path(temporary.name).unlink(missing_ok=True)

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

    def test_template_lineage_impact_is_read_only_and_lists_descendants(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-LINEAGE"
        saved = service.save(design=candidate, actor="coach")
        parent = service.create_template(saved["id"], name="Base package", actor="coach")
        child_candidate = deepcopy(candidate)
        child_candidate["id"] = "DESIGN-LINEAGE-CHILD"
        child_candidate["elements"][0]["type"] = "corner"
        child_saved = service.save(design=child_candidate, actor="coach")
        child = service.create_template(child_saved["id"], name="Child variation", actor="coach", parent_template_id=parent["id"])
        report = service.template_lineage_impact(parent["id"])
        self.assertEqual(report["dependent_count"], 1)
        self.assertEqual(report["dependents"][0]["template_id"], child["id"])
        self.assertEqual(report["dependents"][0]["local_override_count"], 1)
        self.assertIn("type", report["dependents"][0]["overrides"][0]["fields"])
        self.assertTrue(report["propagation_required"])
        self.assertFalse(report["mutated"])
        self.assertIn(parent["id"], {item["id"] for item in service.templates()})
        proposal = service.propose_template_lineage_update(parent["id"], patches=[{"key": parent["assignments"][0]["key"], "patch": {"type": "corner"}}], actor="coach")
        self.assertEqual(proposal["status"], "pending_owner_approval")
        approved = service.approve_template_lineage_update(proposal["id"], decision_ref="DEC-TEMPLATE-LINEAGE-001", actor="owner")
        self.assertEqual(approved["status"], "approved_and_applied")
        self.assertTrue(approved["mutated"])
        self.assertIn(child["id"], approved["propagated_template_ids"])
        self.assertEqual(service.repository.get("play_design_templates", child["id"])["inherited_assignments"][0]["type"], "corner")

    def test_lineage_and_variant_boundaries_preserve_professional_assignment_fields(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-LINEAGE-ALLOWLIST"
        source_template = service.save(design=candidate, actor="coach")
        template = service.create_template(source_template["id"], name="Allowlist template", actor="coach")
        assignment_key = template["assignments"][0]["key"]
        proposal = service.propose_template_lineage_update(
            template["id"],
            patches=[{"key": assignment_key, "patch": {
                "exchange_concept": "tex", "penetration_lane": "B", "block_target_element_id": "TARGET",
                "protection_slide_direction": "left", "collision_intent": "intentional",
            }}],
            actor="coach",
        )
        self.assertEqual(proposal["patches"][0]["patch"]["penetration_lane"], "B")

        source = service.save(design={"id": "PLAY-ALLOWLIST-SOURCE", "unit": "offense", "elements": [{"id": "E-1", "kind": "block"}]}, actor="coach")
        report = service.create_batch_variants(source["id"], actor="coach", variants=[{
            "label": "Protection look", "patch": {"formation": "trips_right"},
            "assignment_patches": [{"element_id": "E-1", "patch": {"protection_scan_order": "edge-to-inside", "block_partner_element_id": "E-1"}}],
        }])
        self.assertEqual(report["variants"][0]["variant_look"]["assignment_patches"][0]["patch"]["protection_scan_order"], "edge-to-inside")

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

    def test_variant_batch_history_is_persisted_and_filterable_by_source(self):
        service = self.service()
        source = service.save(design(), actor="coach")
        first = service.create_batch_variants(source["id"], actor="coach", variants=[{"label": "Cover 3", "patch": {"coverage": "cover_3"}}], batch_id="VARIANT-BATCH-HISTORY-001")
        other_design = design()
        other_design["id"] = "PLAY-HISTORY-OTHER"
        other = service.save(other_design, actor="coach")
        service.create_batch_variants(other["id"], actor="coach", variants=[{"label": "Quarters", "patch": {"coverage": "quarters"}}], batch_id="VARIANT-BATCH-HISTORY-002")
        history = service.variant_batches(source_design_id=source["id"])
        self.assertEqual([item["id"] for item in history], [first["id"]])
        self.assertEqual(history[0]["variants"][0]["parent_design_id"], source["id"])
        self.assertEqual(history[0]["review"]["ready_count"], 1)
        self.assertTrue(history[0]["review"]["ready"])
        self.assertEqual(service.workspace()["variant_batches"][0]["id"], "VARIANT-BATCH-HISTORY-002")

    def test_variant_batch_review_moves_all_valid_children_under_review(self):
        service = self.service()
        source = service.save(design(), actor="coach")
        batch = service.create_batch_variants(source["id"], actor="coach", variants=[{"label": "Cover 3", "patch": {"coverage": "cover_3"}}, {"label": "Quarters", "patch": {"coverage": "quarters"}}], batch_id="VARIANT-BATCH-REVIEW-001")
        reviewed = service.request_variant_batch_review(batch["id"], actor="coach", decision_ref="DEC-REVIEW-BATCH-001")
        self.assertEqual(reviewed["status"], "under_review")
        self.assertEqual(reviewed["review_request"]["decision_ref"], "DEC-REVIEW-BATCH-001")
        self.assertTrue(all(service.repository.get("play_designs", item)["status"] == "under_review" for item in batch["variant_ids"]))
        self.assertTrue(all(service.repository.get("play_designs", item)["approval"]["state"] == "pending_approval" for item in batch["variant_ids"]))
        approved = service.approve_variant_batch_review(batch["id"], actor="owner", decision_ref="DEC-APPROVE-BATCH-001")
        self.assertEqual(approved["status"], "approved_for_release")
        self.assertEqual(approved["review_request"]["state"], "approved_for_release")
        self.assertTrue(all(service.repository.get("play_designs", item)["batch_approval"]["state"] == "approved_for_release" for item in batch["variant_ids"]))

        bundle = service.create_variant_release_bundle(batch["id"], actor="owner", decision_ref="DEC-BUNDLE-001")
        self.assertEqual(bundle["status"], "frozen")
        self.assertTrue(bundle["immutable"])
        self.assertFalse(bundle["production_activation"])
        self.assertEqual(bundle["manifest"]["variant_ids"], batch["variant_ids"])
        self.assertEqual(len(bundle["manifest_hash"]), 64)
        history_with_bundle = service.variant_batches(source_design_id=source["id"])[0]
        self.assertEqual(history_with_bundle["release_bundle"]["id"], bundle["id"])
        self.assertTrue(history_with_bundle["release_bundle"]["immutable"])
        self.assertTrue(history_with_bundle["release_bundle"]["integrity_valid"])
        inspected = service.inspect_variant_release_bundle(bundle["id"])
        self.assertTrue(inspected["integrity"]["valid"])
        tampered = service.repository.get("play_design_variant_release_bundles", bundle["id"])
        tampered["manifest"]["variant_ids"] = []
        service.repository.put("play_design_variant_release_bundles", bundle["id"], tampered, actor="TEST", reason="tamper_fixture")
        self.assertFalse(service.inspect_variant_release_bundle(bundle["id"])["integrity"]["valid"])
        with self.assertRaises(ValueError):
            service.create_variant_release_bundle(batch["id"], actor="owner", decision_ref="DEC-BUNDLE-REPEAT")

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
        history = service.versions(saved["id"])
        self.assertEqual(history["releases"][0]["snapshot_id"], published["latest_snapshot_id"])
        self.assertTrue(all(snapshot["integrity"]["valid"] for snapshot in history["snapshots"]))
        self.assertTrue(history["releases"][0]["integrity"]["valid"])
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

    def test_collaboration_event_retries_are_idempotent_and_sequences_remain_monotonic(self):
        service = self.service()
        candidate = design()
        candidate["elements"][0]["id"] = "E-EVENT-RETRY"
        saved = service.save(design=candidate, actor="coach")
        collaboration = PlayDesignCollaborationService(service.repository)
        first = collaboration.record_event(design_id=saved["id"], event_type="design_saved", actor="coach", payload={"revision": 1}, idempotency_key="MUTATION-001")
        retry = collaboration.record_event(design_id=saved["id"], event_type="design_saved", actor="coach", payload={"revision": 1}, idempotency_key="MUTATION-001")
        second = collaboration.record_event(design_id=saved["id"], event_type="comment_added", actor="coach", payload={"comment_id": "COMMENT-1"}, idempotency_key="MUTATION-002")
        self.assertEqual(retry["id"], first["id"])
        self.assertEqual(len(collaboration.events(design_id=saved["id"])), 2)
        self.assertLess(first["sequence"], second["sequence"])
        self.assertEqual([item["sequence"] for item in collaboration.events(design_id=saved["id"])], [1, 2])
        with self.assertRaisesRegex(ValueError, "different collaboration event"):
            collaboration.record_event(design_id=saved["id"], event_type="comment_resolved", actor="coach", payload={"comment_id": "COMMENT-1"}, idempotency_key="MUTATION-002")

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
