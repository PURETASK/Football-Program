import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nfl_fidos.repository import JsonRepository
from nfl_fidos.source_connectors import SourceConnectorService, _default_fetcher
from nfl_fidos.tenant_repository import TenantRepository


class SourceConnectorTests(unittest.TestCase):
    def test_registered_source_refreshes_with_hash_and_is_current(self):
        with tempfile.TemporaryDirectory() as directory:
            service = SourceConnectorService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SOURCE", actor="OWNER"), fetcher=lambda uri, limit: (b"official source text", {"content-type":"text/plain"}))
            source = service.register_source(source_id="SOURCE-OFFICIAL-001", tier="tier_1_authoritative", kind="official_rulebook", uri="https://rules.example.test/nfl", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER", allowed_domains=["rules.example.test"], actor="OWNER")
            self.assertEqual(source["status"], "registered")
            refresh = service.refresh_source(source_id=source["id"], actor="ANALYST")
            self.assertEqual(refresh["status"], "refreshed")
            self.assertTrue(refresh["sha256"])
            self.assertFalse(service.list_sources()[0]["stale"])

    def test_unauthorized_or_non_https_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            service = SourceConnectorService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SOURCE", actor="OWNER"))
            source = service.register_source(source_id="SOURCE-BAD-001", tier="tier_1_authoritative", kind="official_rulebook", uri="http://unapproved.example.test/rules", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER", allowed_domains=["other.example.test"], actor="OWNER")
            self.assertEqual(source["status"], "rejected")

    def test_default_external_refresh_fails_closed_without_attached_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            service = SourceConnectorService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SOURCE", actor="OWNER"))
            source = service.register_source(source_id="SOURCE-NO-AUTH-001", tier="tier_1_authoritative", kind="official_rulebook", uri="https://rules.example.test/nfl", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER", allowed_domains=["rules.example.test"], actor="OWNER")
            refresh = service.refresh_source(source_id=source["id"], actor="ANALYST")
            self.assertEqual(refresh["status"], "failed")
            self.assertIn("authorization evidence", refresh["error"])

    def test_refresh_all_reports_partial_failures_without_hiding_source_results(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            def fetcher(uri, limit):
                calls.append(uri)
                if uri.endswith("/bad"):
                    raise RuntimeError("fixture failure")
                return b"fresh", {"content-type":"text/plain"}
            service = SourceConnectorService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SOURCE", actor="OWNER"), fetcher=fetcher)
            for source_id, uri in (("SOURCE-GOOD", "https://rules.example.test/good"), ("SOURCE-BAD", "https://rules.example.test/bad")):
                service.register_source(source_id=source_id, tier="tier_1_authoritative", kind="official_rulebook", uri=uri, captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER", allowed_domains=["rules.example.test"], actor="OWNER")
            report = service.refresh_all(actor="ANALYST", stale_only=True)
            self.assertEqual(report["status"], "partial_failure")
            self.assertEqual(report["selected_count"], 2)
            self.assertEqual(report["failed_count"], 1)
            self.assertEqual(len(calls), 2)

    def test_default_fetcher_rejects_redirects_outside_registered_domains(self):
        class Headers:
            def items(self):
                return [("content-type", "text/plain")]
        class Response:
            headers = Headers()
            def geturl(self):
                return "https://outside.example.test/rules"
            def read(self, limit):
                return b"must not be accepted"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        with patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaisesRegex(ValueError, "redirect"):
                _default_fetcher("https://rules.example.test/nfl", 100, allowed_domains=["rules.example.test"])


if __name__ == "__main__":
    unittest.main()
