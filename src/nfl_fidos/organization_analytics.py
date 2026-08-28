"""Tenant-scoped analytics observations and reviewable reports."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .analytics_dictionary import build_analytics_report, calculate_metric


def build_organization_analytics_package(*, package_id: str, organization_id: str, season: str, source_refs: list[str], observations: list[dict[str, Any]], reports: list[dict[str, Any]], analyst: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-ANALYTICS-"):
        issues.append({"code": "ORG-ANALYTICS-ID", "message": "Package id must use ORG-ANALYTICS- prefix", "path": "id"})
    if not organization_id.startswith("ORG-") or not season or not analyst:
        issues.append({"code": "ORG-ANALYTICS-METADATA", "message": "organization, season, and analyst are required", "path": "metadata"})
    if not source_refs:
        issues.append({"code": "ORG-ANALYTICS-SOURCE", "message": "source_refs are required", "path": "source_refs"})
    if not observations or not reports:
        issues.append({"code": "ORG-ANALYTICS-EMPTY", "message": "At least one observation and report are required", "path": "observations"})
    observation_results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, observation in enumerate(observations):
        observation_id = observation.get("observation_id", f"METRIC-OBS-{package_id.removeprefix('ORG-ANALYTICS-')}-{index + 1:03d}")
        if observation_id in seen:
            issues.append({"code": "ORG-ANALYTICS-DUPLICATE", "message": "Duplicate observation id", "path": f"observations[{index}].observation_id"})
        seen.add(observation_id)
        source_ref = observation.get("source_ref", source_refs[0] if source_refs else "")
        if source_ref not in source_refs:
            issues.append({"code": "ORG-ANALYTICS-SOURCE-LINK", "message": "Observation source_ref must be listed in package source_refs", "path": f"observations[{index}].source_ref"})
        try:
            result = calculate_metric(definition=observation["definition"], numerator=observation["numerator"], denominator=observation["denominator"], context=observation["context"], source={"kind": observation.get("source_kind", "approved_export"), "ref": source_ref}, observation_ids=observation["observation_ids"])
        except (KeyError, TypeError, ValueError) as exc:
            result = {"id": observation_id, "status": "invalid", "issues": [{"code": "ORG-ANALYTICS-CALC", "message": str(exc), "path": f"observations[{index}]"}]}
        result["id"] = observation_id
        result["organization_id"] = organization_id
        result["season"] = season
        observation_results.append(result)
        if result.get("status") != "valid":
            issues.extend({"code": item.get("code", "ORG-ANALYTICS-OBS"), "message": item.get("message", "Observation is invalid"), "path": f"observations[{index}].{item.get('path', '')}"} for item in result.get("issues", []))
    by_id = {item.get("id"): item for item in observation_results}
    report_results: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        selected = [by_id.get(item_id) for item_id in report.get("observation_ids", [])]
        if any(item is None for item in selected):
            issues.append({"code": "ORG-ANALYTICS-REPORT-LINK", "message": "Report references an unknown observation", "path": f"reports[{index}].observation_ids"})
            selected = [item for item in selected if item is not None]
        result = build_analytics_report(report_id=report.get("id", ""), audience=report.get("audience", ""), metric_observations=selected, context=report.get("context", {}), caveats=report.get("caveats", []), analyst=analyst)
        result["organization_id"] = organization_id
        result["season"] = season
        report_results.append(result)
        if result.get("status") != "draft":
            issues.extend({"code": "ORG-ANALYTICS-REPORT", "message": error, "path": f"reports[{index}]"} for error in result.get("issues", []))
    return {"id": package_id, "organization_id": organization_id, "season": season, "source_refs": list(source_refs), "observations": observation_results, "reports": report_results, "analyst": analyst, "status": "under_review" if not issues else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_analytics_package(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-ANALYTICS-STATE", "message": "Only an under_review analytics package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-ANALYTICS-ROLE", "message": "Only a program_owner may validate organization analytics", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-ANALYTICS-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
