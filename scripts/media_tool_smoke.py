"""Run a bounded real FFmpeg/FFprobe rehearsal on temporary synthetic media."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from nfl_fidos.media_transform import run_transform
from nfl_fidos.media_worker import probe_media_file


def _run(arguments: list[str], *, timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode, result.stdout[:10000], result.stderr[:10000]
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def run_smoke(*, ffmpeg_binary: str = "ffmpeg", ffprobe_binary: str = "ffprobe") -> dict[str, Any]:
    ffmpeg_path, ffprobe_path = shutil.which(ffmpeg_binary), shutil.which(ffprobe_binary)
    if not ffmpeg_path or not ffprobe_path:
        return {"status":"blocked", "tool_available":False, "ffmpeg":ffmpeg_path, "ffprobe":ffprobe_path, "temporary_workspace":False, "issues":["ffmpeg and ffprobe must both be discoverable"]}
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-media-tools-") as directory:
        root = Path(directory)
        source = root / "source.mp4"
        transcoded = root / "transcoded.mp4"
        thumbnail = root / "thumbnail.jpg"
        segments = root / "segment-%03d.ts"
        code, _, stderr = _run([ffmpeg_path, "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-shortest", "-pix_fmt", "yuv420p", str(source)])
        if code != 0:
            return {"status":"failed", "tool_available":True, "temporary_workspace":True, "checks":{"fixture_generation":False}, "issues":[stderr or "fixture generation failed"]}
        probe = probe_media_file(file_path=source, allowed_roots=[root], ffprobe_binary=ffprobe_path, runner=_run)
        def ffmpeg_runner(arguments: list[str]) -> tuple[int, str, str]:
            rewritten = [ffmpeg_path if item == "ffmpeg" else item for item in arguments]
            return _run(rewritten, timeout=60)
        transcode = run_transform(operation="transcode", input_path=source, output_path=transcoded, allowed_roots=[root], runner=ffmpeg_runner)
        thumb = run_transform(operation="thumbnail", input_path=source, output_path=thumbnail, allowed_roots=[root], runner=ffmpeg_runner)
        segment = run_transform(operation="segment", input_path=source, output_path=segments, allowed_roots=[root], runner=ffmpeg_runner, segment_seconds=1)
        checks = {"fixture_generation":source.exists(), "probe":probe.get("status") == "probed", "transcode":transcode.get("status") == "transformed" and transcoded.exists(), "thumbnail":thumb.get("status") == "transformed" and thumbnail.exists(), "segment":segment.get("status") == "transformed" and any(root.glob("segment-*.ts"))}
        return {"status":"passed" if all(checks.values()) else "failed", "tool_available":True, "temporary_workspace":True, "checks":checks, "probe":{key:probe.get(key) for key in ("status", "duration_seconds", "format_name", "tool_available")}, "issues":[] if all(checks.values()) else ["one or more media tool checks failed"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args(argv)
    result = run_smoke(ffmpeg_binary=args.ffmpeg, ffprobe_binary=args.ffprobe)
    import json
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
