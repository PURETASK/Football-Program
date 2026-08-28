"""Run a read-only authenticated Play Designer rehearsal against a local server.

The rehearsal uses the marked synthetic organization and an ephemeral HTTP
server. It does not write canonical records, publish, approve, or contact an
external provider. It is intentionally independent of any already-running
server so a mismatched local environment secret cannot hide a valid demo path.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from nfl_fidos.auth import issue_token
from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, default_database_path
from nfl_fidos.http_server import create_server


DEMO_SECRET = "local-demo-secret-change-me-32-characters"
DESIGN_ID = "PD-DEMO-OFF-DAGGER"


def _get(base_url: str, path: str, token: str) -> tuple[int, dict]:
    request = Request(base_url + path, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - exercised by operator failures
        status = getattr(exc, "code", 0)
        body = {}
        if hasattr(exc, "read"):
            try:
                body = json.loads(exc.read().decode("utf-8"))
            except (OSError, ValueError):
                body = {"error": str(exc)}
        return status, body or {"error": str(exc)}


def run_rehearsal(*, database: Path) -> dict:
    previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
    os.environ["NFL_FIDOS_AUTH_SECRET"] = DEMO_SECRET
    server, repository = create_server(port=0, database_path=database)
    # This is an ephemeral rehearsal server. Do not let an HTTP worker keep a
    # temporary SQLite file locked after the verification request completes.
    server.daemon_threads = True
    server.block_on_close = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        token = issue_token(subject="DEMO-COACH", role="coach_staff", organization_id=DEMO_ORGANIZATION_ID, secret=DEMO_SECRET)
        checks = [
            ("workspace", f"/v1/playbook/designs?organization_id={DEMO_ORGANIZATION_ID}", "playbook designs"),
            ("versions", f"/v1/playbook/designs/{DESIGN_ID}/versions?organization_id={DEMO_ORGANIZATION_ID}", "version history"),
            ("legality", f"/v1/playbook/designs/{DESIGN_ID}/legality?organization_id={DEMO_ORGANIZATION_ID}", "legality report"),
            ("role_view", f"/v1/playbook/designs/{DESIGN_ID}/role-view?organization_id={DEMO_ORGANIZATION_ID}&role=QB&mode=player", "player role view"),
        ]
        results = []
        for name, path, description in checks:
            status, payload = _get(base_url, path, token)
            results.append({
                "name": name,
                "description": description,
                "http_status": status,
                "payload_status": payload.get("status"),
                "passed": status == 200 and payload.get("status") == "ok",
                "integrity_valid": payload.get("data", {}).get("integrity", {}).get("valid") if isinstance(payload.get("data"), dict) else None,
            })
        workspace_payload = next((item for item in results if item["name"] == "workspace"), None)
        workspace_designs = []
        if workspace_payload and workspace_payload["passed"]:
            # The compact result deliberately does not retain the response body;
            # fetch the same read through the repository-backed service below.
            from nfl_fidos.demo_data import open_repository
            from nfl_fidos.play_design_service import PlayDesignService
            from nfl_fidos.tenant_repository import TenantRepository
            repository = open_repository(database)
            try:
                workspace_designs = PlayDesignService(TenantRepository(repository, organization_id=DEMO_ORGANIZATION_ID, actor="DEMO-REHEARSAL")).workspace()["designs"]
            finally:
                repository.close()
        selected = next((item for item in workspace_designs if item.get("id") == DESIGN_ID), None)
        release_check = {
            "name": "immutable_release_metadata",
            "description": "published release metadata",
            "http_status": 200 if selected else 404,
            "payload_status": selected.get("status") if selected else "not_found",
            "passed": bool(selected and selected.get("status") == "published" and selected.get("release_id") and selected.get("latest_snapshot_id") and selected.get("renderer_checksum")),
            "integrity_valid": bool(selected and selected.get("release_bundle", {}).get("immutable") and selected.get("release_bundle", {}).get("game_plan_snapshot_locked")),
        }
        results.append(release_check)
        return {
            "status": "passed" if all(item["passed"] for item in results) else "failed",
            "synthetic": True,
            "organization_id": DEMO_ORGANIZATION_ID,
            "design_id": DESIGN_ID,
            "checks": results,
            "safety": {
                "external_state_changed": False,
                "production_implementation_allowed": False,
                "approval_recorded": False,
                "stage_advance_authorized": False,
            },
        }
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
        repository.close()
        if previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = previous_secret


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=default_database_path())
    args = parser.parse_args()
    report = run_rehearsal(database=args.database.expanduser().resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
