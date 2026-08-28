"""Validate the local browser-validation evidence package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.browser_evidence import validate_browser_evidence


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=root / "control" / "browser-validation-evidence.json")
    args = parser.parse_args()
    result = validate_browser_evidence(evidence_path=args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
