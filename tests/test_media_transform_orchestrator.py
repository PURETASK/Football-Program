import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.media_transform_orchestrator import MediaTransformOrchestrator
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class MediaTransformOrchestratorTests(unittest.TestCase):
    def test_batch_is_bounded_persisted_and_completes_transform_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            source.write_bytes(b"video")
            repository = TenantRepository(JsonRepository(root / "state.json"), organization_id="ORG-TRANSFORM", actor="ANALYST")
            jobs = MediaProcessingJobService(repository)
            for index in range(2):
                jobs.create_job(job_id=f"MEDIA-JOB-TRANSFORM-{index}", asset_id=f"FILM-{index}", operation="thumbnail", payload={"file_path":str(source), "output_path":str(root / f"thumb-{index}.jpg"), "allowed_roots":[str(root)]}, requested_by="ANALYST")
            report = MediaTransformOrchestrator(repository).run_batch(actor="ANALYST", worker_id="WORKER-1", max_jobs=1, allowed_roots=[str(root)], runner=lambda arguments: (0, "", ""))
            self.assertEqual(report["selected_count"], 1)
            self.assertEqual(report["completed_count"], 1)
            self.assertFalse(report["destructive_action_required"])
            self.assertEqual(len(repository.list("media_transform_batches")), 1)
            self.assertEqual(len(jobs.list_jobs(status="queued")), 1)

    def test_invalid_job_is_reported_without_unbounded_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-TRANSFORM", actor="ANALYST")
            MediaProcessingJobService(repository).create_job(job_id="MEDIA-JOB-INVALID", asset_id="FILM-INVALID", operation="transcode", payload={"file_path":"missing.mp4", "output_path":"out.mp4", "allowed_roots":[directory]}, requested_by="ANALYST")
            report = MediaTransformOrchestrator(repository).run_batch(actor="ANALYST", worker_id="WORKER-1", max_jobs=1, allowed_roots=[directory], runner=lambda arguments: (_ for _ in ()).throw(AssertionError("runner must not execute")))
            self.assertEqual(report["failed_count"], 1)
            self.assertEqual(report["status"], "partial_failure")


if __name__ == "__main__":
    unittest.main()
