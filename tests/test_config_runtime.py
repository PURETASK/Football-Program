import unittest
from pathlib import Path

from nfl_fidos.config import load_config


class RuntimeConfigTests(unittest.TestCase):
    def test_local_config_is_validated_and_resolved(self):
        config = load_config(environ={"NFL_FIDOS_ENV":"local", "NFL_FIDOS_PORT":"9000", "NFL_FIDOS_AUTH_SECRET":"local-secret", "NFL_FIDOS_DATABASE":".runtime/test.db"})
        self.assertEqual(config.port, 9000)
        self.assertIsInstance(config.database_path, Path)
        self.assertEqual(config.ffmpeg_binary, "ffmpeg")
        self.assertEqual(config.ffprobe_binary, "ffprobe")

    def test_production_requires_strong_secret(self):
        with self.assertRaises(ValueError):
            load_config(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"short"})
        config = load_config(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32})
        self.assertEqual(config.environment, "production")

    def test_missing_secret_is_rejected_by_default(self):
        with self.assertRaises(ValueError):
            load_config(environ={"NFL_FIDOS_ENV":"validation"})


if __name__ == "__main__":
    unittest.main()
