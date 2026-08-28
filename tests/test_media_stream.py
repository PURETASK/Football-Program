import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nfl_fidos.auth import issue_token
from nfl_fidos.http_server import create_server


class MediaStreamTests(unittest.TestCase):
    def test_authenticated_full_and_range_reads_are_tenant_scoped(self):
        secret = "media-stream-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.mp4"
            media.write_bytes(b"0123456789")
            server, repository = create_server(port=0, database_path=Path(directory) / "state.sqlite3")
            repository.put("film_assets", "FILM-STREAM-001", {"id":"FILM-STREAM-001", "organization_id":"ORG-STREAM", "uri":media.as_uri(), "media_type":"video/mp4"}, actor="owner", reason="stream_test")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}/v1/media/assets/FILM-STREAM-001/content?organization_id=ORG-STREAM"
                token = issue_token(subject="COACH-STREAM", role="coach_staff", organization_id="ORG-STREAM", secret=secret)
                headers = {"Authorization":"Bearer " + token}
                with urlopen(Request(base, headers=headers)) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b"0123456789")
                with urlopen(Request(base, headers={**headers, "Range":"bytes=2-5"})) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.headers["Content-Range"], "bytes 2-5/10")
                    self.assertEqual(response.read(), b"2345")
                other = issue_token(subject="COACH-OTHER", role="coach_staff", organization_id="ORG-OTHER", secret=secret)
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base, headers={"Authorization":"Bearer " + other}))
                self.assertEqual(error.exception.code, 403)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_invalid_range_is_rejected(self):
        secret = "media-range-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "game.webm"
            media.write_bytes(b"abc")
            server, repository = create_server(port=0, database_path=Path(directory) / "state.sqlite3")
            repository.put("film_assets", "FILM-RANGE-001", {"id":"FILM-RANGE-001", "organization_id":"ORG-RANGE", "uri":media.as_uri(), "media_type":"video/webm"}, actor="owner", reason="range_test")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                token = issue_token(subject="COACH-RANGE", role="coach_staff", organization_id="ORG-RANGE", secret=secret)
                request = Request(f"http://127.0.0.1:{server.server_address[1]}/v1/media/assets/FILM-RANGE-001/content?organization_id=ORG-RANGE", headers={"Authorization":"Bearer " + token, "Range":"bytes=9-10"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, 416)
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()
                repository.close()
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()
