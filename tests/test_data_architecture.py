import json
import unittest
from pathlib import Path

from nfl_fidos.data_architecture import validate_data_architecture, validate_record_tenancy


class DataArchitectureTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "data" / "data-architecture.json"
        self.architecture = json.loads(path.read_text(encoding="utf-8"))

    def test_data_architecture_has_authoritative_entities_and_relationships(self):
        result = validate_data_architecture(self.architecture)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["entity_count"], 18)
        self.assertGreaterEqual(result["relationship_count"], 10)

    def test_tenancy_denies_cross_organization_access_by_default(self):
        denied = validate_record_tenancy(record={"organization_id":"ORG-1"}, requester_organization="ORG-2")
        self.assertFalse(denied["allowed"])
        allowed = validate_record_tenancy(record={"organization_id":"ORG-1"}, requester_organization="ORG-2", cross_organization_scope=True)
        self.assertTrue(allowed["allowed"])
        self.assertTrue(allowed["audit_required"])

    def test_unknown_relationship_endpoint_is_rejected(self):
        architecture = json.loads(json.dumps(self.architecture))
        architecture["relationships"][0]["to"] = "ENTITY-MISSING"
        self.assertEqual(validate_data_architecture(architecture)["status"], "invalid")
