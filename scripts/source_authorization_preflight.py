"""Validate source authorization evidence without network access or external state changes."""

from __future__ import annotations

import argparse
import json

from nfl_fidos.source_authorization import load_source_authorization, validate_source_authorization


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--environment", choices=("local", "validation", "production"), default="local")
    args = parser.parse_args(argv)
    result = validate_source_authorization(authorization=load_source_authorization(args.request), environment=args.environment)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "authorized" else 1


if __name__ == "__main__":
    raise SystemExit(main())
