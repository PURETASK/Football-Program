"""Run the composed, non-activating NFL FIDOS deployment-environment readiness check."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from nfl_fidos.deployment_environment_readiness import run_deployment_environment_readiness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path("deployment/nfl-fidos-deployment.json"))
    parser.add_argument("--control-root", type=Path, default=Path("."))
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--environment", choices=("local", "validation", "production"), default=None)
    parser.add_argument("--output", type=Path, help="Also persist the value-free readiness report to this local JSON path")
    args = parser.parse_args(argv)
    result = run_deployment_environment_readiness(
        contract_path=args.contract,
        control_root=args.control_root,
        environ=dict(os.environ),
        database_path=args.database,
        environment=args.environment,
    )
    if args.output:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result["evidence_output"] = str(output_path)
        output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
