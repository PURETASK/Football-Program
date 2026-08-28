"""Seed the local NFL FIDOS database with a marked synthetic showcase tenant."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, default_database_path, find_demo_records, open_repository, seed_demo_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=None, help="SQLite or JSON repository path; defaults to NFL_FIDOS_DATABASE or .runtime/nfl_fidos.sqlite3")
    parser.add_argument("--organization-id", default=DEMO_ORGANIZATION_ID)
    parser.add_argument("--seed-id", default=DEMO_SEED_ID)
    parser.add_argument("--replace", action="store_true", help="Purge this exact demo seed before recreating it")
    parser.add_argument("--confirm", default="", help="Required with --replace: RESEED-SYNTHETIC-DEMO-DATA")
    parser.add_argument("--no-media", action="store_true", help="Skip optional local FFmpeg demo clip generation")
    parser.add_argument("--dry-run", action="store_true", help="Report matching demo records without changing the repository")
    args = parser.parse_args(argv)
    database = (args.database or default_database_path()).expanduser().resolve()
    if args.dry_run:
        repository = open_repository(database)
        try:
            result = {"status": "dry_run", "database": str(database), "organization_id": args.organization_id, "seed_id": args.seed_id, "record_counts": find_demo_records(repository, organization_id=args.organization_id, seed_id=args.seed_id)}
        finally:
            close = getattr(repository, "close", None)
            if close:
                close()
    else:
        repository = open_repository(database)
        try:
            result = seed_demo_data(repository, database_path=database, organization_id=args.organization_id, seed_id=args.seed_id, replace=args.replace, replace_confirmed=args.confirm == "RESEED-SYNTHETIC-DEMO-DATA", generate_media=not args.no_media)
            result["database"] = str(database)
        finally:
            close = getattr(repository, "close", None)
            if close:
                close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
