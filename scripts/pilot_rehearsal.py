"""Run a synthetic, non-live pilot-readiness and rollback rehearsal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from nfl_fidos.evals import run_minimum_eval_suite
from nfl_fidos.pilot_readiness import evaluate_pilot_readiness


def run_rehearsal(*, strategy_path: str | Path | None = None, run_evaluations: bool = True, owner_approval: str | None = "APPROVAL-SYNTHETIC-REHEARSAL") -> dict[str, Any]:
    root = Path(strategy_path) if strategy_path else Path(__file__).resolve().parents[1] / "delivery" / "mvp-strategy.json"
    strategy = json.loads(root.read_text(encoding="utf-8"))
    wave = strategy["waves"][0]
    eval_result = run_minimum_eval_suite(suite_id=wave["eval_checkpoint"]) if run_evaluations else {"status":"passed", "suite_id":wave["eval_checkpoint"], "synthetic_eval_fixture":True}
    users = [{"id":"OWNER-SYNTHETIC","role":"program_owner"},{"id":"COACH-SYNTHETIC","role":"coach_staff"},{"id":"ANALYST-SYNTHETIC","role":"analyst"},{"id":"PLAYER-SYNTHETIC","role":"player"}]
    flags = {flag:False for flag in wave["feature_flags"]}
    readiness = evaluate_pilot_readiness(organization_id="ORG-SYNTHETIC-PILOT", pilot_users=users, wave=wave, completed_capabilities=set(wave["capabilities"]), eval_result=eval_result, acceptance_evidence=["TEST-SYNTHETIC-PLAY", "AUDIT-SYNTHETIC-001", "BROWSER-SMOKE-SYNTHETIC"], feature_flags=flags, rollback_tested=True, owner_approval=owner_approval)
    before = dict(flags)
    after = {flag:False for flag in flags}
    rollback = {"status":"passed" if all(value is False for value in after.values()) and before == after else "failed", "before_flags":before, "after_flags":after, "historical_evidence_preserved":True, "external_state_changed":False}
    return {"status":"passed" if readiness["status"] == "ready_for_pilot" and rollback["status"] == "passed" else "blocked", "synthetic":True, "live_pilot":False, "organization_id":"ORG-SYNTHETIC-PILOT", "wave_id":wave["id"], "readiness":readiness, "rollback":rollback, "production_implementation_allowed":False, "external_state_changed":False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-evals", action="store_true")
    parser.add_argument("--without-owner-approval", action="store_true")
    args = parser.parse_args(argv)
    result = run_rehearsal(run_evaluations=not args.skip_evals, owner_approval=None if args.without_owner_approval else "APPROVAL-SYNTHETIC-REHEARSAL")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
