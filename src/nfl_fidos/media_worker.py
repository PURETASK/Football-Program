"""Bounded media-worker primitives for probing authorized video assets."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from .media_ingestion import ALLOWED_EXTENSIONS
from .media_jobs import MediaProcessingJobService
from .media_transform import TRANSFORM_OPERATIONS, run_transform
from .tenant_repository import TenantRepository


ProbeRunner = Callable[[list[str]], tuple[int, str, str]]


def _configured_ffprobe(binary: str | None) -> str:
    return binary or os.environ.get("NFL_FIDOS_FFPROBE", "ffprobe")


def _default_runner(arguments: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=30, check=False)
        return result.returncode, result.stdout[:1_000_000], result.stderr[:16_000]
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def probe_media_file(*, file_path: str | Path, allowed_roots: list[str | Path] | None = None, ffprobe_binary: str | None = None, runner: ProbeRunner | None = None) -> dict[str, Any]:
    path = Path(file_path).resolve()
    issues: list[str] = []
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append("unsupported media extension")
    if not path.exists() or not path.is_file():
        issues.append("media file does not exist")
    roots = [Path(root).resolve() for root in (allowed_roots or [])]
    if roots and not any(path == root or root in path.parents for root in roots):
        issues.append("media file is outside an approved storage root")
    if issues:
        return {"status":"rejected", "path":str(path), "issues":issues}
    execute = runner or _default_runner
    code, stdout, stderr = execute([_configured_ffprobe(ffprobe_binary), "-v", "error", "-show_entries", "format=duration,format_name", "-of", "json", str(path)])
    if code == 127:
        return {"status":"metadata_only", "path":str(path), "file_name":path.name, "size_bytes":path.stat().st_size, "tool":"ffprobe", "tool_available":False, "issues":["ffprobe is unavailable; media is cataloged without decoded duration"]}
    if code != 0:
        return {"status":"failed", "path":str(path), "tool":"ffprobe", "tool_available":True, "issues":[stderr or "ffprobe failed"]}
    try:
        parsed = json.loads(stdout)
        format_data = parsed.get("format", {})
        duration = float(format_data["duration"]) if format_data.get("duration") is not None else None
        return {"status":"probed", "path":str(path), "file_name":path.name, "size_bytes":path.stat().st_size, "duration_seconds":duration, "format_name":format_data.get("format_name"), "tool":"ffprobe", "tool_available":True, "issues":[]}
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return {"status":"failed", "path":str(path), "tool":"ffprobe", "tool_available":True, "issues":[f"invalid ffprobe output: {exc}"]}


def index_media_file(*, file_path: str | Path, allowed_roots: list[str | Path] | None = None, ffprobe_binary: str | None = None, runner: ProbeRunner | None = None) -> dict[str, Any]:
    """Build a bounded, searchable media index from authorized stream metadata."""
    path = Path(file_path).resolve()
    issues: list[str] = []
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append("unsupported media extension")
    if not path.exists() or not path.is_file():
        issues.append("media file does not exist")
    roots = [Path(root).resolve() for root in (allowed_roots or [])]
    if roots and not any(path == root or root in path.parents for root in roots):
        issues.append("media file is outside an approved storage root")
    if issues:
        return {"status":"rejected", "operation":"index", "path":str(path), "issues":issues}
    execute = runner or _default_runner
    command = [
        _configured_ffprobe(ffprobe_binary),
        "-v", "error",
        "-show_entries", "format=duration,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,channels,sample_rate",
        "-of", "json",
        str(path),
    ]
    code, stdout, stderr = execute(command)
    if code == 127:
        return {"status":"metadata_only", "operation":"index", "path":str(path), "file_name":path.name, "size_bytes":path.stat().st_size, "stream_count":0, "streams":[], "tool":"ffprobe", "tool_available":False, "issues":["ffprobe is unavailable; media index is metadata-only"]}
    if code != 0:
        return {"status":"failed", "operation":"index", "path":str(path), "tool":"ffprobe", "tool_available":True, "issues":[stderr or "ffprobe index failed"]}
    try:
        parsed = json.loads(stdout)
        format_data = parsed.get("format", {}) if isinstance(parsed, dict) else {}
        streams = parsed.get("streams", []) if isinstance(parsed, dict) else []
        normalized_streams = [stream for stream in streams if isinstance(stream, dict)] if isinstance(streams, list) else []
        duration = float(format_data["duration"]) if format_data.get("duration") is not None else None
        return {
            "status":"indexed",
            "operation":"index",
            "path":str(path),
            "file_name":path.name,
            "size_bytes":path.stat().st_size,
            "duration_seconds":duration,
            "format_name":format_data.get("format_name"),
            "stream_count":len(normalized_streams),
            "streams":normalized_streams,
            "searchable_fields":["file_name", "format_name", "codec_type", "codec_name", "duration_seconds"],
            "tool":"ffprobe",
            "tool_available":True,
            "issues":[],
        }
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return {"status":"failed", "operation":"index", "path":str(path), "tool":"ffprobe", "tool_available":True, "issues":[f"invalid ffprobe index output: {exc}"]}


def process_media_job(*, repository: TenantRepository, job_id: str, worker_id: str, allowed_roots: list[str | Path] | None = None, runner: ProbeRunner | None = None) -> dict[str, Any]:
    jobs = MediaProcessingJobService(repository)
    job = jobs.claim_job(job_id=job_id, worker_id=worker_id)
    if job.get("status") != "running":
        return job
    payload = job.get("payload", {})
    roots = allowed_roots or payload.get("allowed_roots", [])
    if job.get("operation") == "probe":
        result = probe_media_file(file_path=payload.get("file_path", ""), allowed_roots=roots, runner=runner)
    elif job.get("operation") == "index":
        result = index_media_file(file_path=payload.get("file_path", ""), allowed_roots=roots, runner=runner)
    elif job.get("operation") in TRANSFORM_OPERATIONS:
        result = run_transform(operation=job["operation"], input_path=payload.get("file_path", ""), output_path=payload.get("output_path", ""), allowed_roots=roots, runner=runner, segment_seconds=payload.get("segment_seconds", 10))
    else:
        return jobs.fail_job(job_id=job_id, worker_id=worker_id, error_code="MEDIA-OPERATION-UNSUPPORTED", error_message="worker operation is not implemented")
    if result.get("status") in {"probed", "metadata_only", "indexed", "transformed"}:
        output_id = f"MEDIA-OUTPUT-{job_id.removeprefix('MEDIA-JOB-')}"
        repository.put("media_processing_outputs", output_id, {"id":output_id, "organization_id":repository.organization_id, "job_id":job_id, "result":result}, actor=worker_id, reason="media_probe_output_saved")
        return jobs.complete_job(job_id=job_id, worker_id=worker_id, output_refs=[output_id])
    return jobs.fail_job(job_id=job_id, worker_id=worker_id, error_code="MEDIA-PROBE-FAILED", error_message="; ".join(result.get("issues", ["media probe failed"])))
