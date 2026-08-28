"""Inspect secret-manager wiring without printing secret values."""

from __future__ import annotations

import argparse
import json
import os

from nfl_fidos.secret_source import inspect_secret_source


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("local", "validation", "production"), default=None)
    args = parser.parse_args(argv)
    environment = args.environment or os.environ.get("NFL_FIDOS_ENV", "local")
    result = inspect_secret_source(environment=environment, require_external_source=environment == "production")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
