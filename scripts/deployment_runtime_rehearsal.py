"""Exercise the configured HTTP runtime and SQLite persistence in a temporary workspace."""

from __future__ import annotations

import json
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nfl_fidos.http_server import create_server


def _get(base: str, path: str) -> tuple[int, bytes]:
    with urlopen(base + path, timeout=30) as response:
        return response.status, response.read()


def _post(base: str, path: str, payload: bytes) -> tuple[int, bytes]:
    request = Request(base + path, data=payload, method="POST", headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def run_rehearsal() -> dict:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-runtime-") as directory:
        database = Path(directory) / "nfl_fidos.sqlite3"
        server, repository = create_server(host="127.0.0.1", port=0, database_path=database)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            status, body = _get(base, "/health")
            checks["health"] = status == 200 and b'"status": "ok"' in body
            status, body = _get(base, "/v1/control")
            checks["control_plane"] = status == 200 and b'"stage": "STAGE-0"' in body
            status, body = _get(base, "/operator-dashboard")
            checks["dashboard_served"] = status == 200 and b"NFL Football Intelligence" in body
            status, body = _get(base, "/v1/evals")
            checks["evaluations"] = status == 200 and b'"status": "passed"' in body
            status, body = _post(base, "/v1/plays/compile", b"not-json")
            checks["malformed_request_boundary"] = status == 400 and b'"status": "error"' in body
            status, body = _post(base, "/v1/unknown", b"{}")
            checks["unknown_post_boundary"] = status == 405 and b'"status": "error"' in body
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
            repository.close()
        checks["sqlite_created"] = database.exists() and database.stat().st_size > 0
        # A second server instance proves the configured persistence path can be reopened.
        second, second_repository = create_server(host="127.0.0.1", port=0, database_path=database)
        second_thread = threading.Thread(target=second.serve_forever, daemon=True)
        second_thread.start()
        try:
            status, body = _get(f"http://127.0.0.1:{second.server_address[1]}", "/health")
            checks["reopen"] = status == 200 and b'"status": "ok"' in body
        finally:
            second.shutdown()
            second_thread.join(timeout=5)
            second.server_close()
            second_repository.close()
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "temporary_workspace": True,
        "external_state_changed": False,
        "activation_performed": False,
        "production_implementation_allowed": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_rehearsal(), indent=2, sort_keys=True))
