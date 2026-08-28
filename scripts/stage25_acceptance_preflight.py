"""Generate a non-activating Stage 25 specification-acceptance packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.master_spec_acceptance import load_master_spec
from nfl_fidos.stage25_acceptance_packet import build_stage25_acceptance_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("control/master-codex-build-spec.json"))
    parser.add_argument("--audit-ref", default="NFL_FIDOS_SOURCE_AUDIT.md")
    args = parser.parse_args(argv)
    packet = build_stage25_acceptance_packet(spec=load_master_spec(args.spec), audit_ref=args.audit_ref)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0 if packet["review_status"] == "ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
