"""Compose the Master Plan, traceability, evaluation, and control checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.project_audit import run_project_audit


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--skip-evals", action="store_true")
    parser.add_argument("--output", type=Path, help="Also persist the machine-readable checkpoint to this local JSON path")
    args = parser.parse_args()
    result = run_project_audit(root=args.root, markdown=args.markdown, docx=args.docx, run_evals=not args.skip_evals)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        result["evidence_output"] = str(output)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "foundation_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
