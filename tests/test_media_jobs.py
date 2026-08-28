import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class MediaProcessingJobTests(unittest.TestCase):
    def test_job_claim_completion_and_retry_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            service = MediaProcessingJobService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-JOB", actor="ANALYST-1"))
            job = service.create_job(job_id="MEDIA-JOB-001", asset_id="FILM-JOB-001", operation="probe", payload={"uri":"file:///game.mp4"}, requested_by="ANALYST-1", max_attempts=2)
            self.assertEqual(job["status"], "queued")
            running = service.claim_job(job_id="MEDIA-JOB-001", worker_id="WORKER-1")
            self.assertEqual(running["status"], "running")
            retryable = service.fail_job(job_id="MEDIA-JOB-001", worker_id="WORKER-1", error_code="PROBE_TIMEOUT", error_message="probe timed out")
            self.assertEqual(retryable["status"], "retryable")
            service.claim_job(job_id="MEDIA-JOB-001", worker_id="WORKER-2")
            completed = service.complete_job(job_id="MEDIA-JOB-001", worker_id="WORKER-2", output_refs=["MEDIA-META-001"])
            self.assertEqual(completed["status"], "completed")

    def test_exhausted_attempts_become_terminal_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            service = MediaProcessingJobService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-JOB", actor="ANALYST-1"))
            service.create_job(job_id="MEDIA-JOB-002", asset_id="FILM-JOB-002", operation="index", payload={}, requested_by="ANALYST-1", max_attempts=1)
            service.claim_job(job_id="MEDIA-JOB-002", worker_id="WORKER-1")
            failed = service.fail_job(job_id="MEDIA-JOB-002", worker_id="WORKER-1", error_code="INDEX_FAILED", error_message="index unavailable")
            self.assertEqual(failed["status"], "failed")


if __name__ == "__main__":
    unittest.main()
