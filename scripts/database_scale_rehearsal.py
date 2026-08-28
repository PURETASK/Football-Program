"""Run a bounded synthetic SQLite scale and tenancy rehearsal."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from nfl_fidos.migrations import apply_migrations
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


def run_rehearsal(*, records_per_tenant: int = 100, organization_ids: tuple[str, str] = ("ORG-SCALE-A", "ORG-SCALE-B")) -> dict[str, Any]:
    if records_per_tenant <= 0 or records_per_tenant > 10000:
        raise ValueError("records_per_tenant must be between 1 and 10000")
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-db-scale-") as directory:
        database = Path(directory) / "scale.sqlite3"
        repository = SqliteRepository(database)
        apply_migrations(database)
        tenants = [TenantRepository(repository, organization_id=organization_id, actor="SCALE-REHEARSAL") for organization_id in organization_ids]
        started = time.perf_counter()
        for tenant_index, tenant in enumerate(tenants):
            for index in range(records_per_tenant):
                record_id = f"SCALE-{tenant_index}-{index:05d}"
                tenant.put("scale_records", record_id, {"id":record_id, "organization_id":tenant.organization_id, "ordinal":index}, actor="SCALE-REHEARSAL", reason="scale_fixture")
        write_seconds = time.perf_counter() - started
        started = time.perf_counter()
        visible_counts = [len(tenant.list("scale_records")) for tenant in tenants]
        read_seconds = time.perf_counter() - started
        history_counts = [len(tenant.history(collection="scale_records")) for tenant in tenants]
        leakage = any(record.get("organization_id") not in organization_ids for tenant in tenants for record in tenant.list("scale_records"))
        raw_count = len(repository.list("scale_records"))
        raw_history = len(repository.history(collection="scale_records"))
        repository.close()
        checks = {"write_count":sum(visible_counts) == records_per_tenant * len(tenants), "tenant_read_counts":all(count == records_per_tenant for count in visible_counts), "audit_history_counts":all(count == records_per_tenant for count in history_counts) and raw_history == records_per_tenant * len(tenants), "raw_record_count":raw_count == records_per_tenant * len(tenants), "cross_tenant_isolation":not leakage}
        return {"status":"passed" if all(checks.values()) else "failed", "temporary_workspace":True, "records_per_tenant":records_per_tenant, "total_records":records_per_tenant * len(tenants), "visible_counts":visible_counts, "history_counts":history_counts, "raw_count":raw_count, "raw_history":raw_history, "write_seconds":round(write_seconds, 6), "read_seconds":round(read_seconds, 6), "checks":checks, "external_state_changed":False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-per-tenant", type=int, default=100)
    args = parser.parse_args(argv)
    result = run_rehearsal(records_per_tenant=args.records_per_tenant)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
