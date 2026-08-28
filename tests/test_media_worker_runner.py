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
            self.assertEqual(report["operation_counts"], {"probe": 1})
            self.assertEqual(report["status_counts"], {"completed": 1})
            self.assertEqual(report["results"][0]["asset_id"], "FILM-RUNNER-001")
            self.assertFalse(report["external_state_changed"])
            self.assertEqual(repository.get("media_processing_jobs", "MEDIA-JOB-RUNNER-001")["status"], "completed")

    def test_runner_report_explains_retryable_operation_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "game.mp4"
            media.write_bytes(b"fixture")
            tenant = TenantRepository(JsonRepository(root / "state.json"), organization_id="ORG-WORKER-RUNNER", actor="OWNER")
            MediaProcessingJobService(tenant).create_job(
                job_id="MEDIA-JOB-RUNNER-FAIL",
                asset_id="FILM-RUNNER-FAIL",
                operation="thumbnail",
                payload={"file_path": str(media), "output_path": str(root / "thumb.jpg"), "allowed_roots": [str(root)]},
                requested_by="OWNER",
                max_attempts=2,
            )
            report = MediaWorkerRunner(tenant).run_batch(worker_id="MEDIA-WORKER-001", actor="OWNER", allowed_roots=[str(root)], runner=lambda args: (127, "", "ffmpeg unavailable"))
            self.assertEqual(report["status"], "partial_failure")
            self.assertEqual(report["operation_counts"], {"thumbnail": 1})
            self.assertEqual(report["status_counts"], {"retryable": 1})
            self.assertEqual(report["next_action"], "retry_or_review_failed_jobs")
            self.assertEqual(report["results"][0]["last_error"]["code"], "MEDIA-THUMBNAIL-FAILED")

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
        previous_ffprobe = os.environ.get("NFL_FIDOS_FFPROBE")
        os.environ["NFL_FIDOS_FFPROBE"] = "ffprobe-command-not-installed-for-test"
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
            self.assertEqual(payload["data"]["status"], "completed")
            self.assertEqual(payload["data"]["completed_count"], 1)
            self.assertEqual(payload["data"]["failed_count"], 0)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        if previous_ffprobe is None:
            os.environ.pop("NFL_FIDOS_FFPROBE", None)
        else:
            os.environ["NFL_FIDOS_FFPROBE"] = previous_ffprobe

    def test_authorized_reader_can_fetch_job_outputs_and_batch_history(self):
        secret = "media-job-detail-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-JOB-DETAIL", role="analyst", organization_id="ORG-JOB-DETAIL", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            tenant = TenantRepository(repository, organization_id="ORG-JOB-DETAIL", actor="ANALYST-JOB-DETAIL")
            MediaProcessingJobService(tenant).create_job(job_id="MEDIA-JOB-DETAIL-001", asset_id="FILM-DETAIL-001", operation="probe", payload={}, requested_by="ANALYST-JOB-DETAIL")
            tenant.put("media_processing_outputs", "MEDIA-OUTPUT-DETAIL-001", {"organization_id": "ORG-JOB-DETAIL", "job_id": "MEDIA-JOB-DETAIL-001", "result": {"status": "metadata_only"}}, actor="WORKER", reason="fixture")
            tenant.put("media_worker_batches", "MEDIA-WORKER-BATCH-DETAIL-001", {"organization_id": "ORG-JOB-DETAIL", "results": [{"job_id": "MEDIA-JOB-DETAIL-001", "status": "completed"}]}, actor="WORKER", reason="fixture")
            status, payload = handle_request(method="GET", path="/v1/media/jobs/MEDIA-JOB-DETAIL-001?organization_id=ORG-JOB-DETAIL", headers=headers, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["job"]["id"], "MEDIA-JOB-DETAIL-001")
            self.assertEqual(len(payload["data"]["outputs"]), 1)
            self.assertEqual(len(payload["data"]["batches"]), 1)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_media_job_detail_cannot_cross_organization_boundary(self):
        secret = "media-job-detail-tenant-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        owner_token = issue_token(subject="OWNER-TENANT-A", role="program_owner", organization_id="ORG-TENANT-A", secret=secret)
        other_token = issue_token(subject="OWNER-TENANT-B", role="program_owner", organization_id="ORG-TENANT-B", secret=secret)
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            TenantRepository(repository, organization_id="ORG-TENANT-A", actor="OWNER-TENANT-A").put("media_processing_jobs", "MEDIA-JOB-TENANT-A", {"organization_id": "ORG-TENANT-A", "asset_id": "FILM-TENANT-A", "operation": "index", "status": "queued"}, actor="OWNER-TENANT-A", reason="fixture")
            status, payload = handle_request(method="GET", path="/v1/media/jobs/MEDIA-JOB-TENANT-A?organization_id=ORG-TENANT-A", headers={"Authorization": "Bearer " + owner_token}, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["job"]["organization_id"], "ORG-TENANT-A")
            status, _ = handle_request(method="GET", path="/v1/media/jobs/MEDIA-JOB-TENANT-A?organization_id=ORG-TENANT-A", headers={"Authorization": "Bearer " + other_token}, service=service)
            self.assertEqual(status, 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
