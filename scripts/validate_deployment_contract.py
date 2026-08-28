"""Validate the non-activating NFL FIDOS deployment topology contract."""

import json
from pathlib import Path

from nfl_fidos.deployment_contract import validate_deployment_contract


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = validate_deployment_contract(path=root / "deployment" / "nfl-fidos-deployment.json")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "valid" else 1)
