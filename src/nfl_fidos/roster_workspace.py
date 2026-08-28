"""Organization-scoped roster, personnel, and depth-chart workspace."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


VALID_POSITIONS = {"QB", "RB", "FB", "WR", "TE", "OL", "C", "G", "T", "DL", "DT", "DE", "EDGE", "LB", "ILB", "OLB", "DB", "CB", "S", "NB", "K", "P", "LS", "ATH"}
VALID_STATUSES = {"active", "inactive", "injured", "practice_squad", "reserve", "released"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def create_roster_player(*, player_id: str, organization_id: str, display_name: str, position: str, position_group: str, jersey_number: str | None, aliases: list[str], eligibility: list[str], role_groups: list[str], status: str, availability: str, owner: str, source_refs: list[str], actor: str) -> dict[str, Any]:
    issues: list[str] = []
    position = position.upper().strip()
    status = status.lower().strip()
    if not player_id.startswith("PLAYER-"):
        issues.append("player id must start with PLAYER-")
    if not display_name.strip() or position not in VALID_POSITIONS or not position_group.strip():
        issues.append("display name, valid position, and position group are required")
    if status not in VALID_STATUSES:
        issues.append(f"status must be one of {sorted(VALID_STATUSES)}")
    if not owner or not source_refs:
        issues.append("owner and source references are required")
    record = {"id": player_id, "organization_id": organization_id, "display_name": display_name.strip(), "position": position, "position_group": position_group.strip(), "jersey_number": jersey_number, "aliases": aliases, "eligibility": eligibility, "role_groups": role_groups, "status": status if not issues else "invalid", "availability": availability.strip(), "owner": owner, "source_refs": source_refs, "created_at": _now(), "issues": issues, "human_review_required": False}
    return record


def save_depth_chart(*, repository: TenantRepository, depth_chart_id: str, unit: str, position: str, slots: list[dict[str, Any]], season: str, week: str | None, actor: str) -> dict[str, Any]:
    issues: list[str] = []
    position = position.upper().strip()
    if not depth_chart_id.startswith("DEPTH-"):
        issues.append("depth chart id must start with DEPTH-")
    if not unit.strip() or position not in VALID_POSITIONS or not season.strip() or not slots:
        issues.append("unit, valid position, season, and at least one slot are required")
    player_ids = [str(slot.get("player_id")) for slot in slots]
    if any(repository.get("roster_players", player_id) is None for player_id in player_ids):
        issues.append("every depth-chart player must exist in the organization roster")
    if len(player_ids) != len(set(player_ids)):
        issues.append("a player may appear only once at a position")
    normalized_slots = [{"rank": int(slot.get("rank", index + 1)), "player_id": player_id, "role": str(slot.get("role") or "starter" if index == 0 else slot.get("role") or "reserve")} for index, (slot, player_id) in enumerate(zip(slots, player_ids))]
    return {"id": depth_chart_id, "organization_id": repository.organization_id, "unit": unit.strip(), "position": position, "season": season.strip(), "week": week, "slots": normalized_slots, "status": "ready" if not issues else "invalid", "issues": issues, "updated_at": _now(), "updated_by": actor}


def save_personnel_package(*, repository: TenantRepository, package_id: str, name: str, unit: str, roles: list[str], player_ids: list[str], season: str, actor: str) -> dict[str, Any]:
    issues: list[str] = []
    if not package_id.startswith("PERSONNEL-"):
        issues.append("personnel package id must start with PERSONNEL-")
    if not name.strip() or not unit.strip() or not roles or not season.strip():
        issues.append("name, unit, roles, and season are required")
    missing = [player_id for player_id in player_ids if repository.get("roster_players", player_id) is None]
    if missing:
        issues.append(f"unknown roster players: {', '.join(missing)}")
    return {"id": package_id, "organization_id": repository.organization_id, "name": name.strip(), "unit": unit.strip(), "roles": roles, "player_ids": player_ids, "season": season.strip(), "status": "ready" if not issues else "invalid", "issues": issues, "updated_at": _now(), "updated_by": actor}


def build_roster_workspace(*, repository: TenantRepository, role: str = "program_owner", actor: str | None = None, position_group: str | None = None, status: str | None = None, search: str | None = None) -> dict[str, Any]:
    players = repository.list("roster_players")
    if role == "player" and actor:
        players = [player for player in players if actor in {player.get("id"), player.get("player_id"), player.get("owner")}]
    normalized_group = position_group.strip().lower() if position_group else None
    needle = search.strip().lower() if search else None
    if normalized_group:
        players = [player for player in players if str(player.get("position_group", "")).lower() == normalized_group or str(player.get("position", "")).lower() == normalized_group]
    if status:
        players = [player for player in players if player.get("status") == status]
    if needle:
        players = [player for player in players if needle in str(player).lower()]
    depth_charts = repository.list("depth_charts")
    packages = repository.list("personnel_packages")
    if role == "player" and actor:
        depth_charts = [chart for chart in depth_charts if any(slot.get("player_id") == actor for slot in chart.get("slots", []))]
        packages = [package for package in packages if actor in package.get("player_ids", [])]
    return {"organization_id": repository.organization_id, "status": "ready" if players or depth_charts or packages else "empty", "players": sorted(players, key=lambda player: (player.get("position_group", ""), player.get("display_name", ""))), "depth_charts": sorted(depth_charts, key=lambda chart: (chart.get("unit", ""), chart.get("position", ""))), "personnel_packages": sorted(packages, key=lambda package: package.get("name", "")), "position_groups": sorted({player.get("position_group") for player in repository.list("roster_players") if player.get("position_group")}), "counts": {"players": len(players), "active": sum(1 for player in players if player.get("status") == "active"), "depth_charts": len(depth_charts), "personnel_packages": len(packages)}, "human_review_required": True, "privacy_boundary": "Roster records are organization-scoped; player-facing views must be filtered to the signed-in player and approved role groups."}
