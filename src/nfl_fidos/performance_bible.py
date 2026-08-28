"""Stage 13 performance-domain, position-demand, and bounded support contracts."""

from __future__ import annotations

from typing import Any


REQUIRED_DOMAINS = {"strength", "power", "acceleration", "max_velocity", "change_of_direction", "conditioning", "mobility", "workload", "recovery", "sleep", "hydration", "nutrition_support"}
BOUNDARIES = ["No diagnosis, injury determination, treatment, medication, or return-to-play decision", "Qualified performance and medical staff own health-related decisions", "Health signals trigger escalation and never automated intervention"]


def validate_performance_bible(bible: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not REQUIRED_DOMAINS.issubset(set(bible.get("domains", []))):
        issues.append("all performance domains are required")
    profiles = bible.get("position_demand_profiles", [])
    if not profiles:
        issues.append("position demand profiles are required")
    for profile in profiles:
        for field in ("position", "demands", "measures", "cautions"):
            if not profile.get(field):
                issues.append(f"{profile.get('position', '<unknown>')}: missing {field}")
    if not all(boundary in bible.get("support_boundaries", []) for boundary in BOUNDARIES[:2]):
        issues.append("professional safety boundaries are required")
    return {"bible_id":bible.get("bible_id"), "status":"valid" if not issues else "invalid", "errors":issues, "profile_count":len(profiles), "domain_count":len(bible.get("domains", []))}


def build_performance_support_plan(*, plan_id: str, athlete_id: str, position: str, season_phase: str, week_context: str, objectives: list[dict[str, Any]], load_context: dict[str, Any], recovery_context: dict[str, Any], source: dict[str, str], reviewer: str) -> dict[str, Any]:
    """Create an auditable performance-support plan with explicit professional boundaries."""
    issues: list[dict[str, str]] = []
    if not plan_id.startswith("PERF-PLAN-") or not athlete_id or not position or not season_phase or not week_context:
        issues.append({"code":"PERF-PLAN-CONTEXT", "message":"Plan, athlete, position, season, and week context are required", "path":"context"})
    if not objectives or not load_context or not recovery_context or not source.get("kind") or not source.get("ref") or not reviewer:
        issues.append({"code":"PERF-PLAN-EVIDENCE", "message":"Objectives, load/recovery context, source, and reviewer are required", "path":"evidence"})
    forbidden = {"diagnose", "diagnosis", "treatment", "medication", "return_to_play", "clearance"}
    requested_terms = {str(objective.get("type", "")).lower() for objective in objectives} | {str(objective.get("recommendation", "")).lower() for objective in objectives}
    if requested_terms & forbidden:
        issues.append({"code":"PERF-PLAN-BOUNDARY", "message":"Medical or clearance decisions must be escalated to qualified staff", "path":"objectives"})
    return {"id":plan_id, "athlete_id":athlete_id, "position":position, "context":{"season_phase":season_phase,"week_context":week_context}, "objectives":objectives, "load_context":load_context, "recovery_context":recovery_context, "source":source, "reviewer":reviewer, "boundaries":BOUNDARIES, "staff_escalation_required":bool(issues) or any(recovery_context.get(key) for key in ("health_signal", "pain_signal", "illness_signal")), "status":"rejected" if issues else "under_review", "issues":issues}
