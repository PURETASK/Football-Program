"""Compose the local, non-activating project evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nfl_fidos.browser_evidence import validate_browser_evidence
from nfl_fidos.feature_parity import audit_feature_parity
from nfl_fidos.project_audit import run_project_audit
from nfl_fidos.stage0_owner_packet import build_stage0_owner_packet


def build_bundle(*, root: Path, run_evals: bool = True) -> dict:
    """Return one review artifact without changing application state."""
    project = run_project_audit(root=root, run_evals=run_evals)
    parity = audit_feature_parity()
    browser = validate_browser_evidence(evidence_path=root / "control" / "browser-validation-evidence.json")
    registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
    gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
    stage0_owner_packet = build_stage0_owner_packet(registry=registry, gap_audit=gap_audit)
    checks = {
        "project_audit": project["status"] == "foundation_verified",
        "feature_parity": parity["status"] == "ready_for_human_review" and not parity["errors"],
        "browser_evidence": browser["status"] == "valid",
        "production_disabled": project["control"]["production_implementation_allowed"] is False,
        "completion_not_claimed": project["completion_claimed"] is False,
        "stage0_owner_packet_ready": stage0_owner_packet["review_status"] == "ready_for_owner_review",
    }
    return {
        "bundle_id": "LOCAL-EVIDENCE-BUNDLE-NFL-FIDOS-001",
        "status": "valid" if all(checks.values()) else "invalid",
        "checks": checks,
        "project_audit": project,
        "feature_parity": parity,
        "browser_evidence": browser,
        "stage0_owner_packet": stage0_owner_packet,
        "safety": {
            "external_state_changed": False,
            "production_implementation_allowed": False,
            "owner_approval_recorded": False,
            "stage_advance_authorized": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--skip-evals", action="store_true")
    parser.add_argument("--output", type=Path, help="Persist the bundle to this local JSON path")
    args = parser.parse_args(argv)
    result = build_bundle(root=args.root.expanduser().resolve(), run_evals=not args.skip_evals)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        result["evidence_output"] = str(output)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
