"""Dependency-free operator CLI for the NFL FIDOS foundation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .evals import run_minimum_eval_suite
from .ontology import OntologyResolver
from .play_compiler import compile_play


def _print(value: Any) -> int:
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nfl-fidos", description="NFL Football Intelligence & Development OS foundation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="show current program-control state")
    subparsers.add_parser("evals", help="run named minimum evaluation families")
    resolve_parser = subparsers.add_parser("resolve", help="resolve a canonical NFL term or alias")
    resolve_parser.add_argument("term")
    compile_parser = subparsers.add_parser("compile", help="compile a play JSON file")
    compile_parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    if args.command == "evals":
        result = run_minimum_eval_suite()
        _print(result)
        return 0 if result["status"] == "passed" else 1
    if args.command == "resolve":
        return _print(OntologyResolver().resolve(args.term))
    if args.command == "compile":
        with args.path.open(encoding="utf-8") as handle:
            result = compile_play(json.load(handle))
        payload = {"valid": result.valid, "normalized_play": result.normalized_play, "issues": [issue.__dict__ for issue in result.issues]}
        _print(payload)
        return 0 if result.valid else 1
    if args.command == "validate":
        root = Path(__file__).resolve().parents[2]
        with (root / "control" / "manifest.json").open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        with (root / "control" / "stage-0a-registry.json").open(encoding="utf-8") as handle:
            registry = json.load(handle)
        return _print({
            "status": "valid",
            "scope": manifest["scope"],
            "current_stage": manifest["current_stage"],
            "current_work_package": manifest["current_work_package"],
            "production_implementation_allowed": manifest["production_implementation_allowed"],
            "counts": {key: len(registry[key]) for key in ("capabilities", "agents", "objects", "workflows", "nuance_classes", "risks", "questions")},
        })
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
