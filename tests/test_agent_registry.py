import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import AgentRegistry


class AgentRegistryTests(unittest.TestCase):
    def registry(self):
        registry = AgentRegistry()
        registry.register(agent_id="AGT-100", name="Film specialist", family="film", capabilities=["tag", "cite"], permissions=["read_film"])
        return registry

    def test_agent_is_callable_but_not_active_after_registration(self):
        registry = self.registry()
        self.assertEqual(registry.resolve(family="film", capability="tag", active_only=True), [])
        self.assertEqual(registry.resolve(family="film", capability="tag")[0]["lifecycle"], "callable")

    def test_activation_requires_declared_capability(self):
        registry = self.registry()
        active = registry.activate("AGT-100", requested_capability="tag")
        self.assertEqual(active["status"], "active")
        self.assertEqual(registry.active_ids(), ["AGT-100"])
        rejected = registry.activate("AGT-100", requested_capability="recommend")
        self.assertEqual(rejected["code"], "AGENT-CAPABILITY")

    def test_deactivation_removes_agent_from_active_resolution(self):
        registry = self.registry()
        registry.activate("AGT-100", requested_capability="cite")
        result = registry.deactivate("AGT-100")
        self.assertEqual(result["status"], "deactivated")
        self.assertEqual(registry.resolve(family="film", capability="cite", active_only=True), [])

    def test_duplicate_or_invalid_agents_are_rejected(self):
        registry = self.registry()
        duplicate = registry.register(agent_id="AGT-100", name="Other", family="film", capabilities=["tag"], permissions=[])
        self.assertEqual(duplicate["status"], "invalid")
        invalid = registry.register(agent_id="BAD", name="", family="", capabilities=[], permissions=[])
        self.assertEqual(invalid["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
