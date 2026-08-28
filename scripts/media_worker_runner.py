"""Run a bounded batch of organization-scoped media jobs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.media_worker_runner import MediaWorkerRunner
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--allowed-root", action="append", required=True)
    parser.add_argument("--max-jobs", type=int, default=10)
    args = parser.parse_args(argv)
    repository = SqliteRepository(args.database)
    try:
        tenant = TenantRepository(repository, organization_id=args.organization_id, actor=args.actor)
        report = MediaWorkerRunner(tenant).run_batch(worker_id=args.worker_id, actor=args.actor, allowed_roots=args.allowed_root, max_jobs=args.max_jobs)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "completed" else 1
    finally:
        repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
