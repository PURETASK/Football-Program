"""Run a bounded temporary SQLite FTS search-scale and tenancy rehearsal."""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from nfl_fidos.film_search import FilmSearchIndex


def run_rehearsal(*, observations_per_tenant: int = 250, organization_ids: tuple[str, str] = ("ORG-SEARCH-A", "ORG-SEARCH-B")) -> dict[str, Any]:
    if observations_per_tenant <= 0 or observations_per_tenant > 10000:
        raise ValueError("observations_per_tenant must be between 1 and 10000")
    with tempfile.TemporaryDirectory(prefix="nfl-fidos-film-search-") as directory:
        database = Path(directory) / "film-search.sqlite3"
        connection = sqlite3.connect(database)
        index = FilmSearchIndex(connection)
        started = time.perf_counter()
        for tenant_index, organization_id in enumerate(organization_ids):
            for item in range(observations_per_tenant):
                index.upsert({"id":f"FILM-SEARCH-{tenant_index}-{item:05d}","organization_id":organization_id,"label":"two_high_rotation","domain":"coverage","confidence":"moderate","evidence":"rotation visible","context":{"team":organization_id,"opponent":"TEAM-OPP","situation":{"down":3}}})
        index_seconds = time.perf_counter() - started
        started = time.perf_counter()
        first_results = index.search(organization_id=organization_ids[0], query="rotation", opponent="TEAM-OPP")
        second_results = index.search(organization_id=organization_ids[1], query="rotation", opponent="TEAM-OPP")
        cross_tenant = index.search(organization_id=organization_ids[0], query="FILM-SEARCH-1-00000")
        search_seconds = time.perf_counter() - started
        connection.close()
        reopened = sqlite3.connect(database)
        persisted_index = FilmSearchIndex(reopened)
        persisted_results = persisted_index.search(organization_id=organization_ids[0], query="rotation")
        reopened.close()
        checks = {"fts_available": index.available and persisted_index.available, "tenant_a_count": len(first_results) == observations_per_tenant, "tenant_b_count": len(second_results) == observations_per_tenant, "cross_tenant_isolation": not cross_tenant, "persistence": len(persisted_results) == observations_per_tenant}
        return {"status":"passed" if all(checks.values()) else "failed","temporary_workspace":True,"observations_per_tenant":observations_per_tenant,"total_observations":observations_per_tenant * len(organization_ids),"index_seconds":round(index_seconds, 6),"search_seconds":round(search_seconds, 6),"checks":checks,"external_state_changed":False,"production_implementation_allowed":False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations-per-tenant", type=int, default=250)
    args = parser.parse_args(argv)
    result = run_rehearsal(observations_per_tenant=args.observations_per_tenant)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
