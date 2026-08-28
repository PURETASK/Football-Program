import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.deployment_infrastructure import validate_deployment_infrastructure


class DeploymentInfrastructureTests(unittest.TestCase):
    def test_repository_dockerfile_matches_contract(self):
        root = Path(__file__).resolve().parents[1]
        result = validate_deployment_infrastructure(dockerfile_path=root / "Dockerfile", contract_path=root / "deployment" / "nfl-fidos-deployment.json")
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["image_build_performed"])
        self.assertFalse(result["production_implementation_allowed"])

    def test_missing_healthcheck_is_rejected(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            dockerfile = Path(directory) / "Dockerfile"
            text = (root / "Dockerfile").read_text(encoding="utf-8").replace("HEALTHCHECK", "# HEALTHCHECK", 1)
            dockerfile.write_text(text, encoding="utf-8")
            result = validate_deployment_infrastructure(dockerfile_path=dockerfile, contract_path=root / "deployment" / "nfl-fidos-deployment.json")
            self.assertEqual(result["status"], "invalid")
            self.assertTrue(any("healthcheck" in issue for issue in result["issues"]))
