import unittest

from scripts.media_tool_smoke import run_smoke


class MediaToolSmokeTests(unittest.TestCase):
    def test_missing_external_tools_fail_closed_without_workspace_mutation(self):
        result = run_smoke(ffmpeg_binary="nfl-fidos-missing-ffmpeg", ffprobe_binary="nfl-fidos-missing-ffprobe")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["tool_available"])
        self.assertFalse(result["temporary_workspace"])


if __name__ == "__main__":
    unittest.main()
