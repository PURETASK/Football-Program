import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.media_worker import index_media_file, process_media_job, probe_media_file
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class MediaWorkerTests(unittest.TestCase):
    def test_probe_uses_bounded_arguments_and_records_output(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.mp4"
            media.write_bytes(b"authorized fixture")
            calls = []
            def runner(arguments):
                calls.append(arguments)
                return 0, '{"format":{"duration":"12.5","format_name":"mov,mp4"}}', ""
            result = probe_media_file(file_path=media, allowed_roots=[directory], runner=runner)
            self.assertEqual(result["status"], "probed")
            self.assertEqual(result["duration_seconds"], 12.5)
            self.assertEqual(calls[0][0], "ffprobe")
            self.assertNotIn("shell", calls[0])

            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST")
            jobs = MediaProcessingJobService(repository)
            jobs.create_job(job_id="MEDIA-JOB-WORKER-001", asset_id="FILM-ASSET-001", operation="probe", payload={"file_path":str(media), "allowed_roots":[directory]}, requested_by="ANALYST")
            completed = process_media_job(repository=repository, job_id="MEDIA-JOB-WORKER-001", worker_id="WORKER-1", runner=runner)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(len(repository.list("media_processing_outputs")), 1)

    def test_missing_ffprobe_has_safe_metadata_only_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.webm"
            media.write_bytes(b"fixture")
            result = probe_media_file(file_path=media, allowed_roots=[directory], runner=lambda arguments: (127, "", "not found"))
            self.assertEqual(result["status"], "metadata_only")
            self.assertFalse(result["tool_available"])

    def test_index_job_records_searchable_stream_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.mp4"
            media.write_bytes(b"authorized fixture")
            calls = []

            def runner(arguments):
                calls.append(arguments)
                return 0, '{"format":{"duration":"12.5","format_name":"mov,mp4"},"streams":[{"index":0,"codec_type":"video","codec_name":"h264","width":1920,"height":1080},{"index":1,"codec_type":"audio","codec_name":"aac","channels":2}]}', ""

            result = index_media_file(file_path=media, allowed_roots=[directory], runner=runner)
            self.assertEqual(result["status"], "indexed")
            self.assertEqual(result["stream_count"], 2)
            self.assertIn("codec_name", result["searchable_fields"])
            self.assertEqual(calls[0][0], "ffprobe")
            self.assertNotIn("shell", calls[0])

            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST")
            jobs = MediaProcessingJobService(repository)
            jobs.create_job(job_id="MEDIA-JOB-INDEX-001", asset_id="FILM-ASSET-INDEX-001", operation="index", payload={"file_path":str(media), "allowed_roots":[directory]}, requested_by="ANALYST")
            completed = process_media_job(repository=repository, job_id="MEDIA-JOB-INDEX-001", worker_id="WORKER-1", runner=runner)
            self.assertEqual(completed["status"], "completed")
            output = repository.get("media_processing_outputs", "MEDIA-OUTPUT-INDEX-001")
            self.assertEqual(output["result"]["status"], "indexed")

    def test_unapproved_path_is_rejected_before_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.mkv"
            media.write_bytes(b"fixture")
            result = probe_media_file(file_path=media, allowed_roots=[Path(directory) / "other"], runner=lambda arguments: (_ for _ in ()).throw(AssertionError("runner must not execute")))
            self.assertEqual(result["status"], "rejected")

    def test_output_keeps_operation_identity_and_transform_failures_are_truthful(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "game.mp4"
            media.write_bytes(b"fixture")
            repository = TenantRepository(JsonRepository(root / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST")
            jobs = MediaProcessingJobService(repository)
            jobs.create_job(
                job_id="MEDIA-JOB-OUTPUT-001",
                asset_id="FILM-ASSET-OUTPUT-001",
                operation="index",
                payload={"file_path": str(media), "allowed_roots": [str(root)]},
                requested_by="ANALYST",
            )
            completed = process_media_job(
                repository=repository,
                job_id="MEDIA-JOB-OUTPUT-001",
                worker_id="MEDIA-WORKER-001",
                runner=lambda arguments: (0, '{"format":{"duration":"4.0"},"streams":[]}', ""),
            )
            self.assertEqual(completed["status"], "completed")
            output = repository.get("media_processing_outputs", "MEDIA-OUTPUT-OUTPUT-001")
            self.assertEqual(output["operation"], "index")
            self.assertEqual(output["asset_id"], "FILM-ASSET-OUTPUT-001")
            self.assertEqual(output["worker_id"], "MEDIA-WORKER-001")

            jobs.create_job(
                job_id="MEDIA-JOB-THUMBNAIL-FAIL",
                asset_id="FILM-ASSET-OUTPUT-001",
                operation="thumbnail",
                payload={"file_path": str(media), "output_path": str(root / "thumb.jpg"), "allowed_roots": [str(root)]},
                requested_by="ANALYST",
                max_attempts=1,
            )
            failed = process_media_job(
                repository=repository,
                job_id="MEDIA-JOB-THUMBNAIL-FAIL",
                worker_id="MEDIA-WORKER-001",
                runner=lambda arguments: (127, "", "ffmpeg unavailable"),
            )
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(failed["last_error"]["code"], "MEDIA-THUMBNAIL-FAILED")

    def test_malformed_job_input_is_rejected_without_type_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST")
            jobs = MediaProcessingJobService(repository)
            job = jobs.create_job(job_id=None, asset_id=None, operation=None, payload=None, requested_by=None, max_attempts="three")
            self.assertEqual(job["status"], "invalid")
            self.assertIn("payload must be an object", job["issues"])
            self.assertIn("job id must be a string", job["issues"])


if __name__ == "__main__":
    unittest.main()
