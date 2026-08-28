"""Configured HTTP service entrypoint."""

from __future__ import annotations

import argparse

from .config import load_config
from .http_server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nfl-fidos-server")
    parser.add_argument("--allow-missing-auth-secret", action="store_true", help="local development only")
    args = parser.parse_args(argv)
    config = load_config(require_auth_secret=not args.allow_missing_auth_secret)
    serve(host=config.host, port=config.port, database_path=config.database_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
