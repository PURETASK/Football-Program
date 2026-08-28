"""Safe, bounded ffmpeg command planning for authorized media jobs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

from .media_ingestion import ALLOWED_EXTENSIONS


TransformRunner = Callable[[list[str]], tuple[int, str, str]]
TRANSFORM_OPERATIONS = {"transcode", "segment", "thumbnail"}


def _default_runner(arguments: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=300, check=False)
        return result.returncode, result.stdout[:1_000_000], result.stderr[:16_000]
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def _approved_path(value: str | Path, roots: list[str | Path]) -> Path:
    path = Path(value).resolve()
    approved = [Path(root).resolve() for root in roots]
    if not approved or not any(path == root or root in path.parents for root in approved):
        raise ValueError("path is outside approved media roots")
    return path


def build_transform_command(*, operation: str, input_path: str | Path, output_path: str | Path, allowed_roots: list[str | Path], ffmpeg_binary: str = "ffmpeg", segment_seconds: int = 10) -> tuple[list[str], Path, Path]:
    if operation not in TRANSFORM_OPERATIONS:
        raise ValueError("unsupported media transform operation")
    if segment_seconds <= 0 or segment_seconds > 3600:
        raise ValueError("segment_seconds must be between 1 and 3600")
    source = _approved_path(input_path, allowed_roots)
    output = _approved_path(output_path, allowed_roots)
    if not source.exists() or not source.is_file():
        raise ValueError("input media file does not exist")
    if source == output or output.exists():
        raise ValueError("output path must be new and different from input")
    if operation != "thumbnail" and output.suffix.lower() not in ALLOWED_EXTENSIONS and not output.name.endswith("%03d.ts"):
        raise ValueError("output format is not an approved media format")
    if operation == "transcode":
        command = [ffmpeg_binary, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", str(source), "-c:v", "libx264", "-c:a", "aac", str(output)]
    elif operation == "segment":
        command = [ffmpeg_binary, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", str(source), "-f", "segment", "-segment_time", str(segment_seconds), "-reset_timestamps", "1", str(output)]
    else:
        command = [ffmpeg_binary, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-i", str(source), "-frames:v", "1", str(output)]
    return command, source, output


def run_transform(*, operation: str, input_path: str | Path, output_path: str | Path, allowed_roots: list[str | Path], runner: TransformRunner | None = None, segment_seconds: int = 10) -> dict[str, Any]:
    try:
        command, source, output = build_transform_command(operation=operation, input_path=input_path, output_path=output_path, allowed_roots=allowed_roots, segment_seconds=segment_seconds)
    except (TypeError, ValueError) as exc:
        return {"status":"rejected", "operation":operation, "issues":[str(exc)]}
    execute = runner or _default_runner
    code, stdout, stderr = execute(command)
    if code == 127:
        return {"status":"failed", "operation":operation, "input_path":str(source), "output_path":str(output), "tool_available":False, "issues":["ffmpeg is unavailable"]}
    if code != 0:
        return {"status":"failed", "operation":operation, "input_path":str(source), "output_path":str(output), "tool_available":True, "issues":[stderr or "ffmpeg transform failed"]}
    return {"status":"transformed", "operation":operation, "input_path":str(source), "output_path":str(output), "tool_available":True, "stdout":stdout, "issues":[]}
