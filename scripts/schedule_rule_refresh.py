"""Plan bounded freshness review work for official NFL rule sources."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.rule_source_scheduler import RuleSourceScheduler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("rules/authoritative-source-registry.json"))
    parser.add_argument("--freshness-days", type=int, default=30)
    parser.add_argument("--max-sources", type=int, default=10)
    args = parser.parse_args(argv)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = RuleSourceScheduler().plan_due(registry=registry, now=datetime.now(timezone.utc), freshness_days=args.freshness_days, max_sources=args.max_sources)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
