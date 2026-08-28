"""Bounded queue runner for authorized media-processing jobs."""

from __future__ import annotations

from typing import Any

from .media_jobs import JOB_OPERATIONS
from .media_worker import ProbeRunner, process_media_job
from .tenant_repository import TenantRepository


MAX_BATCH_JOBS = 50


class MediaWorkerRunner:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def run_batch(self, *, worker_id: str, actor: str, allowed_roots: list[str], max_jobs: int = 10, runner: ProbeRunner | None = None) -> dict[str, Any]:
        issues: list[str] = []
        if not worker_id.startswith("MEDIA-WORKER-"):
            issues.append("worker_id must start with MEDIA-WORKER-")
        if not actor:
            issues.append("actor is required")
        if not allowed_roots:
            issues.append("at least one approved media root is required")
        if max_jobs <= 0 or max_jobs > MAX_BATCH_JOBS:
            issues.append(f"max_jobs must be between 1 and {MAX_BATCH_JOBS}")
        if issues:
            return {"id":f"MEDIA-WORKER-BATCH-REJECTED-{worker_id}", "organization_id":self.repository.organization_id, "worker_id":worker_id, "status":"rejected", "issues":issues, "selected_count":0, "completed_count":0, "failed_count":0, "results":[], "external_state_changed":False}
        eligible = [job for job in self.repository.list("media_processing_jobs") if job.get("status") in {"queued", "retryable"} and job.get("operation") in JOB_OPERATIONS]
        selected = eligible[:max_jobs]
        results: list[dict[str, Any]] = []
        for job in selected:
            try:
                result = process_media_job(repository=self.repository, job_id=job["id"], worker_id=worker_id, allowed_roots=allowed_roots, runner=runner)
                results.append({"job_id":job["id"], "status":result.get("status"), "output_refs":result.get("output_refs", []), "issues":result.get("issues", [])})
            except (OSError, TypeError, ValueError, KeyError) as exc:
                results.append({"job_id":job["id"], "status":"runner_error", "output_refs":[], "issues":[str(exc)]})
        completed = sum(item["status"] == "completed" for item in results)
        failed = sum(item["status"] in {"failed", "retryable", "runner_error"} for item in results)
        batch_id = f"MEDIA-WORKER-BATCH-{worker_id.removeprefix('MEDIA-WORKER-')}-{len(self.repository.list('media_worker_batches')) + 1:06d}"
        report = {"id":batch_id, "organization_id":self.repository.organization_id, "worker_id":worker_id, "actor":actor, "max_jobs":max_jobs, "selected_count":len(selected), "completed_count":completed, "failed_count":failed, "results":results, "status":"completed" if not failed else "partial_failure", "approved_roots":allowed_roots, "external_state_changed":False, "human_review_required":bool(failed)}
        return self.repository.put("media_worker_batches", batch_id, report, actor=actor, reason="media_worker_batch_reported")
