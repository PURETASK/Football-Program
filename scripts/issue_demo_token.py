"""Issue a local signed token for the synthetic demo organization."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_fidos.auth import issue_token
from nfl_fidos.config import resolve_auth_secret
from nfl_fidos.demo_data import DEMO_ORGANIZATION_ID


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", default="DEMO-COACH")
    parser.add_argument("--role", choices=["program_owner", "coach_staff", "analyst", "player", "validator", "performance_staff"], default="coach_staff")
    parser.add_argument("--organization-id", default=DEMO_ORGANIZATION_ID)
    parser.add_argument("--ttl-seconds", type=int, default=3600)
    args = parser.parse_args(argv)
    if args.organization_id != DEMO_ORGANIZATION_ID:
        raise SystemExit(f"Demo tokens are locked to {DEMO_ORGANIZATION_ID}")
    environ = dict(os.environ)
    secret = resolve_auth_secret(environ=environ)
    if not secret:
        raise SystemExit("Set NFL_FIDOS_AUTH_SECRET (32+ characters recommended) before issuing a demo token.")
    print(issue_token(subject=args.subject, role=args.role, organization_id=args.organization_id, secret=secret, ttl_seconds=args.ttl_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
