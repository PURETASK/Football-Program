import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request, issue_token
from nfl_fidos.organization_operating_bundle import COMPONENT_COLLECTIONS, REQUIRED_COMPONENTS
from nfl_fidos.tenant_repository import TenantRepository


class OrganizationOperatingBundleAPITests(unittest.TestCase):
    def setUp(self):
        self.secret = "organization-operating-bundle-secret-0123456789"
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-BUNDLE", role="program_owner", organization_id="ORG-BUNDLE-API", secret=self.secret)}
        self.coach = {"Authorization": "Bearer " + issue_token(subject="COACH-BUNDLE", role="coach_staff", organization_id="ORG-BUNDLE-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def components(self):
        output = {}
        for name in REQUIRED_COMPONENTS:
            if name == "organization_context":
                output[name] = {"id": "ORG-BUNDLE-API", "season": "2026", "status": "active"}
            else:
                status = "approved" if name == "terminology_bundle" else "validated"
                output[name] = {"id": f"{name.upper()}-API", "organization_id": "ORG-BUNDLE-API", "season": "2026", "status": status}
        return output

    def test_owner_can_submit_approve_and_read_bundle(self):
        body = {"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-API-2026", "season": "2026", "components": self.components()}
        status, response = handle_request(method="POST", path="/v1/organizations/operating-bundle", headers=self.owner, body=body, service=self.service)
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["status"], "ready_for_owner_review")
        status, response = handle_request(method="POST", path="/v1/organizations/operating-bundle/approve", headers=self.owner, body={"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-API-2026", "decision_ref": "DEC-BUNDLE-API-001"}, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "approved_for_non_production")
        self.assertFalse(response["data"]["production_implementation_allowed"])
        status, response = handle_request(method="GET", path="/v1/organizations/operating-bundle?organization_id=ORG-BUNDLE-API", headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["bundles"]), 1)

    def test_coach_cannot_submit_or_approve_bundle(self):
        body = {"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-API-2026", "season": "2026", "components": self.components()}
        status, _ = handle_request(method="POST", path="/v1/organizations/operating-bundle", headers=self.coach, body=body, service=self.service)
        self.assertEqual(status, 403)

    def test_owner_can_compose_from_persisted_component_ids(self):
        tenant = TenantRepository(self.service.repository, organization_id="ORG-BUNDLE-API", actor="OWNER-BUNDLE")
        components = self.components()
        component_ids = {}
        for name, record in components.items():
            record["organization_id"] = "ORG-BUNDLE-API"
            tenant.put(COMPONENT_COLLECTIONS[name], record["id"], record, reason="test_persisted_component")
            component_ids[name] = record["id"]
        body = {"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-PERSISTED-2026", "season": "2026", "component_ids": component_ids}
        status, response = handle_request(method="POST", path="/v1/organizations/operating-bundle", headers=self.owner, body=body, service=self.service)
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["status"], "ready_for_owner_review")

    def test_missing_component_source_fails_closed(self):
        body = {"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-MISSING-2026", "season": "2026", "component_ids": {"organization_context": "MISSING-CONTEXT"}}
        status, response = handle_request(method="POST", path="/v1/organizations/operating-bundle", headers=self.owner, body=body, service=self.service)
        self.assertEqual(status, 422)
        self.assertEqual(response["status"], "blocked")
        status, _ = handle_request(method="POST", path="/v1/organizations/operating-bundle/approve", headers=self.coach, body={"organization_id": "ORG-BUNDLE-API", "bundle_id": "ORG-BUNDLE-API-2026", "decision_ref": "DEC-BUNDLE-API-001"}, service=self.service)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
