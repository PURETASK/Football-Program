import json
import unittest
from pathlib import Path

from nfl_fidos.player_development_bible import validate_player_development_bible


class PlayerDevelopmentBibleTests(unittest.TestCase):
    def test_position_coverage_and_learning_controls(self):
        root = Path(__file__).parents[1]
        bible = json.loads((root / "development" / "player-development-bible.json").read_text(encoding="utf-8"))
        result = validate_player_development_bible(bible)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["position_count"], 12)
        self.assertGreaterEqual(result["role_count"], 20)


if __name__ == "__main__":
    unittest.main()
