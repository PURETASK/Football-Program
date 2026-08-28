import tempfile
import unittest
from pathlib import Path

from nfl_fidos.config import load_config
from nfl_fidos.observability import ObservabilityRecorder
from nfl_fidos.observability_sink import export_events
from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class ObservabilitySinkTests(unittest.TestCase):
    def test_recorder_exports_structured_events_to_provider_sink(self):
        with tempfile.TemporaryDirectory() as directory:
            received = []
            recorder = ObservabilityRecorder(Path(directory) / "events.jsonl", sink=received.append)
            event = recorder.record(operation="test", status="ok", actor="OWNER", organization_id="ORG-OBS", duration_ms=1.2)
            self.assertEqual(received[0]["event_id"], event["event_id"])
            self.assertEqual(recorder.read()[0]["organization_id"], "ORG-OBS")

    def test_export_is_bounded_and_failures_are_explicit(self):
        events = [{"event_id":f"OBS-{index}"} for index in range(3)]
        received = []
        report = export_events(events, sink=lambda event: received.append(event), max_events=2)
        self.assertEqual(report["selected"], 2)
        self.assertEqual(report["exported"], 2)
        self.assertEqual(len(received), 2)
        failed = export_events(events[:1], sink=lambda event: (_ for _ in ()).throw(RuntimeError("sink down")))
        self.assertEqual(failed["status"], "partial_failure")
        self.assertEqual(failed["failed"], 1)

    def test_secret_file_can_supply_authentication_without_source_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            secret_path = Path(directory) / "secret"
            secret_path.write_text("x" * 32, encoding="utf-8")
            config = load_config(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET_FILE":str(secret_path)})
            self.assertEqual(config.auth_secret, "x" * 32)

    def test_api_uses_mounted_secret_file(self):
        with tempfile.TemporaryDirectory() as directory:
            secret_path = Path(directory) / "secret"
            secret_path.write_text("x" * 32, encoding="utf-8")
            previous_secret = __import__("os").environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            __import__("os").environ["NFL_FIDOS_AUTH_SECRET_FILE"] = str(secret_path)
            try:
                token = issue_token(subject="OWNER-SECRET-FILE", role="program_owner", organization_id="ORG-SECRET-FILE", secret="x" * 32)
                status, _ = handle_request(method="GET", path="/v1/operator/summary?organization_id=ORG-SECRET-FILE", headers={"Authorization":"Bearer " + token}, service=FootballIntelligenceService(JsonRepository(Path(directory) / "state.json")))
                self.assertEqual(status, 200)
            finally:
                __import__("os").environ.pop("NFL_FIDOS_AUTH_SECRET_FILE", None)
                if previous_secret is not None:
                    __import__("os").environ["NFL_FIDOS_AUTH_SECRET"] = previous_secret


if __name__ == "__main__":
    unittest.main()
