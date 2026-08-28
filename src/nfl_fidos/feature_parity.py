"""Legacy-dashboard to React feature-parity audit.

This audit verifies the migration contract without declaring the legacy
dashboard safe to retire. Consolidated entries are valid mappings, but their
retirement decision remains an explicit human governance action.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "control" / "feature-parity-manifest.json"
LEGACY_PATH = ROOT / "ui" / "operator-dashboard.html"
REACT_APP_PATH = ROOT / "frontend" / "src" / "App.tsx"


def _load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_feature_parity(
    *,
    manifest_path: Path = MANIFEST_PATH,
    legacy_path: Path = LEGACY_PATH,
    react_app_path: Path = REACT_APP_PATH,
) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    legacy = legacy_path.read_text(encoding="utf-8") if legacy_path.exists() else ""
    react_app = react_app_path.read_text(encoding="utf-8") if react_app_path.exists() else ""
    errors: list[str] = []
    warnings: list[str] = []
    entries = manifest.get("entries", [])
    seen_ids: set[str] = set()
    seen_anchors: set[str] = set()
    states = {"migrated": 0, "consolidated": 0, "deferred": 0}

    for entry in entries:
        entry_id = entry.get("id")
        anchor = entry.get("legacy_anchor")
        state = entry.get("migration_state")
        if not entry_id or entry_id in seen_ids:
            errors.append(f"duplicate or missing parity id: {entry_id or '<missing>'}")
        if anchor in seen_anchors:
            errors.append(f"duplicate legacy anchor: {anchor}")
        seen_ids.add(entry_id)
        seen_anchors.add(anchor)
        if anchor and f'id="{anchor}"' not in legacy:
            errors.append(f"legacy anchor is not present: {anchor}")
        if state not in states:
            errors.append(f"unsupported migration state for {entry_id}: {state}")
            continue
        states[state] += 1
        react_file = ROOT / str(entry.get("react_file", ""))
        if not react_file.exists():
            errors.append(f"React file is missing for {entry_id}: {entry.get('react_file')}")
        token = entry.get("react_route_token")
        if token == "index":
            if "<Route index" not in react_app:
                errors.append(f"React index route is missing for {entry_id}")
        elif token and f'path="{token}"' not in react_app:
            errors.append(f"React route token is missing for {entry_id}: {token}")
        if state == "deferred":
            warnings.append(f"deferred migration requires explicit follow-up: {entry_id}")

    if manifest.get("retirement_decision") != "not_authorized":
        errors.append("legacy retirement decision must remain not_authorized")
    if not entries:
        errors.append("parity manifest contains no entries")

    complete_mapping = not errors and states["deferred"] == 0
    return {
        "audit_id": "AUDIT-FEATURE-PARITY-001",
        "status": "ready_for_human_review" if complete_mapping else "blocked",
        "legacy_source": str(legacy_path),
        "react_route_source": str(react_app_path),
        "entry_count": len(entries),
        "state_counts": states,
        "errors": errors,
        "warnings": warnings,
        "retirement_authorized": False,
        "next_human_action": "Review every mapped surface for behavioral parity before separately authorizing legacy dashboard retirement.",
    }

