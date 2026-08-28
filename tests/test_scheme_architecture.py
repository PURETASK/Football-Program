import json
import unittest
from pathlib import Path

from nfl_fidos.scheme_architecture import validate_scheme_architecture


class SchemeArchitectureTests(unittest.TestCase):
    def test_offense_and_defense_are_compositional(self):
        root = Path(__file__).parents[1]
        architecture = json.loads((root / "scheme" / "scheme-architecture.json").read_text(encoding="utf-8"))
        result = validate_scheme_architecture(architecture)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(len(architecture["offense"]["concept_graph"]), 5)
        self.assertGreaterEqual(len(architecture["defense"]["counter_library"]), 2)


if __name__ == "__main__":
    unittest.main()
