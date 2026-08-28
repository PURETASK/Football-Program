"""Validate provider-neutral monitoring registration without external writes."""

from __future__ import annotations

import argparse
import json
import os

from nfl_fidos.monitoring_contract import load_monitoring_contract
from nfl_fidos.monitoring_registration import validate_monitoring_registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("local", "validation", "production"), default=None)
    args = parser.parse_args(argv)
    environment = args.environment or os.environ.get("NFL_FIDOS_ENV", "local")
    result = validate_monitoring_registration(contract=load_monitoring_contract(), environment=environment)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
