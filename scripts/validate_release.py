"""Validate release artifacts without deploying."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nfl_fidos.evals import run_minimum_eval_suite
from nfl_fidos.release_validation import validate_release_artifacts


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = validate_release_artifacts(root=root, eval_result=run_minimum_eval_suite())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
