import tempfile
import unittest
from pathlib import Path

from nfl_fidos import AgentRegistry, AgentRuntime, JsonRepository, TenantRepository, load_agent_bible


class AgentRuntimeTests(unittest.TestCase):
    def test_runtime_activates_dispatches_and_persists_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-AGENT", actor="coach")
            runtime = AgentRuntime(repository, registry=AgentRegistry())
            runtime.register_bible({"roles":[{"id":"AGT-007", "name":"Validator", "family":"validation", "authority":["validate"]}]})
            runtime.activate(agent_id="AGT-007", capability="validate")
            runtime.register_adapter(agent_id="AGT-007", capability="validate", adapter=lambda payload, context: {"valid": True, "play_id": payload["play_id"], "organization_id": context["organization_id"]})
            result = runtime.dispatch(run_id="RUN-001", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-001", payload={"play_id":"PLAY-001"})
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["handoff"]["status"], "ready")
            self.assertEqual(repository.get("agent_runs", "RUN-001")["output"]["valid"], True)

    def test_inactive_agent_blocks_and_missing_adapter_never_executes(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-AGENT", actor="coach")
            runtime = AgentRuntime(repository, registry=AgentRegistry())
            runtime.register_bible({"roles":[{"id":"AGT-009", "name":"Film", "family":"film", "authority":["tag"]}]})
            blocked = runtime.dispatch(run_id="RUN-002", from_agent="AGT-001", family="film", capability="tag", workflow_id="WF-002", payload={"clip_id":"CLIP-001"})
            self.assertEqual(blocked["status"], "blocked")
            runtime.activate(agent_id="AGT-009", capability="tag")
            pending = runtime.dispatch(run_id="RUN-003", from_agent="AGT-001", family="film", capability="tag", workflow_id="WF-002", payload={"clip_id":"CLIP-001"})
            self.assertEqual(pending["status"], "awaiting_adapter")
            self.assertTrue(pending["human_review_required"])

    def test_controlled_agent_bible_loads(self):
        path = Path(__file__).parents[1] / "agents" / "agent-organization-bible.json"
        bible = load_agent_bible(path)
        self.assertEqual(bible["scope"], "NFL football only")
        self.assertEqual(len(bible["roles"]), 16)


if __name__ == "__main__":
    unittest.main()
