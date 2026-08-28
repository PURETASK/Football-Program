"""Run non-activating NFL FIDOS deployment preflight evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from nfl_fidos.deployment_preflight import run_deployment_preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path("deployment/nfl-fidos-deployment.json"))
    parser.add_argument("--control-root", type=Path, default=Path("."))
    parser.add_argument("--environment", choices=("local", "validation", "production"))
    args = parser.parse_args(argv)
    result = run_deployment_preflight(contract_path=args.contract, control_root=args.control_root, environ=dict(os.environ), environment=args.environment)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
