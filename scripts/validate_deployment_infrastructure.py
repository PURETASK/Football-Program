"""Validate local image instructions against the non-production deployment contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.deployment_infrastructure import validate_deployment_infrastructure


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dockerfile", type=Path, default=root / "Dockerfile")
    parser.add_argument("--contract", type=Path, default=root / "deployment" / "nfl-fidos-deployment.json")
    args = parser.parse_args()
    result = validate_deployment_infrastructure(dockerfile_path=args.dockerfile, contract_path=args.contract)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
