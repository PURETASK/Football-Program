"""Start the non-production standard-library HTTP adapter for local validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from nfl_fidos.http_server import serve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", type=Path, default=None)
    args = parser.parse_args()
    serve(host=args.host, port=args.port, database_path=args.database)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
