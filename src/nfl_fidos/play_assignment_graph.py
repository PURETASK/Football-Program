"""Structured football-assignment graph primitives for professional play designs.

Diagram geometry answers where an object moves.  The assignment graph answers
why it moves, what it keys, what it depends on, and which player or assignment
it exchanges with.  Keeping those relationships explicit lets validation,
animation, teaching views, and exports use the same football intent.
"""

from __future__ import annotations

from typing import Any


GRAPH_FIELDS = {
    "objective",
    "technique",
    "landmark",
    "depth_yards",
    "leverage",
    "gap",
    "fit_gap",
    "zone",
    "read_key",
    "read_prompt",
    "target_player_id",
    "target_element_id",
    "depends_on",
    "exchange_with",
    "exchange_concept",
    "exclusive_assignment",
}

LEVERAGE_VALUES = {"inside", "outside", "head_up", "top_down", "trail", "stack", "free"}

EXCHANGE_CONCEPT_POSITION_RULES = {
    "tex": "front_exchange",
    "et": "front_exchange",
    "cross_dog": "linebacker_exchange",
    "cross_dog_fire": "linebacker_exchange",
}
INTERIOR_POSITIONS = {"DT", "NT", "DL", "TACKLE", "NOSE", "3T", "4I", "4T", "0T", "1T"}
EDGE_POSITIONS = {"DE", "EDGE", "END", "OLB", "5T", "6T", "7T", "9T", "RUSH"}
LINEBACKER_POSITIONS = {"LB", "ILB", "MLB", "WLB", "WILL", "SAM", "MIKE", "OLB", "JACK", "BUCK", "LINEBACKER"}


def _issue(code: str, message: str, path: str, severity: str = "error", *, suggestion: str | None = None) -> dict[str, Any]:
    issue: dict[str, Any] = {
        "code": code,
        "message": message,
        "explanation": message,
        "path": path,
        "severity": severity,
        "overrideable": severity != "error",
    }
    if suggestion:
        issue["suggestion"] = suggestion
    return issue


def _timing(element: dict[str, Any]) -> tuple[int | None, int | None]:
    timing = element.get("timing") if isinstance(element.get("timing"), dict) else {}
    start = timing.get("start_ms", element.get("start_ms"))
    end = timing.get("end_ms", element.get("end_ms"))
    return (start if isinstance(start, int) and not isinstance(start, bool) else None, end if isinstance(end, int) and not isinstance(end, bool) else None)


def _position_family(player: dict[str, Any] | None) -> str | None:
    if not isinstance(player, dict):
        return None
    tokens = {str(player.get(field, "")).strip().upper() for field in ("position", "role", "alignment_key") if player.get(field)}
    if tokens & INTERIOR_POSITIONS:
        return "interior"
    if tokens & EDGE_POSITIONS:
        return "edge"
    if tokens & LINEBACKER_POSITIONS:
        return "linebacker"
    return None


