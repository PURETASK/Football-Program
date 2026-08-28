import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.media_worker_runner import MediaWorkerRunner
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.tenant_repository import TenantRepository


class MediaWorkerRunnerTests(unittest.TestCase):
    def test_runner_claims_bounded_job_and_persists_batch_report(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.mp4"
            media.write_bytes(b"fixture")
            repository = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(repository, organization_id="ORG-WORKER-RUNNER", actor="OWNER")
            MediaProcessingJobService(tenant).create_job(job_id="MEDIA-JOB-RUNNER-001", asset_id="FILM-RUNNER-001", operation="probe", payload={"file_path":str(media), "allowed_roots":[directory]}, requested_by="OWNER")
            report = MediaWorkerRunner(tenant).run_batch(worker_id="MEDIA-WORKER-001", actor="OWNER", allowed_roots=[directory], runner=lambda args: (0, '{"format":{"duration":"5.0","format_name":"mp4"}}', ""))
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["completed_count"], 1)
            self.assertFalse(report["external_state_changed"])
            self.assertEqual(repository.get("media_processing_jobs", "MEDIA-JOB-RUNNER-001")["status"], "completed")

    def test_runner_requires_approved_root_and_worker_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(repository, organization_id="ORG-WORKER-RUNNER", actor="OWNER")
            report = MediaWorkerRunner(tenant).run_batch(worker_id="WORKER-BAD", actor="OWNER", allowed_roots=[])
            self.assertEqual(report["status"], "rejected")
            self.assertTrue(report["issues"])

    def test_owner_can_run_worker_through_authenticated_api(self):
        secret = "media-worker-runner-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        headers = {"Authorization":"Bearer "+issue_token(subject="OWNER-WORKER-API", role="program_owner", organization_id="ORG-WORKER-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.webm"
            media.write_bytes(b"fixture")
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            tenant = TenantRepository(repository, organization_id="ORG-WORKER-API", actor="OWNER-WORKER-API")
            MediaProcessingJobService(tenant).create_job(job_id="MEDIA-JOB-API-001", asset_id="FILM-API-001", operation="probe", payload={"file_path":str(media), "allowed_roots":[directory]}, requested_by="OWNER-WORKER-API")
            status, payload = handle_request(method="POST", path="/v1/media/worker/run", headers=headers, body={"organization_id":"ORG-WORKER-API", "worker_id":"MEDIA-WORKER-API-001", "allowed_roots":[directory], "max_jobs":1}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["status"], "partial_failure")
            self.assertEqual(payload["data"]["failed_count"], 1)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
