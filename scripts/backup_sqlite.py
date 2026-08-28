"""Create or restore a verified SQLite backup."""

from __future__ import annotations

import argparse
import json

from nfl_fidos.database_operations import backup_sqlite_database, restore_sqlite_backup, verify_sqlite_database


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("database")
    backup = subparsers.add_parser("backup")
    backup.add_argument("database")
    backup.add_argument("destination")
    restore = subparsers.add_parser("restore")
    restore.add_argument("backup")
    restore.add_argument("destination")
    args = parser.parse_args()
    if args.command == "verify":
        result = verify_sqlite_database(args.database)
    elif args.command == "backup":
        result = backup_sqlite_database(args.database, args.destination)
    else:
        result = restore_sqlite_backup(args.backup, args.destination)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"valid", "created", "restored"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
