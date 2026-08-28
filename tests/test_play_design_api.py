import os
import sys
import tempfile
from copy import deepcopy
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from tests.test_play_creation import design


class PlayDesignApiTests(unittest.TestCase):
    def test_variant_api_rejects_malformed_contract_shapes_before_service(self):
        secret = "play-design-variant-shape-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-VARIANT-SHAPE", role="coach_staff", organization_id="ORG-VARIANT-SHAPE", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            cases = [
                ({"label": 7, "patch": {"coverage": "cover_3"}}, "label must be a string"),
                ({"label": "Cover 3", "patch": []}, "patch must be an object"),
                ({"label": "Cover 3", "patch": {}, "assignment_patches": {}}, "assignment_patches must be a list"),
                ({"label": "Cover 3", "patch": {}, "assignment_patches": [{"element_id": 7, "patch": {"type": "corner"}}]}, "element_id must be a string"),
            ]
            for variant, message in cases:
                status, payload = handle_request(method="POST", path="/v1/playbook/designs/variants", headers=coach, body={"organization_id":"ORG-VARIANT-SHAPE", "design_id":"UNKNOWN", "variants":[variant]}, service=service)
                self.assertEqual(status, 400)
                self.assertIn(message, payload["error"])
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_variant_history_api_is_organization_scoped_and_source_filterable(self):
        secret = "play-design-variant-history-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-HISTORY", role="coach_staff", organization_id="ORG-DESIGN-HISTORY", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.sqlite3"))
            status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-HISTORY", "design":design()}, service=service)
            self.assertEqual(status, 201)
            design_id = created["data"]["id"]
            status, _ = handle_request(method="POST", path="/v1/playbook/designs/variants", headers=coach, body={"organization_id":"ORG-DESIGN-HISTORY", "design_id":design_id, "batch_id":"VARIANT-BATCH-HISTORY-API-001", "variants":[{"label":"Cover 3", "patch":{"coverage":"cover_3"}}]}, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path=f"/v1/playbook/designs/variants?organization_id=ORG-DESIGN-HISTORY&source_design_id={design_id}", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["count"], 1)
            self.assertEqual(payload["data"]["batches"][0]["id"], "VARIANT-BATCH-HISTORY-API-001")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_variant_batch_review_request_is_role_scoped_and_updates_children(self):
        secret = "play-design-variant-review-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-REVIEW-BATCH", role="coach_staff", organization_id="ORG-DESIGN-REVIEW-BATCH", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-REVIEW-BATCH", "design":design()}, service=service)
            self.assertEqual(status, 201)
            design_id = created["data"]["id"]
            status, batch = handle_request(method="POST", path="/v1/playbook/designs/variants", headers=coach, body={"organization_id":"ORG-DESIGN-REVIEW-BATCH", "design_id":design_id, "batch_id":"VARIANT-BATCH-REVIEW-API-001", "variants":[{"label":"Cover 3", "patch":{"coverage":"cover_3"}}]}, service=service)
            self.assertEqual(status, 201)
            status, reviewed = handle_request(method="POST", path="/v1/playbook/designs/variants/request-review", headers=coach, body={"organization_id":"ORG-DESIGN-REVIEW-BATCH", "batch_id":batch["data"]["id"], "decision_ref":"DEC-REVIEW-BATCH-API-001"}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(reviewed["data"]["status"], "under_review")
            self.assertEqual(reviewed["data"]["review_request"]["decision_ref"], "DEC-REVIEW-BATCH-API-001")
            child = service.repository.get("play_designs", batch["data"]["variant_ids"][0])
            self.assertEqual(child["status"], "under_review")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_variant_batch_approval_requires_program_owner_and_does_not_publish(self):
        secret = "play-design-variant-approval-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-APPROVAL", role="coach_staff", organization_id="ORG-DESIGN-APPROVAL", secret=secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-APPROVAL", role="program_owner", organization_id="ORG-DESIGN-APPROVAL", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-APPROVAL", "design":design()}, service=service)
            self.assertEqual(status, 201)
            status, batch = handle_request(method="POST", path="/v1/playbook/designs/variants", headers=coach, body={"organization_id":"ORG-DESIGN-APPROVAL", "design_id":created["data"]["id"], "batch_id":"VARIANT-BATCH-APPROVAL-API-001", "variants":[{"label":"Cover 3", "patch":{"coverage":"cover_3"}}]}, service=service)
            self.assertEqual(status, 201)
            status, _ = handle_request(method="POST", path="/v1/playbook/designs/variants/request-review", headers=coach, body={"organization_id":"ORG-DESIGN-APPROVAL", "batch_id":batch["data"]["id"], "decision_ref":"DEC-REVIEW-APPROVAL-API"}, service=service)
            self.assertEqual(status, 200)
            denied_status, _ = handle_request(method="POST", path="/v1/playbook/designs/variants/approve-review", headers=coach, body={"organization_id":"ORG-DESIGN-APPROVAL", "batch_id":batch["data"]["id"], "decision_ref":"DEC-DENIED-APPROVAL-API"}, service=service)
            self.assertEqual(denied_status, 403)
            status, approved = handle_request(method="POST", path="/v1/playbook/designs/variants/approve-review", headers=owner, body={"organization_id":"ORG-DESIGN-APPROVAL", "batch_id":batch["data"]["id"], "decision_ref":"DEC-APPROVE-API"}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(approved["data"]["status"], "approved_for_release")
            child = service.repository.get("play_designs", batch["data"]["variant_ids"][0])
            self.assertEqual(child["status"], "under_review")
            self.assertNotIn("release_id", child)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_export_preflight_is_org_scoped_and_returns_structured_blockers(self):
        secret = "play-design-preflight-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PREFLIGHT-API", role="coach_staff", organization_id="ORG-DESIGN-PREFLIGHT", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-PREFLIGHT", "design":design()}, service=service)
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            status, payload = handle_request(method="POST", path="/v1/playbook/designs/export/preflight", headers=coach, body={"organization_id":"ORG-DESIGN-PREFLIGHT", "design_ids":[design_id], "kind":"wristband", "format":"pdf", "layout":"wristband_3col", "role":"P1"}, service=service)
            self.assertEqual(status, 200)
            self.assertTrue(payload["data"]["can_render"])
            self.assertEqual(payload["data"]["layout"], "wristband_3col")
            self.assertEqual(payload["data"]["role"], "P1")
            self.assertNotIn("content_base64", payload["data"])
            broken = deepcopy(created["data"])
            broken["players"] = broken["players"][:9]
            broken_status, broken_payload = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-PREFLIGHT", "design":broken, "expected_revision":created["data"]["_revision"]}, service=service)
            self.assertEqual(broken_status, 201)
            status, payload = handle_request(method="POST", path="/v1/playbook/designs/export/preflight", headers=coach, body={"organization_id":"ORG-DESIGN-PREFLIGHT", "design_ids":[design_id], "kind":"play_card", "format":"pdf"}, service=service)
            self.assertEqual(status, 200)
            self.assertFalse(payload["data"]["can_render"])
            self.assertIn("EXPORT-PLAYER-COUNT", {issue["code"] for issue in payload["data"]["validation"]["issues"]})
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_live_draft_validation_is_explainable_and_does_not_persist(self):
        secret = "play-design-preview-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PREVIEW-API", role="coach_staff", organization_id="ORG-DESIGN-PREVIEW", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            candidate = design()
            candidate["assignment_model_version"] = "1.0"
            candidate["elements"][0].update({"id": "E-PREVIEW", "target_player_id": "MISSING-PLAYER"})
            status, payload = handle_request(method="POST", path="/v1/playbook/designs/validate", headers=coach, body={"organization_id":"ORG-DESIGN-PREVIEW", "design":candidate}, service=service)
            self.assertEqual(status, 200)
            self.assertTrue(payload["data"]["draft"])
            self.assertFalse(payload["data"]["persisted"])
            self.assertEqual(payload["data"]["status"], "invalid")
            self.assertIn("ASSIGNMENT-TARGET-PLAYER", {issue["code"] for issue in payload["data"]["issues"]})
            self.assertEqual(payload["data"]["assignment_graph"]["summary"]["node_count"], 1)
            workspace_status, workspace = handle_request(method="GET", path="/v1/playbook/designs?organization_id=ORG-DESIGN-PREVIEW", headers=coach, service=service)
            self.assertEqual(workspace_status, 200)
            self.assertEqual(workspace["data"]["designs"], [])
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_design_registry_persistence_review_branch_and_publish(self):
        secret = "play-design-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-DESIGN-API", role="coach_staff", organization_id="ORG-DESIGN-API", secret=secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-DESIGN-API", role="program_owner", organization_id="ORG-DESIGN-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            api_design = design()
            api_design["elements"][0]["id"] = "E-API-POST"
            body = {"organization_id": "ORG-DESIGN-API", "design": api_design}
            status, payload = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body=body, service=service)
            self.assertEqual(status, 201)
            design_id = payload["data"]["id"]
            source_element_id = payload["data"]["elements"][0]["id"]
            status, payload = handle_request(method="GET", path="/v1/playbook/designs/assets?organization_id=ORG-DESIGN-API&unit=defense", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertTrue(any(item["term"] == "cover_3" for item in payload["data"]["assets"]))
            status, payload = handle_request(method="GET", path="/v1/playbook/designs/assets?organization_id=ORG-DESIGN-API&unit=offense&context_formation=shotgun_trips&personnel=11&rule_profile=nfl", headers=coach, service=service)
            self.assertEqual(status, 200)
            post = next(item for item in payload["data"]["assets"] if item["term"] == "post")
            angle = next(item for item in payload["data"]["assets"] if item["term"] == "angle")
            self.assertTrue(post["compatibility"]["compatible"])
            self.assertFalse(angle["compatibility"]["compatible"])
            trips = next(item for item in payload["data"]["assets"] if item["term"] == "shotgun_trips")
            self.assertEqual(len(trips["alignment"]["slots"]), 11)
            status, templates = handle_request(method="GET", path="/v1/playbook/designs/templates?organization_id=ORG-DESIGN-API&unit=offense", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertTrue(any(item["id"] == "TPL-OFF-DAGGER-2X2" and item["assignments"] for item in templates["data"]["templates"]))
            status, custom_template = handle_request(method="POST", path="/v1/playbook/designs/templates", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "name":"API custom concept", "tags":["install"]}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(custom_template["data"]["scope"], "organization")
            status, selected_template = handle_request(method="POST", path="/v1/playbook/designs/templates", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "name":"API selected stencil", "element_ids":[source_element_id]}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(selected_template["data"]["capture_scope"], "selection")
            self.assertEqual(selected_template["data"]["source_element_ids"], [source_element_id])
            status, lineage = handle_request(method="GET", path=f"/v1/playbook/designs/templates/lineage-impact?organization_id=ORG-DESIGN-API&template_id={custom_template['data']['id']}", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertFalse(lineage["data"]["mutated"])
            status, proposal = handle_request(method="POST", path="/v1/playbook/designs/templates/lineage-proposal", headers=coach, body={"organization_id":"ORG-DESIGN-API", "template_id":custom_template["data"]["id"], "patches":[{"key":"A-01", "patch":{"type":"corner"}}]}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(proposal["data"]["status"], "pending_owner_approval")
            status, approved_proposal = handle_request(method="POST", path="/v1/playbook/designs/templates/lineage-proposal/approve", headers=owner, body={"organization_id":"ORG-DESIGN-API", "proposal_id":proposal["data"]["id"], "decision_ref":"DEC-LINEAGE-API-001"}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(approved_proposal["data"]["status"], "approved_and_applied")
            self.assertTrue(approved_proposal["data"]["mutated"])
            status, variant_batch = handle_request(method="POST", path="/v1/playbook/designs/variants", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "variants":[{"label":"Cover 3","patch":{"coverage":"cover_3"},"assignment_patches":[{"element_id":source_element_id,"patch":{"type":"corner"}}]},{"label":"Quarters","patch":{"coverage":"quarters"}}]}, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(variant_batch["data"]["count"], 2)
            self.assertTrue(all(item["parent_design_id"] == design_id for item in variant_batch["data"]["variants"]))
            self.assertEqual(next(item for item in variant_batch["data"]["variants"][0]["elements"] if item["id"] == source_element_id)["type"], "corner")
            status, _ = handle_request(method="POST", path="/v1/playbook/designs/request-review", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "decision_ref":"DEC-REVIEW-API"}, service=service)
            self.assertEqual(status, 200)
            status, _ = handle_request(method="POST", path="/v1/playbook/designs/comments", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "text":"Check the key."}, service=service)
            self.assertEqual(status, 201)
            status, _ = handle_request(method="POST", path="/v1/playbook/designs/branch", headers=coach, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "branch_id":"DESIGN-API-BRANCH"}, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="POST", path="/v1/playbook/designs/publish", headers=owner, body={"organization_id":"ORG-DESIGN-API", "design_id":design_id, "decision_ref":"DEC-PUBLISH-API"}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "published")
            status, payload = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/role-view?organization_id=ORG-DESIGN-API&role=WR", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "renderable")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_design_save_conflict_returns_server_snapshot_for_resolution(self):
        secret = "play-design-conflict-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-CONFLICT-API", role="coach_staff", organization_id="ORG-DESIGN-CONFLICT", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            first = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-CONFLICT", "design": design()}, service=service)
            self.assertEqual(first[0], 201)
            current = first[1]["data"]
            changed = design()
            changed["id"] = current["id"]
            changed["concept"] = "Changed by another coach"
            second = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-CONFLICT", "design":changed, "expected_revision":current["_revision"]}, service=service)
            self.assertEqual(second[0], 201)
            stale = design()
            stale["id"] = current["id"]
            stale["concept"] = "Stale local edit"
            conflict = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-CONFLICT", "design":stale, "expected_revision":current["_revision"]}, service=service)
            self.assertEqual(conflict[0], 409)
            self.assertEqual(conflict[1]["status"], "conflict")
            self.assertEqual(conflict[1]["data"]["code"], "DESIGN-CONFLICT")
            self.assertEqual(conflict[1]["data"]["server_design"]["concept"], "Changed by another coach")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_collaboration_presence_threads_replies_resolution_and_events(self):
        secret = "play-design-collab-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-COLLAB-API", role="coach_staff", organization_id="ORG-DESIGN-COLLAB", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-COLLAB", "design": design()}, service=service)
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            presence_status, _ = handle_request(method="POST", path="/v1/playbook/designs/presence", headers=coach, body={"organization_id":"ORG-DESIGN-COLLAB", "design_id":design_id, "session_id":"SESSION-COLLAB", "display_name":"Coach", "cursor":{"x":50,"y":20}}, service=service)
            self.assertEqual(presence_status, 200)
            presence_read_status, presence_read = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/presence?organization_id=ORG-DESIGN-COLLAB", headers=coach, service=service)
            self.assertEqual(presence_read_status, 200)
            self.assertEqual(presence_read["data"]["presence"][0]["session_id"], "SESSION-COLLAB")
            comment_status, comment = handle_request(method="POST", path="/v1/playbook/designs/comments", headers=coach, body={"organization_id":"ORG-DESIGN-COLLAB", "design_id":design_id, "text":"Confirm the safety key."}, service=service)
            self.assertEqual(comment_status, 201)
            reply_status, reply = handle_request(method="POST", path="/v1/playbook/designs/comments/reply", headers=coach, body={"organization_id":"ORG-DESIGN-COLLAB", "design_id":design_id, "comment_id":comment["data"]["id"], "text":"Install note added."}, service=service)
            self.assertEqual(reply_status, 201)
            resolve_status, _ = handle_request(method="POST", path="/v1/playbook/designs/comments/resolve", headers=coach, body={"organization_id":"ORG-DESIGN-COLLAB", "design_id":design_id, "comment_id":comment["data"]["id"], "resolved":True}, service=service)
            self.assertEqual(resolve_status, 200)
            comments_status, comments = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/comments?organization_id=ORG-DESIGN-COLLAB", headers=coach, service=service)
            self.assertEqual(comments_status, 200)
            self.assertEqual(len(comments["data"]["threads"]), 1)
            self.assertEqual(comments["data"]["threads"][0]["replies"][0]["id"], reply["data"]["id"])
            events_status, events = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/events?organization_id=ORG-DESIGN-COLLAB&since=0", headers=coach, service=service)
            self.assertEqual(events_status, 200)
            self.assertTrue(any(event["event_type"] == "comment_replied" for event in events["data"]["events"]))
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_version_history_diff_branch_merge_and_owner_rollback(self):
        secret = "play-design-versioning-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-VERSION-API", role="coach_staff", organization_id="ORG-DESIGN-VERSION", secret=secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-VERSION-API", role="program_owner", organization_id="ORG-DESIGN-VERSION", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-VERSION", "design":design()}, service=service)
            self.assertEqual(created_status, 201)
            current = created["data"]
            first_versions_status, first_versions = handle_request(method="GET", path=f"/v1/playbook/designs/{current['id']}/versions?organization_id=ORG-DESIGN-VERSION", headers=coach, service=service)
            self.assertEqual(first_versions_status, 200)
            first_snapshot = first_versions["data"]["snapshots"][0]["id"]

            changed = deepcopy(current)
            changed["elements"][0]["points"][1]["x"] = 48
            saved_status, saved = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-VERSION", "design":changed, "expected_revision":current["_revision"]}, service=service)
            self.assertEqual(saved_status, 201)
            current = saved["data"]
            history_status, history = handle_request(method="GET", path=f"/v1/playbook/designs/{current['id']}/versions?organization_id=ORG-DESIGN-VERSION", headers=coach, service=service)
            self.assertEqual(history_status, 200)
            self.assertGreaterEqual(len(history["data"]["snapshots"]), 2)
            compare_snapshot = history["data"]["snapshots"][-1]["id"]
            diff_status, diff = handle_request(method="GET", path=f"/v1/playbook/designs/{current['id']}/diff?organization_id=ORG-DESIGN-VERSION&base_snapshot_id={first_snapshot}&compare_snapshot_id={compare_snapshot}", headers=coach, service=service)
            self.assertEqual(diff_status, 200)
            self.assertTrue(diff["data"]["diff"]["elements"]["changed"])
            self.assertEqual(diff["data"]["base_design"]["id"], current["id"])
            self.assertEqual(diff["data"]["compare_design"]["id"], current["id"])

            branch_status, branch = handle_request(method="POST", path="/v1/playbook/designs/branch", headers=coach, body={"organization_id":"ORG-DESIGN-VERSION", "design_id":current["id"], "branch_id":"DESIGN-VERSION-BRANCH"}, service=service)
            self.assertEqual(branch_status, 201)
            branch_design = deepcopy(branch["data"])
            branch_design["elements"][0]["points"][0]["x"] = 16
            branch_save_status, branch_save = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-VERSION", "design":branch_design, "expected_revision":branch_design["_revision"]}, service=service)
            self.assertEqual(branch_save_status, 201)
            merge_status, merged = handle_request(method="POST", path="/v1/playbook/designs/versioning/merge", headers=coach, body={"organization_id":"ORG-DESIGN-VERSION", "design_id":current["id"], "branch_id":"DESIGN-VERSION-BRANCH", "expected_revision":current["_revision"]}, service=service)
            self.assertEqual(merge_status, 200)
            self.assertEqual(merged["data"]["status"], "merged")
            current = merged["data"]["design"]

            rollback_status, rollback = handle_request(method="POST", path="/v1/playbook/designs/versioning/rollback", headers=owner, body={"organization_id":"ORG-DESIGN-VERSION", "design_id":current["id"], "snapshot_id":first_snapshot, "decision_ref":"DEC-ROLLBACK-VERSION", "expected_revision":current["_revision"]}, service=service)
            self.assertEqual(rollback_status, 200)
            self.assertEqual(rollback["data"]["design"]["status"], "draft")
            self.assertEqual(rollback["data"]["design"]["rolled_back_from_snapshot_id"], first_snapshot)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_teaching_view_and_mastery_are_role_scoped(self):
        secret = "play-design-teaching-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-TEACHING-API", role="coach_staff", organization_id="ORG-DESIGN-TEACHING", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-TEACHING-API", role="player", organization_id="ORG-DESIGN-TEACHING", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            candidate = design()
            candidate["teaching"] = {"quizzes": [{"id": "QUIZ-API-1", "question": "Identify the read.", "options": ["Post", "Flat"], "answer": "Post"}]}
            candidate["elements"][0]["read_key"] = "Safety"
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-TEACHING", "design":candidate}, service=service)
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            view_status, view = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/teaching-view?organization_id=ORG-DESIGN-TEACHING&role=WR&mode=player&step=0", headers=player, service=service)
            self.assertEqual(view_status, 200)
            self.assertIn("accessible_text", view["data"])
            self.assertNotIn("answer", view["data"]["quizzes"][0])
            step_id = view["data"]["steps"][0]["id"]
            mastery_status, mastery = handle_request(method="POST", path="/v1/playbook/designs/mastery", headers=player, body={"organization_id":"ORG-DESIGN-TEACHING", "design_id":design_id, "role":"WR", "step_id":step_id, "score":0.95, "result":"passed"}, service=service)
            self.assertEqual(mastery_status, 201)
            self.assertEqual(mastery["data"]["user_id"], "PLAYER-TEACHING-API")
            quiz_status, quiz = handle_request(method="POST", path="/v1/playbook/designs/quiz", headers=player, body={"organization_id":"ORG-DESIGN-TEACHING", "design_id":design_id, "role":"WR", "quiz_id":"QUIZ-API-1", "answer":"Post"}, service=service)
            self.assertEqual(quiz_status, 201)
            self.assertTrue(quiz["data"]["correct"])
            summary_status, summary = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/mastery?organization_id=ORG-DESIGN-TEACHING&role=WR", headers=player, service=service)
            self.assertEqual(summary_status, 200)
            self.assertEqual(summary["data"]["summary"]["mastered_step_count"], 2)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_production_export_endpoint_returns_signed_by_hash_artifact(self):
        secret = "play-design-export-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-EXPORT-API", role="coach_staff", organization_id="ORG-DESIGN-EXPORT", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-EXPORT", "design":design()}, service=service)
            self.assertEqual(created_status, 201)
            export_status, export = handle_request(method="POST", path="/v1/playbook/designs/export", headers=coach, body={"organization_id":"ORG-DESIGN-EXPORT", "design_id":created["data"]["id"], "kind":"play_card", "format":"svg", "black_white":True, "branding":{"team_name":"Export Team"}}, service=service)
            self.assertEqual(export_status, 200)
            self.assertEqual(export["data"]["validation"]["status"], "valid")
            self.assertEqual(len(export["data"]["sha256"]), 64)
            self.assertEqual(len(export["data"]["signature"]), 64)
            self.assertEqual(export["data"]["signature_algorithm"], "HMAC-SHA256")
            self.assertEqual(export["data"]["source_manifest"][0]["design_id"], created["data"]["id"])
            self.assertIn("source_manifest_hash", export["data"]["signed_fields"])
            self.assertIn("#111827", __import__("base64").b64decode(export["data"]["content_base64"]).decode("utf-8"))
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_legality_report_and_owner_override_routes_are_role_scoped(self):
        secret = "play-design-legality-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-LEGALITY-API", role="coach_staff", organization_id="ORG-DESIGN-LEGALITY", secret=secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-LEGALITY-API", role="program_owner", organization_id="ORG-DESIGN-LEGALITY", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            candidate = design()
            candidate["route_collision_policy"] = "error"
            candidate["elements"].append({"id": "E-ROUTE-2", "kind": "route", "player_id": "P1", "type": "post", "points": [{"x": 10, "y": 30}, {"x": 30, "y": 5}], "arrow_style": "route"})
            created_status, created = handle_request(method="POST", path="/v1/playbook/designs", headers=coach, body={"organization_id":"ORG-DESIGN-LEGALITY", "design":candidate}, service=service)
            self.assertEqual(created_status, 201)
            design_id = created["data"]["id"]
            report_status, report = handle_request(method="GET", path=f"/v1/playbook/designs/{design_id}/legality?organization_id=ORG-DESIGN-LEGALITY", headers=coach, service=service)
            self.assertEqual(report_status, 200)
            self.assertEqual(report["data"]["status"], "invalid")
            request_status, request = handle_request(method="POST", path="/v1/playbook/designs/legality/override", headers=coach, body={"organization_id":"ORG-DESIGN-LEGALITY", "design_id":design_id, "issue_code":"LEGALITY-ROUTE-COLLISION", "rationale":"Intentional switch release documented for this install.", "decision_ref":"DEC-REQUEST-API", "evidence_refs":["film://clip/api-1"], "expires_at":"2099-01-01T00:00:00Z"}, service=service)
            self.assertEqual(request_status, 201)
            self.assertEqual(request["data"]["status"], "pending_owner_approval")
            denied_status, _ = handle_request(method="POST", path="/v1/playbook/designs/legality/override/approve", headers=coach, body={"organization_id":"ORG-DESIGN-LEGALITY", "design_id":design_id, "override_id":request["data"]["id"], "decision_ref":"DEC-NOT-OWNER"}, service=service)
            self.assertEqual(denied_status, 403)
            approve_status, approved = handle_request(method="POST", path="/v1/playbook/designs/legality/override/approve", headers=owner, body={"organization_id":"ORG-DESIGN-LEGALITY", "design_id":design_id, "override_id":request["data"]["id"], "decision_ref":"DEC-OWNER-API"}, service=service)
            self.assertEqual(approve_status, 200)
            self.assertEqual(approved["data"]["status"], "approved")
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
