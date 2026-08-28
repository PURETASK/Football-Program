import tempfile
import unittest
from pathlib import Path

from nfl_fidos import AgentRegistry, AgentRuntime, JsonRepository, TenantRepository
from nfl_fidos.local_agent_adapters import register_local_validation_adapters


class LocalAgentAdapterTests(unittest.TestCase):
    def test_local_adapters_cover_declared_capabilities_without_auto_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-LOCAL-ADAPTER", actor="validator")
            runtime = AgentRuntime(repository, registry=AgentRegistry())
            bible = {"roles": [{"id": "AGT-007", "name": "Validator", "family": "validation", "authority": ["validate", "reject"]}]}
            result = register_local_validation_adapters(runtime, bible)
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["active_capabilities"], [])
            self.assertFalse(result["activation_performed"])
            pending = runtime.dispatch(run_id="RUN-LOCAL-001", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-LOCAL", payload={"secret_like":"do-not-return"})
            self.assertEqual(pending["status"], "blocked")

    def test_active_local_adapter_returns_value_free_rehearsal_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-LOCAL-ADAPTER", actor="validator")
            runtime = AgentRuntime(repository, registry=AgentRegistry())
            bible = {"roles": [{"id": "AGT-007", "name": "Validator", "family": "validation", "authority": ["validate"]}]}
            result = register_local_validation_adapters(runtime, bible, activate=True)
            self.assertEqual(result["active_capabilities"], ["AGT-007:validate"])
            completed = runtime.dispatch(run_id="RUN-LOCAL-002", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-LOCAL", payload={"secret_like":"do-not-return", "play_id":"PLAY-LOCAL"})
            self.assertEqual(completed["status"], "completed")
            output = completed["output"]
            self.assertEqual(output["status"], "local_validation_only")
            self.assertNotIn("do-not-return", output)
            self.assertFalse(output["external_provider_called"])
            self.assertFalse(output["canonical_write_performed"])
            self.assertFalse(output["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()
