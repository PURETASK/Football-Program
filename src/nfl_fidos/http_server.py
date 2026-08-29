"""Optional standard-library HTTP adapter for the pure API router."""

from __future__ import annotations

import json
import sqlite3
import hashlib
import os
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from .api import handle_request
from .repository import JsonRepository
from .service import FootballIntelligenceService
from .sqlite_repository import SqliteRepository
from .auth import authorize_principal, verify_token
from .tenant_repository import TenantRepository
from .config import resolve_auth_secret
from .security_controls import SlidingWindowRateLimiter, configured_rate_limit


REQUEST_RATE_LIMITER = SlidingWindowRateLimiter(limit=120, window_seconds=60)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_UI_ROOT = PROJECT_ROOT / "ui"
REACT_DIST_ROOT = PROJECT_ROOT / "frontend" / "dist"

STATIC_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


class FidosHTTPServer(ThreadingHTTPServer):
    """Threaded server that drains request handlers before repository teardown.

    ``ThreadingHTTPServer`` defaults to daemon request threads. That is
    convenient for a short-lived demo server, but unsafe for the SQLite
    adapter: a long-lived SSE collaboration request can still be reading
    while an owner calls ``server_close()`` and closes the shared connection.
    Non-daemon handlers plus ``block_on_close`` make shutdown a real lifecycle
    boundary and prevent use-after-close races.
    """

    daemon_threads = False
    block_on_close = True


def _safe_child(root: Path, relative_path: str) -> Path | None:
    """Resolve a request-owned relative path without allowing traversal."""
    try:
        candidate = (root / relative_path).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict, *, extra_headers: dict[str, str] | None = None) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if extra_headers:
        for key, value in extra_headers.items():
            handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(encoded)


