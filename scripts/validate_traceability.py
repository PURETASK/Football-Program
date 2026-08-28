"""Validate stage coverage and repository-backed evidence references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.traceability import validate_traceability_ledger


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=root / "control" / "requirements-traceability.json")
    parser.add_argument("--root", type=Path, default=root)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    result = validate_traceability_ledger(ledger, root=args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
