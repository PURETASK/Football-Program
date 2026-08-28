import json
import unittest
from pathlib import Path

from nfl_fidos.agent_bible import validate_agent_bible


class AgentBibleTests(unittest.TestCase):
    def test_controlled_agent_bible_covers_registry_and_boundaries(self):
        root = Path(__file__).parents[1]
        bible = json.loads((root / "agents" / "agent-organization-bible.json").read_text(encoding="utf-8"))
        result = validate_agent_bible(bible)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["role_count"], 16)
        self.assertGreaterEqual(len(bible["handoff_matrix"]), 5)


if __name__ == "__main__":
    unittest.main()
