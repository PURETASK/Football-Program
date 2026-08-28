import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_transform import build_transform_command, run_transform


class MediaTransformTests(unittest.TestCase):
    def test_commands_are_bounded_and_non_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            output = Path(directory) / "output.mp4"
            source.write_bytes(b"source")
            command, _, _ = build_transform_command(operation="transcode", input_path=source, output_path=output, allowed_roots=[directory])
            self.assertEqual(command[0], "ffmpeg")
            self.assertIn("-nostdin", command)
            self.assertIn("-n", command)
            self.assertNotIn("shell", command)
            result = run_transform(operation="thumbnail", input_path=source, output_path=Path(directory) / "thumb.jpg", allowed_roots=[directory], runner=lambda arguments: (0, "", ""))
            self.assertEqual(result["status"], "transformed")

    def test_missing_tool_and_path_escape_are_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            source.write_bytes(b"source")
            missing = run_transform(operation="transcode", input_path=source, output_path=Path(directory) / "output.mp4", allowed_roots=[directory], runner=lambda arguments: (127, "", "not found"))
            self.assertFalse(missing["tool_available"])
            escaped = run_transform(operation="transcode", input_path=source, output_path=Path(directory).parent / "output.mp4", allowed_roots=[directory], runner=lambda arguments: (_ for _ in ()).throw(AssertionError("runner must not execute")))
            self.assertEqual(escaped["status"], "rejected")

    def test_segment_duration_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mp4"
            source.write_bytes(b"source")
            with self.assertRaises(ValueError):
                build_transform_command(operation="segment", input_path=source, output_path=Path(directory) / "part%03d.ts", allowed_roots=[directory], segment_seconds=0)


if __name__ == "__main__":
    unittest.main()
