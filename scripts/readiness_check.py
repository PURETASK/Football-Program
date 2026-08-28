"""Run the non-destructive NFL FIDOS operational readiness check."""

from __future__ import annotations

import json
import sys

from nfl_fidos.operational_readiness import run_operational_readiness


def main() -> int:
    report = run_operational_readiness()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
