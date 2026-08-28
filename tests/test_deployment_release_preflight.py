import unittest

from nfl_fidos.deployment_release_preflight import compose_deployment_release_preflight


class DeploymentReleasePreflightTests(unittest.TestCase):
    def test_coherent_validation_evidence_is_ready_without_activation(self):
        result = compose_deployment_release_preflight(
            release_validation={"artifact_status":"complete", "deployment_status":"valid", "production_implementation_allowed":False},
            deployment_preflight={"status":"ready", "environment":"validation"},
            operational_readiness={"status":"ready"},
            eval_result={"status":"passed", "passed":97, "failed":0},
        )
        self.assertEqual(result["status"], "ready_for_validation")
        self.assertFalse(result["activation_performed"])
        self.assertFalse(result["production_implementation_allowed"])
        self.assertFalse(result["external_state_changed"])

    def test_incomplete_operations_or_invalid_artifacts_block(self):
        result = compose_deployment_release_preflight(
            release_validation={"artifact_status":"complete", "deployment_status":"valid", "production_implementation_allowed":False},
            deployment_preflight={"status":"blocked", "environment":"production"},
            operational_readiness={"status":"blocked"},
            eval_result={"status":"passed"},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("deployment_preflight", result["blockers"])
        self.assertIn("operational_readiness", result["blockers"])


if __name__ == "__main__":
    unittest.main()
