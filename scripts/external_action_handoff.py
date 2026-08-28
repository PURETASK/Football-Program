"""Generate a value-free handoff packet for remaining external actions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.external_handoff import build_external_action_handoff


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    ledger = json.loads((root / "control" / "requirements-traceability.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "control" / "manifest.json").read_text(encoding="utf-8"))
    result = build_external_action_handoff(ledger=ledger, manifest=manifest)
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