def _validate_named_exchange_concept(
    element: dict[str, Any],
    partner: dict[str, Any],
    path: str,
    player_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    concept = str(element.get("exchange_concept") or "").strip().lower()
    if not concept or concept not in EXCHANGE_CONCEPT_POSITION_RULES:
        return []
    findings: list[dict[str, Any]] = []
    partner_concept = str(partner.get("exchange_concept") or "").strip().lower()
    if partner_concept != concept:
        findings.append(_issue("ASSIGNMENT-EXCHANGE-CONCEPT-RECIPROCITY", f"Named exchange concept {concept} is not recorded on both sides of the pair.", f"{path}.exchange_concept", "warning", suggestion="Apply the same named concept to both reciprocal assignments."))
    if not str(element.get("exchange_trigger") or "").strip() or not str(element.get("exchange_communication") or "").strip():
        findings.append(_issue("ASSIGNMENT-EXCHANGE-COMMUNICATION-MISSING", f"Named {concept} exchange requires a snap trigger and communication cue.", f"{path}.exchange_communication", "warning", suggestion="Record the trigger and the exact staff/player communication for the exchange."))
    role = str(element.get("exchange_role") or "")
    partner_role = str(partner.get("exchange_role") or "")
    if {role, partner_role} != {"penetrate_loop", "loop_penetrate"} and concept in {"tex", "et", "cross_dog", "cross_dog_fire"}:
        findings.append(_issue("ASSIGNMENT-EXCHANGE-ROLE-MISMATCH", f"Named {concept} exchange requires one penetrate_loop side and one loop_penetrate side.", f"{path}.exchange_role", "warning", suggestion="Set reciprocal penetration and loop responsibilities on the pair."))
    first_family = _position_family(player_by_id.get(str(element.get("player_id"))))
    second_family = _position_family(player_by_id.get(str(partner.get("player_id"))))
    expected = EXCHANGE_CONCEPT_POSITION_RULES[concept]
    if expected == "front_exchange":
        valid = {first_family, second_family} == {"interior", "edge"}
        message = f"Named {concept} exchange expects one interior defensive lineman and one edge defender; found {first_family or 'unknown'} and {second_family or 'unknown'}."
    else:
        valid = first_family == "linebacker" and second_family == "linebacker"
        message = f"Named {concept} exchange expects two linebacker-family partners; found {first_family or 'unknown'} and {second_family or 'unknown'}."
    if not valid:
        findings.append(_issue("ASSIGNMENT-EXCHANGE-PARTNER-MISMATCH", message, f"{path}.exchange_with", "warning", suggestion="Choose position-compatible partners or change the named exchange concept; document an intentional exception in staff review."))
    return findings


def _graph_enabled(design: dict[str, Any], elements: list[dict[str, Any]]) -> bool:
    return bool(design.get("assignment_model_version")) or any(any(field in element for field in GRAPH_FIELDS) for element in elements)


def validate_assignment_graph(design: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate references, dependencies, timing, and exclusive responsibilities."""
    raw_elements = design.get("elements")
    if not isinstance(raw_elements, list):
        return []
    elements = [element for element in raw_elements if isinstance(element, dict)]
    if not _graph_enabled(design, elements):
        return []

    issues: list[dict[str, Any]] = []
    players = design.get("players") if isinstance(design.get("players"), list) else []
    player_ids = {player.get("id") for player in players if isinstance(player, dict) and isinstance(player.get("id"), str)}
    player_by_id = {str(player.get("id")): player for player in players if isinstance(player, dict) and isinstance(player.get("id"), str)}
    element_by_id = {element.get("id"): element for element in elements if isinstance(element.get("id"), str) and element.get("id")}

    for index, element in enumerate(elements):
        path = f"elements[{index}]"
        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            issues.append(_issue("ASSIGNMENT-ID", "Structured assignments require a stable element id", f"{path}.id", suggestion="Assign a stable organization-scoped ID before linking this assignment."))
            continue
        target_player = element.get("target_player_id")
        if target_player is not None and target_player not in player_ids:
            issues.append(_issue("ASSIGNMENT-TARGET-PLAYER", "Assignment target_player_id does not reference a player in this design", f"{path}.target_player_id", suggestion="Choose one of the current offensive or defensive players, or clear the target."))
        target_element = element.get("target_element_id")
        if target_element is not None and target_element not in element_by_id:
            issues.append(_issue("ASSIGNMENT-TARGET-ELEMENT", "Assignment target_element_id does not reference another assignment", f"{path}.target_element_id", suggestion="Relink the read or progression to an existing assignment."))
        if target_element == element_id:
            issues.append(_issue("ASSIGNMENT-SELF-TARGET", "An assignment cannot target itself", f"{path}.target_element_id"))

        dependencies = element.get("depends_on", [])
        if dependencies is not None and not isinstance(dependencies, list):
            issues.append(_issue("ASSIGNMENT-DEPENDENCY-SHAPE", "depends_on must be a list of assignment IDs", f"{path}.depends_on"))
            dependencies = []
        seen_dependencies: set[str] = set()
        for dependency_index, dependency_id in enumerate(dependencies):
            dependency_path = f"{path}.depends_on[{dependency_index}]"
            if not isinstance(dependency_id, str) or not dependency_id:
                issues.append(_issue("ASSIGNMENT-DEPENDENCY-ID", "Dependency references must be non-empty assignment IDs", dependency_path))
                continue
            if dependency_id == element_id:
                issues.append(_issue("ASSIGNMENT-SELF-DEPENDENCY", "An assignment cannot depend on itself", dependency_path))
            elif dependency_id not in element_by_id:
                issues.append(_issue("ASSIGNMENT-DEPENDENCY-REF", "Dependency does not reference an assignment in this design", dependency_path, suggestion="Choose an existing assignment or remove the stale dependency."))
            if dependency_id in seen_dependencies:
                issues.append(_issue("ASSIGNMENT-DUPLICATE-DEPENDENCY", "The same dependency is listed more than once", dependency_path, "warning"))
            seen_dependencies.add(dependency_id)

        exchange_id = element.get("exchange_with")
        if exchange_id is not None:
            if exchange_id == element_id:
                issues.append(_issue("ASSIGNMENT-SELF-EXCHANGE", "An assignment cannot exchange with itself", f"{path}.exchange_with"))
            elif exchange_id not in element_by_id:
                issues.append(_issue("ASSIGNMENT-EXCHANGE-REF", "Exchange target does not reference an assignment in this design", f"{path}.exchange_with", suggestion="Link the paired block, rush, stunt, fit, motion, or read assignment."))
            elif element_by_id[exchange_id].get("exchange_with") not in {None, element_id}:
                issues.append(_issue("ASSIGNMENT-EXCHANGE-CONFLICT", "Exchange target is already paired with a different assignment", f"{path}.exchange_with", "warning", suggestion="Make the exchange reciprocal or choose a different partner."))
            elif str(element_id) < str(exchange_id) and design.get("unit") == "defense":
                issues.extend(_validate_named_exchange_concept(element, element_by_id[exchange_id], path, player_by_id))

        leverage = element.get("leverage")
        if leverage is not None and leverage not in LEVERAGE_VALUES:
            issues.append(_issue("ASSIGNMENT-LEVERAGE", "Leverage must use a supported normalized value", f"{path}.leverage", suggestion=f"Use one of: {', '.join(sorted(LEVERAGE_VALUES))}."))
        depth = element.get("depth_yards")
        if depth is not None and (isinstance(depth, bool) or not isinstance(depth, (int, float)) or depth < 0 or depth > 60):
            issues.append(_issue("ASSIGNMENT-DEPTH", "depth_yards must be a number from 0 through 60", f"{path}.depth_yards"))

    adjacency: dict[str, list[str]] = {}
    for element_id, element in element_by_id.items():
        adjacency[element_id] = [value for value in element.get("depends_on", []) if isinstance(value, str) and value in element_by_id]
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_paths: set[tuple[str, ...]] = set()

    def visit(node: str, chain: list[str]) -> None:
        if node in visiting:
            start = chain.index(node) if node in chain else 0
            cycle_paths.add(tuple(chain[start:] + [node]))
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in adjacency.get(node, []):
            visit(dependency, [*chain, node])
        visiting.remove(node)
        visited.add(node)

    for element_id in adjacency:
        visit(element_id, [])
    for cycle in sorted(cycle_paths):
        issues.append(_issue("ASSIGNMENT-DEPENDENCY-CYCLE", f"Assignment dependency cycle detected: {' -> '.join(cycle)}", "elements", suggestion="Remove or redirect one dependency so the teaching progression has a clear order."))

    exclusives: dict[tuple[str, str], list[str]] = {}
    player_windows: dict[str, list[tuple[str, int, int]]] = {}
    for element_id, element in element_by_id.items():
        if element.get("exclusive_assignment") is not True:
            continue
        target = element.get("target_player_id") or element.get("target_element_id") or element.get("fit_gap") or element.get("gap") or element.get("zone") or element.get("landmark")
        phase = str(element.get("phase") or element.get("kind") or "assignment")
        if target:
            exclusives.setdefault((phase, str(target)), []).append(element_id)
        player_id = element.get("player_id")
        start, end = _timing(element)
        if isinstance(player_id, str) and start is not None and end is not None:
            player_windows.setdefault(player_id, []).append((element_id, start, end))
    for (phase, target), ids in sorted(exclusives.items()):
        if len(ids) > 1:
            issues.append(_issue("ASSIGNMENT-EXCLUSIVE-CONFLICT", f"Exclusive {phase} responsibility {target} is assigned to multiple elements: {', '.join(ids)}", "elements", suggestion="Change the target, phase, or exclusivity rule for one assignment."))
    for player_id, windows in player_windows.items():
        for left_index, (left_id, left_start, left_end) in enumerate(windows):
            for right_id, right_start, right_end in windows[left_index + 1:]:
                if max(left_start, right_start) < min(left_end, right_end):
                    issues.append(_issue("ASSIGNMENT-PLAYER-OVERLAP", f"Player {player_id} has overlapping exclusive assignments {left_id} and {right_id}", "elements", suggestion="Separate their timing windows or mark the compatible responsibility as non-exclusive."))

    for element_id, element in element_by_id.items():
        start, _ = _timing(element)
        if start is None:
            continue
        for dependency_id in adjacency.get(element_id, []):
            _, dependency_end = _timing(element_by_id[dependency_id])
            if dependency_end is not None and start < dependency_end:
                issues.append(_issue("ASSIGNMENT-DEPENDENCY-TIMING", f"{element_id} begins before prerequisite {dependency_id} finishes", f"elements[{elements.index(element)}].depends_on", "warning", suggestion="Move the dependent timing window later or clarify that the actions intentionally overlap."))
    return issues


def build_assignment_graph(design: dict[str, Any]) -> dict[str, Any]:
    """Build a renderer-safe graph summary from structured play elements."""
    raw_elements = design.get("elements") if isinstance(design.get("elements"), list) else []
    elements = [element for element in raw_elements if isinstance(element, dict) and isinstance(element.get("id"), str) and element.get("id")]
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for element in elements:
        start, end = _timing(element)
        nodes.append({
            "id": element["id"],
            "kind": element.get("kind"),
            "label": element.get("type") or element.get("assignment") or element.get("kind"),
            "player_id": element.get("player_id"),
            "objective": element.get("objective"),
            "assignment": element.get("assignment"),
            "responsibility": element.get("responsibility"),
            "technique": element.get("technique"),
            "landmark": element.get("landmark"),
            "type": element.get("type"),
            "route_family": element.get("route_family"),
            "break_type": element.get("break_type"),
            "stem_depth_yards": element.get("stem_depth_yards"),
            "break_depth_yards": element.get("break_depth_yards"),
            "blocking_primitive": element.get("blocking_primitive"),
            "protection_mode": element.get("protection_mode"),
            "gap": element.get("gap_owner") or element.get("fit_gap") or element.get("gap"),
            "zone": element.get("rotation_to_zone") or element.get("zone"),
            "target_element_id": element.get("block_target_element_id") or element.get("target_element_id"),
            "target_player_id": element.get("target_player_id"),
            "exchange_with": element.get("exchange_with"),
            "exchange_concept": element.get("exchange_concept"),
            "start_ms": start,
            "end_ms": end,
        })
        for dependency_id in element.get("depends_on", []) if isinstance(element.get("depends_on"), list) else []:
            if isinstance(dependency_id, str):
                edges.append({"source": dependency_id, "target": element["id"], "relation": "precedes"})
        if isinstance(element.get("exchange_with"), str):
            edges.append({"source": element["id"], "target": element["exchange_with"], "relation": "exchange"})
        if isinstance(element.get("target_element_id"), str):
            edges.append({"source": element["id"], "target": element["target_element_id"], "relation": "targets_assignment"})
        for field, relation in (("block_target_element_id", "blocks_assignment"), ("block_partner_element_id", "combo_partner"), ("protection_target_element_id", "protects_against")):
            target = element.get(field)
            if isinstance(target, str) and target:
                edges.append({"source": element["id"], "target": target, "relation": relation})
        if isinstance(element.get("target_player_id"), str):
            edges.append({"source": element["id"], "target": element["target_player_id"], "relation": "targets_player"})
    findings = validate_assignment_graph(design)
    gap_ownership = build_gap_ownership_map(design)
    coverage_shell = build_coverage_shell_map(design)
    player_assignments = build_player_assignment_summary(design)
    return {
        "version": str(design.get("assignment_model_version") or "1.0"),
        "nodes": nodes,
        "edges": edges,
        "findings": findings,
        "gap_ownership": gap_ownership,
        "coverage_shell": coverage_shell,
        "player_assignments": player_assignments,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "blocking_count": sum(1 for issue in findings if issue.get("severity", "error") == "error"),
            "warning_count": sum(1 for issue in findings if issue.get("severity") == "warning"),
        },
    }


def build_gap_ownership_map(design: dict[str, Any]) -> dict[str, Any]:
    """Build a renderer- and teaching-safe defensive gap ownership map.

    The map deliberately preserves conflicts instead of choosing a winner.
    That lets the canvas, validation panel, teaching view, and exports show
    unresolved ownership honestly while still displaying the authored path and
    responsibility for each owner.
    """
    raw_elements = design.get("elements") if isinstance(design.get("elements"), list) else []
    elements = [item for item in raw_elements if isinstance(item, dict)]
    ownership: dict[str, list[dict[str, Any]]] = {}
    declared = design.get("declared_gaps", design.get("gaps", []))
    declared_gaps = [str(item).strip() for item in declared if isinstance(item, str) and item.strip()] if isinstance(declared, list) else []
    for element in elements:
        if element.get("kind") not in {"fit", "rush", "block", "stunt", "rotation"}:
            continue
        gap = element.get("gap_owner") or element.get("fit_gap") or element.get("gap")
        if not isinstance(gap, str) or not gap.strip():
            continue
        gap = gap.strip()
        points = element.get("points") if isinstance(element.get("points"), list) else []
        ownership.setdefault(gap, []).append({
            "element_id": element.get("id"),
            "player_id": element.get("player_id"),
            "responsibility": element.get("responsibility") or element.get("fit_rule") or element.get("assignment"),
            "kind": element.get("kind"),
            "path": points,
            "exchange_with": element.get("exchange_with"),
        })
    for gap in declared_gaps:
        ownership.setdefault(gap, [])
    entries = []
    for gap in sorted(ownership):
        owners = ownership[gap]
        status = "unassigned" if not owners else "conflicted" if len(owners) > 1 else "assigned"
        entries.append({"gap": gap, "status": status, "owners": owners, "owner_count": len(owners)})
    return {
        "version": "1.0",
        "entries": entries,
        "assigned_count": sum(1 for item in entries if item["status"] == "assigned"),
        "unassigned_count": sum(1 for item in entries if item["status"] == "unassigned"),
        "conflicted_count": sum(1 for item in entries if item["status"] == "conflicted"),
        "status": "conflicted" if any(item["status"] == "conflicted" for item in entries) else "incomplete" if any(item["status"] == "unassigned" for item in entries) else "complete",
    }


def build_coverage_shell_map(design: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical coverage-zone and rotation responsibility map."""
    raw_elements = design.get("elements") if isinstance(design.get("elements"), list) else []
    elements = [item for item in raw_elements if isinstance(item, dict)]
    declared = design.get("coverage_zones", [])
    zones = [str(item).strip() for item in declared if isinstance(item, str) and item.strip()] if isinstance(declared, list) else []
    owners: dict[str, list[dict[str, Any]]] = {}
    for element in elements:
        if element.get("kind") not in {"coverage", "rotation"}:
            continue
        zone = element.get("rotation_to_zone") if element.get("kind") == "rotation" else element.get("zone")
        zone = zone or element.get("zone")
        if not isinstance(zone, str) or not zone.strip():
            continue
        zone = zone.strip()
        timing = element.get("timing") if isinstance(element.get("timing"), dict) else {}
        owners.setdefault(zone, []).append({
            "element_id": element.get("id"),
            "player_id": element.get("player_id"),
            "kind": element.get("kind"),
            "responsibility": element.get("responsibility") or element.get("assignment"),
            "rotation_sequence": element.get("rotation_sequence"),
            "rotation_trigger": element.get("rotation_trigger"),
            "vacated_zone": element.get("rotation_vacated_zone") or element.get("rotation_from_zone"),
            "replacement_player_id": element.get("rotation_replacement_player_id"),
            "exchange_with": element.get("exchange_with"),
            "path": element.get("points") if isinstance(element.get("points"), list) else element.get("path", []),
            "start_ms": timing.get("start_ms", element.get("start_ms", 0)),
            "end_ms": timing.get("end_ms", element.get("end_ms")),
        })
    for zone in zones:
        owners.setdefault(zone, [])
    entries = []
    for zone in sorted(owners):
        zone_owners = sorted(owners[zone], key=lambda item: (item.get("rotation_sequence") is None, item.get("rotation_sequence") or 0, str(item.get("element_id") or "")))
        entries.append({
            "zone": zone,
            "status": "unassigned" if not zone_owners else "conflicted" if len(zone_owners) > 1 else "assigned",
            "owner_count": len(zone_owners),
            "owners": zone_owners,
        })
    return {
        "version": "1.0",
        "entries": entries,
        "assigned_count": sum(1 for item in entries if item["status"] == "assigned"),
        "unassigned_count": sum(1 for item in entries if item["status"] == "unassigned"),
        "conflicted_count": sum(1 for item in entries if item["status"] == "conflicted"),
        "rotation_count": sum(1 for item in elements if item.get("kind") == "rotation"),
        "status": "conflicted" if any(item["status"] == "conflicted" for item in entries) else "incomplete" if any(item["status"] == "unassigned" for item in entries) else "complete",
    }


def build_player_assignment_summary(design: dict[str, Any]) -> dict[str, Any]:
    """Summarize authored assignment coverage for every player icon."""
    players = design.get("players") if isinstance(design.get("players"), list) else []
    elements = design.get("elements") if isinstance(design.get("elements"), list) else []
    by_player: dict[str, list[dict[str, Any]]] = {}
    for element in elements:
        if not isinstance(element, dict) or not isinstance(element.get("player_id"), str):
            continue
        by_player.setdefault(element["player_id"], []).append(element)
    entries = []
    for player in players:
        if not isinstance(player, dict) or not isinstance(player.get("id"), str):
            continue
        player_id = player["id"]
        assignments = by_player.get(player_id, [])
        entries.append({
            "player_id": player_id,
            "position": player.get("position") or player.get("role"),
            "assignment_count": len(assignments),
            "assignment_ids": [item.get("id") for item in assignments if item.get("id")],
            "kinds": sorted({str(item.get("kind")) for item in assignments if item.get("kind")}),
            "targets": sorted({str(item.get("target_player_id") or item.get("target_element_id") or item.get("block_target_element_id")) for item in assignments if item.get("target_player_id") or item.get("target_element_id") or item.get("block_target_element_id")}),
            "status": "assigned" if assignments else "unassigned",
        })
    return {
        "version": "1.0",
        "entries": entries,
        "assigned_count": sum(1 for item in entries if item["status"] == "assigned"),
        "unassigned_count": sum(1 for item in entries if item["status"] == "unassigned"),
        "status": "complete" if entries and all(item["status"] == "assigned" for item in entries) else "incomplete",
    }
