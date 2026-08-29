#!/usr/bin/env python3
"""Run the source-to-implementation conformance audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.master_plan_audit import audit_master_plan


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_MARKDOWN = ROOT / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md"
REPOSITORY_DOCX = ROOT / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.docx"
DEFAULT_MARKDOWN = REPOSITORY_MARKDOWN if REPOSITORY_MARKDOWN.is_file() else Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).md")
DEFAULT_DOCX = REPOSITORY_DOCX if REPOSITORY_DOCX.is_file() else Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).docx")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--traceability", type=Path, default=ROOT / "control" / "requirements-traceability.json")
    parser.add_argument("--output", type=Path, help="Also persist the conformance report to this local JSON path")
    args = parser.parse_args()
    result = audit_master_plan(args.markdown, args.docx, args.root, args.traceability)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        result["evidence_output"] = str(output)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
