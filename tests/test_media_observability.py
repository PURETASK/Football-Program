import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_ingestion import ingest_media_file
from nfl_fidos.observability import ObservabilityRecorder


class MediaObservabilityTests(unittest.TestCase):
    def test_authorized_media_is_hashed_and_tenant_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "play.mp4"
            media.write_bytes(b"authorized synthetic film")
            result = ingest_media_file(file_path=media, asset_id="FILM-INGEST-001", organization_id="ORG-1", source={"kind":"licensed_film", "ref":"LICENSE-1"}, captured_at="2026-08-23", allowed_roots=[root])
            self.assertEqual(result["status"], "registered")
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(result["organization_id"], "ORG-1")

    def test_unauthorized_or_out_of_root_media_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "play.exe"
            media.write_bytes(b"not film")
            result = ingest_media_file(file_path=media, asset_id="FILM-INGEST-002", organization_id="ORG-1", source={"kind":"unknown", "ref":"X"}, captured_at="2026-08-23", allowed_roots=[])
            self.assertEqual(result["status"], "rejected")
            self.assertIsNone(result["sha256"])

    def test_observability_records_required_runtime_fields_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = ObservabilityRecorder(Path(directory) / "events.jsonl")
            with recorder.span(operation="compile_play", actor="coach-1", organization_id="ORG-1", source_refs=["PLAY-1"]):
                pass
            with self.assertRaises(RuntimeError):
                with recorder.span(operation="blocked_write", actor="coach-1", organization_id="ORG-1"):
                    raise RuntimeError("denied")
            events = recorder.read()
            self.assertEqual(len(events), 2)
            self.assertTrue({"event_id","request_id","actor","organization_id","operation","status","duration_ms","error_code","source_refs"}.issubset(events[0]))
            self.assertEqual(events[1]["status"], "error")

    def test_observability_redacts_secret_material_from_extra_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = ObservabilityRecorder(Path(directory) / "events.jsonl")
            event = recorder.record(operation="secret_check", status="ok", actor="coach-1", organization_id="ORG-1", duration_ms=1, extra={"authorization":"Bearer should-not-persist", "nested":{"api_key":"hidden"}})
            self.assertEqual(event["authorization"], "[REDACTED]")
            self.assertEqual(event["nested"]["api_key"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
