"""Run a bounded local HTTP source-integration rehearsal.

The fixture server is local-only and is never treated as an NFL or production
source. The rehearsal exercises the connector's injected, test-only transport
with real HTTP requests while preserving the production HTTPS allowlist in
``_default_fetcher``.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from nfl_fidos.repository import JsonRepository
from nfl_fidos.source_connectors import SourceConnectorService
from nfl_fidos.tenant_repository import TenantRepository


class _FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib handler contract
        if self.path == "/good":
            content = b"synthetic authorized source content"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://outside.invalid/redirected")
            self.end_headers()
            return
        if self.path == "/oversize":
            content = b"x" * (10_000_001)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        self.send_error(404)

    def log_message(self, *_args):
        return


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fixture_fetcher(base_url: str):
    opener = build_opener(_NoRedirect())

    def fetch(uri: str, max_bytes: int):
        path = urlparse(uri).path
        local_uri = base_url + path
        request = Request(local_uri, headers={"User-Agent": "NFL-FIDOS-local-fixture/1.0"})
        try:
            response = opener.open(request, timeout=5)
        except HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308}:
                location = exc.headers.get("Location", "")
                if urlparse(location).hostname != "source.test":
                    raise ValueError("source redirect left the registered domain allowlist") from exc
            raise ValueError(f"fixture transport failed: {exc}") from exc
        except Exception as exc:
            raise ValueError(f"fixture transport failed: {exc}") from exc
        with response:
            status = getattr(response, "status", 200)
            if status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location", "")
                if urlparse(location).hostname != "source.test":
                    raise ValueError("source redirect left the registered domain allowlist")
            content = response.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise ValueError("source response exceeds configured maximum size")
            return content, {key.lower(): value for key, value in response.headers.items()}

    return fetch


def run_rehearsal(*, records_directory: str | Path | None = None) -> dict:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    directory = tempfile.TemporaryDirectory(dir=str(records_directory) if records_directory else None)
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        repository = JsonRepository(Path(directory.name) / "state.json")
        tenant = TenantRepository(repository, organization_id="ORG-SOURCE-FIXTURE", actor="OWNER-FIXTURE")
        connector = SourceConnectorService(tenant, fetcher=_fixture_fetcher(base_url))
        source_args = {"tier": "tier_1_authoritative", "kind": "official_rulebook", "captured_at": "2026-08-23", "effective_period": "2026-season", "citation_location": "fixture", "owner": "OWNER-FIXTURE", "allowed_domains": ["source.test"], "actor": "OWNER-FIXTURE"}
        for source_id, path in (("SOURCE-FIXTURE-GOOD", "/good"), ("SOURCE-FIXTURE-REDIRECT", "/redirect"), ("SOURCE-FIXTURE-OVERSIZE", "/oversize")):
            connector.register_source(source_id=source_id, uri=f"https://source.test{path}", **source_args)
        good = connector.refresh_source(source_id="SOURCE-FIXTURE-GOOD", actor="ANALYST-FIXTURE")
        redirected = connector.refresh_source(source_id="SOURCE-FIXTURE-REDIRECT", actor="ANALYST-FIXTURE")
        oversized = connector.refresh_source(source_id="SOURCE-FIXTURE-OVERSIZE", actor="ANALYST-FIXTURE")
        sources = connector.list_sources()
        checks = {
            "real_local_http_request_refreshed": good["status"] == "refreshed" and bool(good["sha256"]),
            "redirect_outside_allowlist_failed_closed": redirected["status"] == "failed" and "redirect" in redirected["error"].lower(),
            "oversize_failed_closed": oversized["status"] == "failed" and "maximum size" in oversized["error"].lower(),
            "freshness_state_updated": next(item for item in sources if item["id"] == "SOURCE-FIXTURE-GOOD")["status"] == "current" and not next(item for item in sources if item["id"] == "SOURCE-FIXTURE-GOOD")["stale"],
            "refresh_evidence_persisted": len(tenant.list("source_refreshes")) == 3,
        }
        return {"status": "passed" if all(checks.values()) else "failed", "synthetic": True, "local_fixture": True, "checks": checks, "refresh_results": [good, redirected, oversized], "external_state_changed": False, "production_implementation_allowed": False}
    finally:
        server.shutdown()
        server.server_close()
        directory.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-directory", type=Path)
    args = parser.parse_args(argv)
    result = run_rehearsal(records_directory=args.records_directory)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