class FidosRequestHandler(BaseHTTPRequestHandler):
    def handle(self) -> None:  # noqa: D401 - stdlib handler contract
        """Ignore normal client disconnects without noisy server tracebacks."""
        try:
            super().handle()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

    def _allow_request(self) -> bool:
        authorization = self.headers.get("Authorization", "")
        token_fingerprint = hashlib.sha256(authorization.encode("utf-8")).hexdigest()[:16]
        client = self.client_address[0] if self.client_address else "unknown"
        limiter = getattr(self.server, "request_rate_limiter", REQUEST_RATE_LIMITER)
        result = limiter.check(f"{client}:{self.command}:{urlparse(self.path).path}:{token_fingerprint}")
        if result["allowed"]:
            return True
        _json_response(self, 429, {"status": "rate_limited", "data": result, "error": "Request rate limit exceeded; retry after the indicated interval."}, extra_headers={"Retry-After": str(result["retry_after_seconds"])})
        return False

    def _write_static_file(self, path: Path, *, cache_control: str) -> None:
        document = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", STATIC_MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(document)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()
        self.wfile.write(document)

    def _write_html_file(self, path: Path, *, cache_control: str = "no-store") -> None:
        document = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(document)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(document)

    def _serve_ui_asset(self) -> bool:
        """Serve legacy assets and the incrementally migrated React app."""
        request_path = urlparse(self.path).path

        legacy_name = request_path.removeprefix("/")
        is_legacy_asset = (
            "/" not in legacy_name
            and Path(legacy_name).suffix.lower() in {".css", ".js"}
            and (legacy_name.startswith("play-designer") or legacy_name.startswith("pilot-verification"))
        )
        if is_legacy_asset:
            legacy_asset = _safe_child(LEGACY_UI_ROOT, legacy_name)
            if legacy_asset is None or not legacy_asset.is_file():
                _json_response(self, 404, {"status": "error", "data": None, "error": "UI asset not found"})
                return True
            self._write_static_file(legacy_asset, cache_control="no-cache")
            return True

        if request_path == "/app" or request_path.startswith("/app/"):
            index = REACT_DIST_ROOT / "index.html"
            relative_path = request_path.removeprefix("/app").lstrip("/")
            if relative_path:
                app_asset = _safe_child(REACT_DIST_ROOT, relative_path)
                if app_asset is not None and app_asset.is_file():
                    cache_control = "public, max-age=31536000, immutable" if relative_path.startswith("assets/") else "no-cache"
                    self._write_static_file(app_asset, cache_control=cache_control)
                    return True
                if relative_path.startswith("assets/"):
                    _json_response(self, 404, {"status": "error", "data": None, "error": "Application asset not found"})
                    return True
            if not index.is_file():
                _json_response(
                    self,
                    503,
                    {
                        "status": "unavailable",
                        "data": None,
                        "error": "The React application has not been built. Run npm install and npm run build from frontend/.",
                    },
                )
                return True
            self._write_html_file(index)
            return True
        return False

    def _serve_media_content(self) -> bool:
        parsed = urlparse(self.path)
        prefix = "/v1/media/assets/"
        if not (parsed.path.startswith(prefix) and parsed.path.endswith("/content")):
            return False
        asset_id = parsed.path[len(prefix):-len("/content")].strip("/")
        query = parse_qs(parsed.query)
        organization_id = query.get("organization_id", [""])[0]
        authorization = self.headers.get("Authorization", "")
        try:
            secret = resolve_auth_secret()
        except ValueError:
            secret = ""
        if not organization_id or not authorization.startswith("Bearer ") or not secret:
            _json_response(self, 401, {"status":"error", "data":None, "error":"Bearer authentication and organization scope are required"})
            return True
        try:
            principal = verify_token(authorization.removeprefix("Bearer ").strip(), secret=secret)
            decision = authorize_principal(principal=principal, action="read_film", organization_id=organization_id)
        except ValueError:
            decision = {"allowed":False}
        if not decision.get("allowed"):
            _json_response(self, 403, {"status":"error", "data":decision, "error":"Permission or organization scope denied"})
            return True
        tenant = TenantRepository(self.server.fidos_service.repository, organization_id=principal.organization_id, actor=principal.subject)
        asset = tenant.get("film_assets", asset_id)
        if not asset:
            _json_response(self, 404, {"status":"error", "data":None, "error":"Media asset not found"})
            return True
        uri = asset.get("uri", "")
        parsed_uri = urlparse(uri)
        raw_path = unquote(parsed_uri.path)
        if os.name == "nt" and raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
            raw_path = raw_path[1:]
        path = Path(raw_path) if parsed_uri.scheme == "file" and not parsed_uri.netloc else None
        if path is None or not path.exists() or not path.is_file():
            _json_response(self, 404, {"status":"error", "data":None, "error":"Media content is unavailable"})
            return True
        size = path.stat().st_size
        start, end = 0, size - 1
        status = 200
        range_header = self.headers.get("Range", "")
        if range_header:
            try:
                unit, bounds = range_header.split("=", 1)
                if unit != "bytes" or "," in bounds:
                    raise ValueError
                left, right = bounds.split("-", 1)
                if left:
                    start = int(left)
                    end = int(right) if right else size - 1
                else:
                    suffix = int(right)
                    start = max(0, size - suffix)
                    end = size - 1
                if start < 0 or start > end or end >= size:
                    raise ValueError
                status = 206
            except (ValueError, TypeError):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return True
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", asset.get("media_type", "application/octet-stream"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        return True

    def _serve_collaboration_stream(self) -> bool:
        """Serve authenticated SSE streams for Play Designer and staff events."""
        parsed = urlparse(self.path)
        prefix = "/v1/playbook/designs/"
        suffix = "/events/stream"
        query = parse_qs(parsed.query)
        organization_id = query.get("organization_id", [""])[0]
        organization_stream = parsed.path == "/v1/collaboration/events/stream"
        play_stream = parsed.path.startswith(prefix) and parsed.path.endswith(suffix)
        if not (organization_stream or play_stream):
            return False
        design_id = parsed.path[len(prefix):-len(suffix)].strip("/") if play_stream else ""
        if (play_stream and not design_id) or not organization_id:
            _json_response(self, 400, {"status": "error", "data": None, "error": "organization_id and design_id are required for a Play Designer stream" if play_stream else "organization_id is required"})
            return True
        try:
            since = max(0, int(query.get("since", ["0"])[0]))
            timeout_seconds = min(30.0, max(1.0, float(query.get("timeout", ["25"])[0])))
        except (TypeError, ValueError):
            _json_response(self, 400, {"status": "error", "data": None, "error": "since must be an integer and timeout must be numeric"})
            return True

        def event_path(sequence: int) -> str:
            if organization_stream:
                return f"/v1/collaboration/events?organization_id={quote(organization_id, safe='')}&since={sequence}"
            return f"/v1/playbook/designs/{quote(design_id, safe='')}/events?organization_id={quote(organization_id, safe='')}&since={sequence}"

        # Validate authentication, tenant scope, and design existence before
        # switching to a streaming response.
        status, payload = handle_request(
            method="GET",
            path=event_path(since),
            headers=dict(self.headers.items()),
            service=self.server.fidos_service,
        )
        if status != 200:
            _json_response(self, status, payload)
            return True

        # An SSE request owns its connection for the lifetime of the stream;
        # do not let BaseHTTPRequestHandler attempt to parse a second request
        # after the browser closes the stream.
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()

        def write_chunk(chunk: str) -> None:
            self.wfile.write(chunk.encode("utf-8"))
            self.wfile.flush()

        try:
            write_chunk("retry: 1500\n\n")
            deadline = time.monotonic() + timeout_seconds
            heartbeat_at = time.monotonic() + 10.0
            while time.monotonic() < deadline:
                status, payload = handle_request(
                    method="GET",
                    path=event_path(since),
                    headers=dict(self.headers.items()),
                    service=self.server.fidos_service,
                )
                if status != 200:
                    write_chunk(f"event: stream_error\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n")
                    break
                events = payload.get("data", {}).get("events", []) if isinstance(payload, dict) else []
                for event in events:
                    sequence = int(event.get("sequence", since))
                    event_name = str(event.get("event_type", "collaboration_event"))
                    write_chunk(
                        f"id: {sequence}\n"
                        f"event: {event_name}\n"
                        f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
                    )
                    since = max(since, sequence)
                now = time.monotonic()
                if not events and now >= heartbeat_at:
                    write_chunk(": keep-alive\n\n")
                    heartbeat_at = now + 10.0
                if not events:
                    time.sleep(min(0.5, max(0.0, deadline - now)))
            write_chunk("event: stream_end\ndata: {}\n\n")
        except (BrokenPipeError, ConnectionResetError, OSError, sqlite3.ProgrammingError):
            pass
        return True

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        if not self._allow_request():
            return
        if self._serve_ui_asset():
            return
        if self._serve_media_content():
            return
        if self._serve_collaboration_stream():
            return
        if self.path in {"/", "/operator-dashboard"}:
            document = (LEGACY_UI_ROOT / "operator-dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(document)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(document)
            return
        status, payload = handle_request(method="GET", path=self.path, headers=dict(self.headers.items()), service=self.server.fidos_service)
        _json_response(self, status, payload)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
        if not self._allow_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 2_000_000:
                raise ValueError("request body exceeds 2 MB limit")
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            _json_response(self, 400, {"status":"error", "data":None, "error":str(exc)})
            return
        status, payload = handle_request(method="POST", path=self.path, body=body, headers=dict(self.headers.items()), service=self.server.fidos_service)
        _json_response(self, status, payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8080, database_path: str | Path | None = None) -> tuple[FidosHTTPServer, object]:
    repository = SqliteRepository(database_path) if database_path else JsonRepository(Path.cwd() / ".runtime" / "http-state.json")
    server = FidosHTTPServer((host, port), FidosRequestHandler)
    server.fidos_service = FootballIntelligenceService(repository)
    server.request_rate_limiter = SlidingWindowRateLimiter(limit=configured_rate_limit(), window_seconds=60)
    return server, repository


def serve(host: str = "127.0.0.1", port: int = 8080, database_path: str | Path | None = None) -> None:
    server, repository = create_server(host=host, port=port, database_path=database_path)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        close = getattr(repository, "close", None)
        if close:
            close()
