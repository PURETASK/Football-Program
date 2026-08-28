"""Tenant-scoped visual playbook storage and deterministic role rendering."""

from __future__ import annotations

from typing import Any

from .tenant_repository import TenantRepository
from .visual_playbook import validate_visual_play
from .visual_playbook import simulate_what_if
from .visual_render import render_visual_svg


class VisualWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def save_visual(self, visual: dict[str, Any], *, actor: str) -> dict[str, Any]:
        if not visual.get("id") or not visual["id"].startswith("VISUAL-"):
            raise ValueError("visual id must start with VISUAL-")
        record = dict(visual)
        record["organization_id"] = self.repository.organization_id
        issues = validate_visual_play(record)
        record["status"] = "renderable" if not issues else "invalid"
        record["issues"] = issues
        if issues:
            return record
        return self.repository.put("visual_plays", record["id"], record, actor=actor, reason="visual_play_saved")

    def get_visual(self, visual_id: str, *, role: str | None = None) -> dict[str, Any]:
        visual = self.repository.get("visual_plays", visual_id)
        if visual is None:
            raise KeyError(f"Unknown visual play: {visual_id}")
        return {"visual": visual, "role": role or "coach", "svg": render_visual_svg(visual=visual, role=role)}

    def list_visuals(self, *, play_id: str | None = None) -> list[dict[str, Any]]:
        visuals = self.repository.list("visual_plays")
        if play_id:
            visuals = [visual for visual in visuals if visual.get("play_id") == play_id]
        return sorted(visuals, key=lambda visual: visual.get("id", ""))

    def create_what_if(self, *, visual_id: str, simulation_id: str, adjustment: dict[str, Any], requester_role: str, actor: str) -> dict[str, Any]:
        visual = self.repository.get("visual_plays", visual_id)
        if visual is None:
            raise KeyError(f"Unknown visual play: {visual_id}")
        scenario = simulate_what_if(simulation_id=simulation_id, canonical_visual=visual, adjustment=adjustment, requester_role=requester_role)
        scenario["organization_id"] = self.repository.organization_id
        if scenario.get("status") == "scenario_ready":
            return self.repository.put("visual_scenarios", simulation_id, scenario, actor=actor, reason="visual_what_if_created")
        return scenario
