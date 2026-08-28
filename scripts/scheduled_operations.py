"""External-scheduler entry point; dry-run is the default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nfl_fidos.config import load_config
from nfl_fidos.repository import JsonRepository
from nfl_fidos.scheduled_operations import ScheduledOperationsService
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NFL FIDOS bounded scheduled operations")
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--worker-id", default="SCHEDULER-WORKER")
    parser.add_argument("--database", type=Path, default=Path(".runtime/nfl_fidos.sqlite3"))
    parser.add_argument("--max-sources", type=int, default=100)
    parser.add_argument("--max-transforms", type=int, default=10)
    parser.add_argument("--retention-days", type=int, default=365)
    parser.add_argument("--allowed-root", action="append", default=[])
    parser.add_argument("--execute", action="store_true", help="execute operations; otherwise only plan")
    args = parser.parse_args(argv)
    config = load_config()
    repository = SqliteRepository(args.database) if args.database.suffix.lower() in {".sqlite", ".sqlite3", ".db"} else JsonRepository(args.database)
    try:
        tenant = TenantRepository(repository, organization_id=args.organization_id, actor=args.actor)
        result = ScheduledOperationsService(tenant, environment=config.environment).run(actor=args.actor, worker_id=args.worker_id, execute=args.execute, max_sources=args.max_sources, max_transforms=args.max_transforms, retention_days=args.retention_days, allowed_roots=args.allowed_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("status", "") not in {"blocked", "partial_failure"} else 1
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()


if __name__ == "__main__":
    sys.exit(main())
