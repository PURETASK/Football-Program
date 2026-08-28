"""Generate a non-activating Stage 0 owner-review packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.stage0_owner_packet import build_stage0_owner_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    root = args.root.resolve()
    registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
    gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
    packet = build_stage0_owner_packet(registry=registry, gap_audit=gap_audit)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0 if packet["review_status"] == "ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
