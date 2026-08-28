"""Seed a safe Stage 0 rehearsal tenant and print an owner-review report.

This command is intentionally a rehearsal, not an approval shortcut. It
creates the marked synthetic showcase tenant, evaluates the persisted
organization operating set, and embeds the current Stage 0 owner packet. It
never writes a Stage 0 approval, advances the stage, activates production, or
changes an external system.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_fidos.demo_data import (  # noqa: E402
    DEMO_ORGANIZATION_ID,
    DEMO_SEED_ID,
    default_database_path,
    find_demo_records,
    open_repository,
    seed_demo_data,
)
from nfl_fidos.organization_operating_bundle import load_persisted_organization_components  # noqa: E402
from nfl_fidos.organization_population_readiness import build_organization_population_readiness  # noqa: E402
from nfl_fidos.stage0_owner_packet import build_stage0_owner_packet  # noqa: E402
from nfl_fidos.tenant_repository import TenantRepository  # noqa: E402


def build_rehearsal_report(*, root: Path, database: Path, seed: dict[str, Any]) -> dict[str, Any]:
    """Combine seed, Stage 0 packet, and persisted operating-set evidence."""
    registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
    gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
    packet = build_stage0_owner_packet(registry=registry, gap_audit=gap_audit)

    repository = open_repository(database)
    try:
        tenant = TenantRepository(repository, organization_id=DEMO_ORGANIZATION_ID, actor="STAGE0-REHEARSAL")
        components = load_persisted_organization_components(tenant)
        readiness = build_organization_population_readiness(tenant=tenant, organization_id=DEMO_ORGANIZATION_ID, season="2026")
        counts = find_demo_records(repository, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID)
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()

    return {
        "status": "ready_for_owner_review" if packet["review_status"] == "ready_for_owner_review" else "blocked",
        "rehearsal": {
            "synthetic": True,
            "organization_id": DEMO_ORGANIZATION_ID,
            "seed_id": DEMO_SEED_ID,
            "database": str(database),
            "record_counts": counts,
            "persisted_operating_component_count": len(components),
            "population_readiness": readiness,
        },
        "synthetic_walkthroughs": [
            {"workspace": "Play Designer", "entry_point": "PD-DEMO-OFF-DAGGER", "purpose": "Review offensive design, assignments, validation, teaching steps, and published-state rendering."},
            {"workspace": "Play Designer", "entry_point": "PD-DEMO-DEF-COVER3", "purpose": "Review defensive front, coverage, pressure, rotation, assignments, and review-pending workflow."},
            {"workspace": "Play Designer", "entry_point": "PD-DEMO-OFF-DAGGER-COUNTER", "purpose": "Review branch/counter relationships and version-aware playbook navigation."},
            {"workspace": "Player Learning", "entry_point": "PLAYER-DEMO-QB-1", "purpose": "Review player assignment, lesson, mastery evidence, and practice linkage."},
            {"workspace": "Scouting", "entry_point": "OPP-DEMO-LIONS", "purpose": "Review opponent tendencies with sample-size and synthetic-provenance labels."},
            {"workspace": "Game Week", "entry_point": "WEEK-1", "purpose": "Review a synthetic weekly plan, installation priorities, approvals, and delivery records."},
        ],
        "stage0_evidence_summary": {
            "registry_and_gap_audit_present": True,
            "operating_components_persisted": len(components),
            "population_readiness_status": readiness["status"],
            "owner_review_packet_status": packet["review_status"],
            "approval_boundary": "Synthetic data demonstrates the workflow only; it cannot satisfy real owner approval or authorize stage advancement.",
        },
        "seed": seed,
        "stage0_owner_packet": packet,
        "safety": {
            "owner_approval_recorded": False,
            "stage_advance_authorized": False,
            "production_implementation_allowed": False,
            "activation_performed": False,
            "external_state_changed": False,
        },
        "next_human_action": "Program owner reviews the packet and records real approval only after the Stage 0A acceptance criteria are satisfied.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=None, help="SQLite or JSON path; defaults to NFL_FIDOS_DATABASE or .runtime/nfl_fidos.sqlite3")
    parser.add_argument("--no-media", action="store_true", help="Skip optional FFmpeg synthetic clip generation")
    parser.add_argument("--dry-run", action="store_true", help="Do not seed; report existing synthetic records and Stage 0 evidence")
    parser.add_argument("--output", type=Path, default=None, help="Also write the JSON owner-review rehearsal report to this local path")
    args = parser.parse_args(argv)
    database = (args.database or default_database_path()).expanduser().resolve()

    repository = open_repository(database)
    try:
        if args.dry_run:
            seed = {"status": "dry_run", "organization_id": DEMO_ORGANIZATION_ID, "seed_id": DEMO_SEED_ID, "record_counts": find_demo_records(repository, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID), "external_state_changed": False}
        else:
            seed = seed_demo_data(repository, database_path=database, organization_id=DEMO_ORGANIZATION_ID, seed_id=DEMO_SEED_ID, generate_media=not args.no_media)
    finally:
        close = getattr(repository, "close", None)
        if close:
            close()

    report = build_rehearsal_report(root=ROOT, database=database, seed=seed)
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        report["report_output"] = str(output)
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
