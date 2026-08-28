"""Validate scheduler registration without contacting or modifying an external scheduler."""

from __future__ import annotations

import argparse
import json
import os

from nfl_fidos.scheduler_registration import load_scheduler_registration, validate_scheduler_registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("local", "validation", "production"), default=None)
    args = parser.parse_args(argv)
    environment = args.environment or os.environ.get("NFL_FIDOS_ENV", "local")
    result = validate_scheduler_registration(registration=load_scheduler_registration(), environment=environment)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
