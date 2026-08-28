import tempfile
import unittest
from pathlib import Path

from nfl_fidos import JsonRepository, TenantRepository, build_organization_population_readiness
from nfl_fidos.organization_operating_bundle import COMPONENT_COLLECTIONS, REQUIRED_COMPONENTS


class OrganizationPopulationReadinessTests(unittest.TestCase):
    def test_empty_tenant_reports_every_required_component_without_fabrication(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-POPULATION", actor="OWNER")
            result = build_organization_population_readiness(tenant=tenant, organization_id="ORG-POPULATION", season="2026")
            self.assertEqual(result["status"], "population_incomplete")
            self.assertEqual(result["ready_component_count"], 0)
            self.assertEqual(result["required_component_count"], len(REQUIRED_COMPONENTS))
            self.assertEqual(len(result["blockers"]), len(REQUIRED_COMPONENTS))
            self.assertFalse(result["production_implementation_allowed"])

    def test_readiness_accepts_only_current_tenant_records_in_required_states(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-POPULATION", actor="OWNER")
            for name in REQUIRED_COMPONENTS:
                status = "active" if name == "organization_context" else "approved" if name == "terminology_bundle" else "validated"
                record = {"id": f"{name.upper()}-POPULATION", "organization_id": "ORG-POPULATION", "season": "2026", "status": status}
                if name == "organization_context":
                    record = {"id": "ORG-POPULATION", "organization_id": "ORG-POPULATION", "season": "2026", "status": status}
                tenant.put(COMPONENT_COLLECTIONS[name], record["id"], record, reason="population_readiness_fixture")
            result = build_organization_population_readiness(tenant=tenant, organization_id="ORG-POPULATION", season="2026")
            self.assertEqual(result["status"], "ready_for_bundle")
            self.assertEqual(result["ready_component_count"], len(REQUIRED_COMPONENTS))

    def test_cross_tenant_request_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-POPULATION", actor="OWNER")
            with self.assertRaises(PermissionError):
                build_organization_population_readiness(tenant=tenant, organization_id="ORG-OTHER", season="2026")


if __name__ == "__main__":
    unittest.main()
