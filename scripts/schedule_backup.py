"""Plan or execute one bounded, verified SQLite backup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.backup_scheduler import BackupScheduler
from nfl_fidos.config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination_directory", type=Path)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--interval-hours", type=int, default=24)
    parser.add_argument("--keep", type=int, default=7)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    config = load_config()
    result = BackupScheduler(environment=config.environment).run(source=args.source, destination_directory=args.destination_directory, actor=args.actor, execute=args.execute, interval_hours=args.interval_hours, keep=args.keep)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"blocked", "invalid"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
