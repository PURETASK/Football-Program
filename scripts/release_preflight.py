"""Compose non-activating release and deployment preflight evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from nfl_fidos.deployment_preflight import run_deployment_preflight
from nfl_fidos.deployment_release_preflight import compose_deployment_release_preflight
from nfl_fidos.evals import run_minimum_eval_suite
from nfl_fidos.operational_readiness import run_operational_readiness
from nfl_fidos.release_validation import validate_release_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--environment", choices=("local", "validation", "production"), default="validation")
    parser.add_argument("--database", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    evaluations = run_minimum_eval_suite()
    release = validate_release_artifacts(root=root, eval_result=evaluations)
    preflight = run_deployment_preflight(contract_path=root / "deployment" / "nfl-fidos-deployment.json", control_root=root, environ=dict(os.environ), environment=args.environment)
    readiness = run_operational_readiness(environ={**dict(os.environ), "NFL_FIDOS_ENV":args.environment}, database_path=args.database, run_evals=False, eval_result=evaluations)
    result = compose_deployment_release_preflight(release_validation=release, deployment_preflight=preflight, operational_readiness=readiness, eval_result=evaluations)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready_for_validation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
