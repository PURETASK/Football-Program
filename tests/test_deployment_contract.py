import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.deployment_contract import validate_deployment_contract


class DeploymentContractTests(unittest.TestCase):
    def test_controlled_deployment_contract_is_valid_and_design_only(self):
        root = Path(__file__).resolve().parents[1]
        result = validate_deployment_contract(path=root / "deployment" / "nfl-fidos-deployment.json")
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["production_implementation_allowed"])
        self.assertEqual(result["service_count"], 3)

    def test_missing_service_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deployment.json"
            path.write_text(json.dumps({"deployment_id":"DEPLOY-TEST", "scope":"NFL only", "status":"design_only", "production_implementation_allowed":False, "services":[], "storage":[{}], "secrets":[{}]}), encoding="utf-8")
            result = validate_deployment_contract(path=path)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("SERVICE-API" in issue for issue in result["issues"]))

    def test_operational_controls_are_required(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads((root / "deployment" / "nfl-fidos-deployment.json").read_text(encoding="utf-8"))
        contract["rollout"].pop("rollback")
        path = root / ".runtime" / "invalid-deployment-contract-test.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
        try:
            result = validate_deployment_contract(path=path)
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("rollback" in issue for issue in result["issues"]))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
