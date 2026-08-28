"""Bounded repository-backed orchestration for authorized media transform jobs."""

from __future__ import annotations

from typing import Any, Callable

from .media_jobs import MediaProcessingJobService, SCHEDULED_MEDIA_OPERATIONS
from .media_worker import ProbeRunner, process_media_job
from .tenant_repository import TenantRepository


class MediaTransformOrchestrator:
    def __init__(self, repository: TenantRepository):
        self.repository = repository
        self.jobs = MediaProcessingJobService(repository)

    def run_batch(self, *, actor: str, worker_id: str, max_jobs: int = 10, allowed_roots: list[str] | None = None, runner: ProbeRunner | None = None) -> dict[str, Any]:
        if max_jobs <= 0:
            raise ValueError("max_jobs must be positive")
        eligible = [job for job in self.jobs.list_jobs() if job.get("status") in {"queued", "retryable"} and job.get("operation") in SCHEDULED_MEDIA_OPERATIONS]
        selected = eligible[:max_jobs]
        results: list[dict[str, Any]] = []
        for job in selected:
            result = process_media_job(repository=self.repository, job_id=job["id"], worker_id=worker_id, allowed_roots=allowed_roots, runner=runner)
            results.append({"job_id":job["id"], "status":result.get("status"), "output_refs":result.get("output_refs", []), "issues":result.get("issues", [])})
        completed = sum(result["status"] == "completed" for result in results)
        failed = sum(result["status"] in {"failed", "retryable"} for result in results)
        batch_id = f"MEDIA-TRANSFORM-BATCH-{worker_id}-{len(self.repository.list('media_transform_batches')) + 1:06d}"
        report = {"id":batch_id, "organization_id":self.repository.organization_id, "actor":actor, "worker_id":worker_id, "max_jobs":max_jobs, "selected_count":len(selected), "completed_count":completed, "failed_count":failed, "results":results, "status":"completed" if not failed else "partial_failure", "destructive_action_required":False}
        self.repository.put("media_transform_batches", batch_id, report, actor=actor, reason="media_transform_batch_persisted")
        return report
