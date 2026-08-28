"""Fail-closed removal of the exact NFL FIDOS synthetic demo seed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, default_database_path, find_demo_records, open_repository, purge_demo_data


CONFIRMATION = "DELETE-SYNTHETIC-DEMO-DATA"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=None, help="SQLite or JSON repository path; defaults to NFL_FIDOS_DATABASE or .runtime/nfl_fidos.sqlite3")
    parser.add_argument("--organization-id", default=DEMO_ORGANIZATION_ID)
    parser.add_argument("--seed-id", default=DEMO_SEED_ID)
    parser.add_argument("--confirm", default="", help=f"Required exact confirmation: {CONFIRMATION}")
    parser.add_argument("--dry-run", action="store_true", help="List what would be deleted without changing the repository")
    args = parser.parse_args(argv)
    database = (args.database or default_database_path()).expanduser().resolve()
    repository = open_repository(database)
    try:
        if args.dry_run:
            result = {"status": "dry_run", "database": str(database), "organization_id": args.organization_id, "seed_id": args.seed_id, "record_counts": find_demo_records(repository, organization_id=args.organization_id, seed_id=args.seed_id), "message": f"No records were deleted. Re-run with --confirm {CONFIRMATION} to remove only this exact synthetic seed."}
        else:
            if args.confirm != CONFIRMATION:
                raise SystemExit(f"Refusing to delete anything. Supply --confirm {CONFIRMATION} exactly.")
            result = purge_demo_data(repository, database_path=database, organization_id=args.organization_id, seed_id=args.seed_id)
            result["database"] = str(database)
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
