"""Durable, organization-scoped media processing job lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


JOB_OPERATIONS = {"probe", "transcode", "segment", "thumbnail", "index"}
SCHEDULED_MEDIA_OPERATIONS = {"transcode", "segment", "thumbnail", "index"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MediaProcessingJobService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_job(self, *, job_id: str, asset_id: str, operation: str, payload: dict[str, Any], requested_by: str, max_attempts: int = 3) -> dict[str, Any]:
        issues: list[str] = []
        if not job_id.startswith("MEDIA-JOB-"):
            issues.append("job id must start with MEDIA-JOB-")
        if not asset_id.startswith("FILM-"):
            issues.append("asset id must start with FILM-")
        if operation not in JOB_OPERATIONS:
            issues.append("unsupported media operation")
        if not requested_by or max_attempts <= 0:
            issues.append("requester and positive max_attempts are required")
        job = {
            "id": job_id, "organization_id": self.repository.organization_id, "asset_id": asset_id,
            "operation": operation, "payload": payload, "requested_by": requested_by,
            "status": "queued" if not issues else "invalid", "attempt": 0, "max_attempts": max_attempts,
            "created_at": _now(), "updated_at": _now(), "issues": issues,
        }
        if job["status"] == "queued":
            return self.repository.put("media_processing_jobs", job_id, job, actor=requested_by, reason="media_processing_job_created")
        return job

    def claim_job(self, *, job_id: str, worker_id: str) -> dict[str, Any]:
        job = self.repository.get("media_processing_jobs", job_id)
        if job is None:
            raise KeyError(f"Unknown media job: {job_id}")
        if job["status"] not in {"queued", "retryable"}:
            job["issues"] = list(job.get("issues", [])) + ["job is not claimable in current state"]
            return job
        job.update({"status": "running", "worker_id": worker_id, "attempt": job.get("attempt", 0) + 1, "started_at": _now(), "updated_at": _now()})
        return self.repository.put("media_processing_jobs", job_id, job, actor=worker_id, reason="media_processing_job_claimed")

    def complete_job(self, *, job_id: str, worker_id: str, output_refs: list[str]) -> dict[str, Any]:
        job = self.repository.get("media_processing_jobs", job_id)
        if job is None:
            raise KeyError(f"Unknown media job: {job_id}")
        if job["status"] != "running" or job.get("worker_id") != worker_id:
            job["issues"] = list(job.get("issues", [])) + ["only the active worker can complete a running job"]
            return job
        job.update({"status": "completed", "output_refs": output_refs, "completed_at": _now(), "updated_at": _now()})
        return self.repository.put("media_processing_jobs", job_id, job, actor=worker_id, reason="media_processing_job_completed")

    def fail_job(self, *, job_id: str, worker_id: str, error_code: str, error_message: str) -> dict[str, Any]:
        job = self.repository.get("media_processing_jobs", job_id)
        if job is None:
            raise KeyError(f"Unknown media job: {job_id}")
        if job["status"] != "running" or job.get("worker_id") != worker_id:
            job["issues"] = list(job.get("issues", [])) + ["only the active worker can fail a running job"]
            return job
        terminal = job.get("attempt", 0) >= job.get("max_attempts", 1)
        job.update({"status": "failed" if terminal else "retryable", "last_error":{"code":error_code, "message":error_message}, "updated_at":_now()})
        return self.repository.put("media_processing_jobs", job_id, job, actor=worker_id, reason="media_processing_job_failed")

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.repository.get("media_processing_jobs", job_id)

    def list_jobs(self, *, status: str | None = None) -> list[dict[str, Any]]:
        jobs = self.repository.list("media_processing_jobs")
        return [job for job in jobs if not status or job.get("status") == status]
