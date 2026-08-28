"""Apply or inspect NFL FIDOS SQLite migrations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nfl_fidos.migrations import apply_migrations, inspect_migrations, rollback_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="NFL FIDOS SQLite migration operator")
    parser.add_argument("database", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--rollback", type=Path)
    args = parser.parse_args()
    if args.rollback:
        result = rollback_snapshot(args.database, args.rollback)
    elif args.dry_run:
        result = apply_migrations(args.database, dry_run=True)
    else:
        result = apply_migrations(args.database, snapshot_path=args.snapshot)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
