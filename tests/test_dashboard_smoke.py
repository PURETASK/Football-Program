import unittest
from unittest.mock import patch

from scripts.dashboard_smoke import run_smoke


class DashboardSmokeTests(unittest.TestCase):
    def test_smoke_includes_authentication_negative_paths(self):
        def fake_get(url):
            if url.endswith('/'):
                return 200, b'NFL Football Intelligence &amp; Development OS film-playlist-form Canonical timeline playback'
            if url.endswith('/health'):
                return 200, b'{"status": "ok"}'
            return 200, b'{"status": "passed", "stage":"STAGE-0"}'

        def fake_request(method, url, body=None):
            return 401, b'{"status":"error"}'

        with patch("scripts.dashboard_smoke._get", side_effect=fake_get), patch("scripts.dashboard_smoke._request", side_effect=fake_request):
            result = run_smoke("http://example.test")
        self.assertEqual(result["status"], "passed")
        names = {check["name"] for check in result["checks"]}
        self.assertTrue({"stage0_auth_boundary", "film_invalid_token_boundary", "usability_auth_boundary"} <= names)


if __name__ == "__main__":
    unittest.main()
