"""Read-only smoke checks for the operator dashboard and control surfaces."""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get(url: str) -> tuple[int, bytes]:
    # The eval endpoint executes the full deterministic suite; allow enough time
    # for a cold local runtime without weakening the read-only smoke contract.
    with urlopen(url, timeout=30) as response:
        return response.status, response.read()


def _request(method: str, url: str, body: dict | None = None) -> tuple[int, bytes]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def run_smoke(base_url: str) -> dict:
    checks = [
        ("dashboard", "/", [b"NFL Football Intelligence &amp; Development OS", b"film-playlist-form", b"Canonical timeline playback"]),
        ("health", "/health", [b'"status": "ok"']),
        ("control", "/v1/control", [b'"stage"']),
        ("evals", "/v1/evals", [b'"status": "passed"']),
    ]
    results = []
    for name, path, required in checks:
        status, body = _get(base_url.rstrip("/") + path)
        missing = [item.decode("utf-8") for item in required if item not in body]
        results.append({"name": name, "status_code": status, "missing": missing, "passed": status == 200 and not missing})
    boundary_checks = [
        ("stage0_auth_boundary", "GET", "/v1/control/stage-0-approval?organization_id=ORG-BROWSER-SMOKE", None, 401),
        ("film_invalid_token_boundary", "GET", "/v1/film/search?organization_id=ORG-BROWSER-SMOKE", None, 401),
        ("usability_auth_boundary", "POST", "/v1/ux/usability-feedback", {"organization_id":"ORG-BROWSER-SMOKE","feedback_id":"UX-SMOKE-001","session_id":"UX-SESSION-SMOKE","screen_id":"governance","task_id":"TASK-SMOKE","outcome":"completed","severity":"note","feedback_text":"read-only auth boundary check","submitted_at":"2026-08-23T00:00:00Z","evidence_refs":["BROWSER-SMOKE"]}, 401),
    ]
    for name, method, path, body, expected_status in boundary_checks:
        status, response_body = _request(method, base_url.rstrip("/") + path, body)
        results.append({"name": name, "status_code": status, "expected_status": expected_status, "response_present": bool(response_body), "passed": status == expected_status and bool(response_body)})
    return {"read_only": True, "base_url": base_url, "checks": results, "status": "passed" if all(item["passed"] for item in results) else "failed"}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    try:
        result = run_smoke(target)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        result = {"read_only": True, "base_url": target, "status": "failed", "error": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
