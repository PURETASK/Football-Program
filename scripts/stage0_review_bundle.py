"""Build one reproducible, non-activating Stage 0 review bundle.

The bundle combines the current control-plane evidence with an inventory of
the optional synthetic showcase tenant. It never seeds, deletes, approves,
advances, deploys, or contacts an external provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, default_database_path, find_demo_records, open_repository
from nfl_fidos.project_audit import run_project_audit
from nfl_fidos.stage0_owner_packet import build_stage0_owner_packet


REVIEW_FILES = (
    "control/stage-0a-registry.json",
    "control/stage-0-gap-audit.json",
    "control/stage-0-exit-gate.json",
    "control/stage-0-owner-approval-template.json",
    "NFL_FIDOS_SOURCE_AUDIT.md",
    "NFL_FIDOS_IMPLEMENTATION_STATUS.md",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    inventory = []
    for relative in REVIEW_FILES:
        path = root / relative
        inventory.append({
            "path": relative,
            "present": path.is_file(),
            "sha256": _sha256(path) if path.is_file() else None,
        })
    return inventory


def _synthetic_inventory(database: Path) -> dict[str, Any]:
    repository = open_repository(database)
    try:
        counts = find_demo_records(repository, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID)
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()
    return {
        "database": str(database),
        "organization_id": DEMO_ORGANIZATION_ID,
        "seed_id": DEMO_SEED_ID,
        "present": bool(counts),
        "record_counts": counts,
        "synthetic_only": True,
    }


def build_bundle(*, root: Path, database: Path | None = None, run_evals: bool = True) -> dict[str, Any]:
    """Return a point-in-time Stage 0 bundle without changing application state."""
    root = root.expanduser().resolve()
    database = (database or default_database_path()).expanduser().resolve()
    registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
    gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
    project_audit = run_project_audit(root=root, run_evals=run_evals)
    owner_packet = build_stage0_owner_packet(registry=registry, gap_audit=gap_audit)
    files = _file_inventory(root)
    synthetic = _synthetic_inventory(database)
    checks = {
        "review_files_present": all(item["present"] for item in files),
        "project_foundation_verified": project_audit["status"] == "foundation_verified",
        "owner_packet_ready": owner_packet["review_status"] == "ready_for_owner_review",
        "synthetic_inventory_available": synthetic["present"],
        "production_disabled": project_audit["control"]["production_implementation_allowed"] is False,
        "completion_not_claimed": project_audit["completion_claimed"] is False,
    }
    return {
        "bundle_id": "STAGE0-REVIEW-BUNDLE-NFL-FIDOS-001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "valid" if all(checks.values()) else "invalid",
        "checks": checks,
        "review_files": files,
        "project_audit": project_audit,
        "stage0_owner_packet": owner_packet,
        "synthetic_demo": synthetic,
        "safety": {
            "seed_performed": False,
            "deletion_performed": False,
            "approval_recorded": False,
            "stage_advance_authorized": False,
            "production_implementation_allowed": False,
            "external_state_changed": False,
        },
        "next_human_action": "Program owner reviews this bundle and records real Stage 0 approval only after accepting the registry and gap audit.",
    }


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--skip-evals", action="store_true")
    parser.add_argument("--output", type=Path, help="Persist the bundle as a local JSON review artifact")
    args = parser.parse_args(argv)
    result = build_bundle(root=args.root, database=args.database, run_evals=not args.skip_evals)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        result["evidence_output"] = str(output)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
