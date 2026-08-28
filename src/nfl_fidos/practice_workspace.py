"""Coach-facing persisted practice builder workspace."""

from __future__ import annotations

from typing import Any

from .practice_architecture import build_practice_architecture
from .practice_resources import plan_practice_resources
from .tenant_repository import TenantRepository


class PracticeWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def create_plan(self, *, practice_id: str, team_context: str, season_phase: str, week_context: str, objective: str, opponent_priorities: list[str], periods: list[dict[str, Any]], staff_available: list[str], facility_constraints: list[str], load_controls: dict[str, Any], restrictions: list[dict[str, Any]], actor: str, roster_ids: list[str] | None = None, install_items: list[dict[str, Any]] | None = None, attendance_policy: str | None = None, practice_card_preferences: dict[str, Any] | None = None, resource_schedule: dict[str, Any] | None = None, resource_availability: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        practice = build_practice_architecture(practice_id=practice_id, team_context=team_context, season_phase=season_phase, week_context=week_context, objective=objective, opponent_priorities=opponent_priorities, periods=periods, staff_available=staff_available, facility_constraints=facility_constraints, load_controls=load_controls, restrictions=restrictions)
        practice["organization_id"] = self.repository.organization_id
        practice.update({"roster_ids": roster_ids or [], "install_items": install_items or [], "attendance_policy": attendance_policy or "staff_recorded", "practice_card_preferences": practice_card_preferences or {}})
        if resource_schedule is not None:
            resource_plan = plan_practice_resources(organization_id=self.repository.organization_id, practice_id=practice_id, schedule=resource_schedule, availability=resource_availability or [])
            practice["resource_plan"] = resource_plan
            if resource_plan["status"] != "ready":
                practice["status"] = "blocked"
                practice["issues"] = list(practice.get("issues", [])) + [{"code":"PRACTICE-RESOURCE-BLOCKED", "message":"Facility or staff resource schedule is not feasible", "path":"resource_plan"}]
        if practice["status"] == "draft":
            return self.repository.put("practice_plans", practice_id, practice, actor=actor, reason="practice_plan_created")
        return practice

    def workspace(self, *, week: str | None = None) -> dict[str, Any]:
        plans = self.repository.list("practice_plans")
        if week:
            plans = [plan for plan in plans if plan.get("week_context") == week]
        return {"organization_id":self.repository.organization_id, "status":"ready" if plans else "empty", "week":week, "plans":plans, "load_exceeded":sum(1 for plan in plans if any(issue.get("code") == "PRACTICE-LOAD-EXCEEDED" for issue in plan.get("issues", []))), "human_review_required":bool(plans)}
