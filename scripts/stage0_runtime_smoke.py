"""Run a bounded HTTP smoke test against the synthetic Stage 0 organization."""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from nfl_fidos.auth import issue_token
from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, find_demo_records, open_repository, purge_demo_data, seed_demo_data
from nfl_fidos.http_server import create_server


DEMO_SECRET = "stage0-runtime-smoke-secret-012345678901234567890"

# These are the shipped React route contracts.  Keeping the list in the
# served-app smoke prevents a route from silently regressing to a 404 or an
# HTML fallback with missing assets while component tests still pass.
FRONTEND_ROUTES = (
    "/app/",
    "/app/inbox",
    "/app/roster",
    "/app/analytics",
    "/app/delivery",
    "/app/collaboration",
    "/app/playbook",
    "/app/film",
    "/app/practice",
    "/app/scouting",
    "/app/game-plan",
    "/app/player",
    "/app/admin",
    "/app/admin/stage-25",
    "/app/admin/population-readiness",
    "/app/reviews",
    "/app/playbook/designer/new",
    "/app/playbook/designer/new?unit=defense",
)


def _get(base: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = Request(base.rstrip("/") + path, headers=headers or {})
    with urlopen(request, timeout=10) as response:
        return response.status, response.read()


def run_smoke(database: Path) -> dict[str, object]:
    """Seed locally, exercise public and authenticated routes, then shut down."""
    database = database.expanduser().resolve()
    repository = open_repository(database)
    try:
        seed = seed_demo_data(repository, database_path=database, seed_id=DEMO_SEED_ID, generate_media=False)
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()

    previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
    os.environ["NFL_FIDOS_AUTH_SECRET"] = DEMO_SECRET
    server, server_repository = create_server(host="127.0.0.1", port=0, database_path=database)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        checks: list[dict[str, object]] = []

        def check(name: str, path: str, headers: dict[str, str] | None = None) -> bytes:
            status, body = _get(base, path, headers)
            checks.append({"name": name, "path": path, "status_code": status, "bytes": len(body), "passed": status == 200 and bool(body)})
            return body

        check("health", "/health")
        index = check("react_shell", "/app/playbook/designer/new").decode("utf-8")
        for route in FRONTEND_ROUTES:
            if route != "/app/playbook/designer/new":
                check("react_route", route)
        asset_paths = re.findall(r'(?:src|href)="(/app/assets/[^"]+)"', index)
        for asset_path in asset_paths:
            check("react_asset", asset_path)

        token = issue_token(subject="DEMO-COACH", role="coach_staff", organization_id=DEMO_ORGANIZATION_ID, secret=DEMO_SECRET)
        owner_token = issue_token(subject="DEMO-PROGRAM-OWNER", role="program_owner", organization_id=DEMO_ORGANIZATION_ID, secret=DEMO_SECRET)
        check(
            "authenticated_playbook_workspace",
            f"/v1/playbook/workspace?organization_id={DEMO_ORGANIZATION_ID}",
            {"Authorization": f"Bearer {token}"},
        )
        review_bundle_body = check(
            "authenticated_stage0_review_bundle",
            f"/v1/control/stage-0-review-bundle?organization_id={DEMO_ORGANIZATION_ID}",
            {"Authorization": f"Bearer {owner_token}"},
        )
        try:
            review_bundle = json.loads(review_bundle_body).get("data", {})
            safety = review_bundle.get("safety", {})
            checks.append({
                "name": "stage0_review_bundle_safe_and_populated",
                "path": "/v1/control/stage-0-review-bundle",
                "status_code": 200,
                "bytes": len(review_bundle_body),
                "review_status": review_bundle.get("review_status"),
                "synthetic_present": review_bundle.get("synthetic_demo", {}).get("present"),
                "passed": review_bundle.get("review_status") == "ready_for_owner_review" and review_bundle.get("synthetic_demo", {}).get("present") is True and all(safety.get(key) is False for key in ("approval_recorded", "stage_advance_authorized", "production_implementation_allowed", "external_state_changed")),
            })
        except (TypeError, ValueError, AttributeError):
            checks.append({"name": "stage0_review_bundle_safe_and_populated", "path": "/v1/control/stage-0-review-bundle", "status_code": 200, "bytes": len(review_bundle_body), "passed": False})
        for unit, expected_kinds in (
            ("offense", {"formation", "route", "motion", "run", "block"}),
            ("defense", {"front", "coverage", "pressure", "stunt", "rotation"}),
        ):
            catalog_body = check(
                f"authenticated_{unit}_asset_catalog",
                f"/v1/playbook/designs/assets?organization_id={DEMO_ORGANIZATION_ID}&unit={unit}",
                {"Authorization": f"Bearer {token}"},
            )
            try:
                catalog = json.loads(catalog_body)
                assets = catalog.get("data", {}).get("assets", [])
                found_kinds = {asset.get("kind") for asset in assets}
                found_categories = {asset.get("category") for asset in assets}
                catalog_check = {
                    "name": f"{unit}_asset_catalog_populated",
                    "path": f"/v1/playbook/designs/assets?unit={unit}",
                    "status_code": 200,
                    "bytes": len(catalog_body),
                    "asset_count": len(assets),
                    "kinds": sorted(kind for kind in found_kinds if kind),
                    "categories": sorted(category for category in found_categories if category),
                    "passed": bool(assets) and expected_kinds.issubset(found_kinds | found_categories),
                }
            except (TypeError, ValueError, AttributeError):
                catalog_check = {
                    "name": f"{unit}_asset_catalog_populated",
                    "path": f"/v1/playbook/designs/assets?unit={unit}",
                    "status_code": 200,
                    "bytes": len(catalog_body),
                    "asset_count": 0,
                    "kinds": [],
                    "categories": [],
                    "passed": False,
                }
            checks.append(catalog_check)
        jobs_body = check(
            "authenticated_media_jobs",
            f"/v1/media/jobs?organization_id={DEMO_ORGANIZATION_ID}",
            {"Authorization": f"Bearer {token}"},
        )
        jobs_payload = json.loads(jobs_body)
        demo_job_id = next((job.get("id") for job in jobs_payload.get("data", {}).get("jobs", []) if job.get("id") == "MEDIA-JOB-DEMO-THUMBNAIL"), None)
        if demo_job_id:
            check(
                "authenticated_media_job_detail",
                f"/v1/media/jobs/{demo_job_id}?organization_id={DEMO_ORGANIZATION_ID}",
                {"Authorization": f"Bearer {token}"},
            )
        else:
            checks.append({"name": "authenticated_media_job_detail", "path": "MEDIA-JOB-DEMO-THUMBNAIL", "status_code": 0, "bytes": 0, "passed": False})
        passed = all(bool(item["passed"]) for item in checks) and bool(asset_paths)
        result = {
            "status": "passed" if passed else "failed",
            "database": str(database),
            "organization_id": DEMO_ORGANIZATION_ID,
            "seed_status": seed.get("status"),
            "synthetic": True,
            "checks": checks,
            "safety": {"production_implementation_allowed": False, "external_state_changed": False, "stage_advance_authorized": False},
        }
        return result
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
        close = getattr(server_repository, "close", None)
        if close:
            close()
        if previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = previous_secret
        cleanup_repository = open_repository(database)
        try:
            cleanup = purge_demo_data(cleanup_repository, database_path=database, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID)
            # The return object is already constructed before finally runs, so
            # retain cleanup evidence in the repository history and expose the
            # postcondition through the smoke result when possible.
            if "result" in locals():
                result["cleanup"] = cleanup
                result["cleanup_verification"] = find_demo_records(cleanup_repository, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID)
        finally:
            close = getattr(cleanup_repository, "close", None)
            if close:
                close()


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=root / ".runtime" / "stage0-demo.sqlite3")
    args = parser.parse_args(argv)
    result = run_smoke(args.database)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
