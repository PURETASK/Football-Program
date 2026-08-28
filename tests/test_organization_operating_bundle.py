import unittest
import tempfile
from pathlib import Path

from nfl_fidos.organization_operating_bundle import (
    COMPONENT_COLLECTIONS,
    REQUIRED_COMPONENTS,
    approve_organization_operating_bundle,
    build_organization_operating_bundle,
    load_persisted_organization_components,
)
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


def component(name: str) -> dict:
    status = "active" if name == "organization_context" else "approved" if name == "terminology_bundle" else "validated"
    if name == "organization_context":
        return {"id": "ORG-SYNTH", "season": "2026", "status": status}
    return {"id": f"{name.upper()}-SYNTH", "organization_id": "ORG-SYNTH", "season": "2026", "status": status}


class OrganizationOperatingBundleTests(unittest.TestCase):
    def valid_components(self):
        return {name: component(name) for name in REQUIRED_COMPONENTS}

    def test_composes_all_required_components_for_owner_review(self):
        result = build_organization_operating_bundle(
            bundle_id="ORG-BUNDLE-SYNTH-2026", organization_id="ORG-SYNTH", season="2026", components=self.valid_components()
        )
        self.assertEqual(result["status"], "ready_for_owner_review")
        self.assertEqual(set(result["component_refs"]), set(REQUIRED_COMPONENTS))
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["activation_performed"])

    def test_missing_or_unvalidated_component_blocks(self):
        components = self.valid_components()
        components.pop("analytics")
        components["media_review"]["organization_id"] = "ORG-OTHER"
        result = build_organization_operating_bundle(
            bundle_id="ORG-BUNDLE-SYNTH-2026", organization_id="ORG-SYNTH", season="2026", components=components
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any(issue["code"] == "BUNDLE-MISSING" for issue in result["issues"]))
        self.assertTrue(any(issue["code"] == "BUNDLE-SCOPE" for issue in result["issues"]))

    def test_owner_approval_remains_non_activating(self):
        bundle = build_organization_operating_bundle(
            bundle_id="ORG-BUNDLE-SYNTH-2026", organization_id="ORG-SYNTH", season="2026", components=self.valid_components()
        )
        approved = approve_organization_operating_bundle(
            bundle=bundle, approver="owner-1", approver_role="program_owner", decision_ref="DEC-ORG-BUNDLE-001"
        )
        self.assertEqual(approved["status"], "approved_for_non_production")
        self.assertFalse(approved["production_implementation_allowed"])
        self.assertFalse(approved["activation_performed"])
        self.assertFalse(approved["stage_advance_authorized"])

    def test_non_owner_cannot_approve(self):
        bundle = build_organization_operating_bundle(
            bundle_id="ORG-BUNDLE-SYNTH-2026", organization_id="ORG-SYNTH", season="2026", components=self.valid_components()
        )
        result = approve_organization_operating_bundle(
            bundle=bundle, approver="coach-1", approver_role="coach_staff", decision_ref="DEC-ORG-BUNDLE-001"
        )
        self.assertEqual(result["status"], "rejected")

    def test_persisted_component_resolution_is_tenant_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(repository, organization_id="ORG-SYNTH", actor="OWNER-1")
            for name in REQUIRED_COMPONENTS:
                record = component(name)
                record["organization_id"] = "ORG-SYNTH"
                tenant.put(COMPONENT_COLLECTIONS[name], record["id"], record, reason="test_component_seed")
            resolved = load_persisted_organization_components(tenant)
            self.assertEqual(set(resolved), set(REQUIRED_COMPONENTS))
            missing = load_persisted_organization_components(tenant, {"analytics": "ANALYTICS-NOT-PRESENT"})
            self.assertNotIn("analytics", missing)


if __name__ == "__main__":
    unittest.main()
