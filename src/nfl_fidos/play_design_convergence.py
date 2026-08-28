"""Deterministic multi-editor convergence rehearsals for Play Designer drafts.

This module deliberately exercises the existing three-way merge contract in
memory. It does not open sockets, write canonical records, or claim that a
real multi-client deployment has been validated.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .play_design_versioning import design_checksum, three_way_merge


def _scenario_design() -> dict[str, Any]:
    return {
        "id": "CONVERGENCE-REHEARSAL-001",
        "organization_id": "ORG-CONVERGENCE-REHEARSAL",
        "unit": "offense",
        "formation": "shotgun_2x2",
        "concept": "spacing",
        "players": [
            {"id": "QB", "position": "QB", "start": {"x": 50, "y": 36}},
            {"id": "X", "position": "WR", "start": {"x": 12, "y": 30}},
        ],
        "elements": [
            {"id": "ROUTE-X", "kind": "route", "player_id": "X", "type": "go", "depth_yards": 12, "points": [{"x": 12, "y": 30}, {"x": 12, "y": 18}]},
            {"id": "READ-QB", "kind": "read", "player_id": "QB", "type": "corner", "points": [{"x": 50, "y": 36}, {"x": 44, "y": 24}]},
        ],
        "timeline": {"snap_ms": 0, "events": []},
    }


def _edit(design: dict[str, Any], *, formation: str | None = None, route_type: str | None = None) -> dict[str, Any]:
    candidate = deepcopy(design)
    if formation is not None:
        candidate["formation"] = formation
    if route_type is not None:
        route = next(item for item in candidate["elements"] if item["id"] == "ROUTE-X")
        route["type"] = route_type
    return candidate


def run_convergence_rehearsal() -> dict[str, Any]:
    """Run disjoint and overlapping two-editor merge scenarios."""
    base = _scenario_design()
    editor_a = _edit(base, formation="trips_right")
    editor_b = _edit(base, route_type="corner")
    forward = three_way_merge(base, editor_a, editor_b)
    reverse = three_way_merge(base, editor_b, editor_a)
    disjoint = {
        "conflicts": forward["conflicts"],
        "reverse_conflicts": reverse["conflicts"],
        "converged": not forward["conflicts"] and not reverse["conflicts"] and design_checksum(forward["merged"]) == design_checksum(reverse["merged"]),
        "checksum": design_checksum(forward["merged"]),
    }

    overlap_a = _edit(base, route_type="post")
    overlap_b = _edit(base, route_type="corner")
    overlap_forward = three_way_merge(base, overlap_a, overlap_b)
    overlap_reverse = three_way_merge(base, overlap_b, overlap_a)
    overlap = {
        "conflicts": overlap_forward["conflicts"],
        "reverse_conflicts": overlap_reverse["conflicts"],
        "conflict_detected": bool(overlap_forward["conflicts"]) and overlap_forward["conflicts"] == overlap_reverse["conflicts"],
        "selected_forward_value": overlap_forward["merged"]["elements"][0].get("type"),
        "selected_reverse_value": overlap_reverse["merged"]["elements"][0].get("type"),
    }
    cases = {"disjoint_edits": disjoint, "overlapping_edits": overlap}
    return {
        "status": "passed" if disjoint["converged"] and overlap["conflict_detected"] else "blocked",
        "cases": cases,
        "external_state_changed": False,
        "limitations": ["In-memory deterministic rehearsal only; network latency, transport ordering, and real browser multi-client behavior still require deployment-environment testing."],
    }
