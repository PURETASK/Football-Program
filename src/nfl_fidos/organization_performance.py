"""Tenant-scoped non-diagnostic performance review package."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .athlete_performance import build_readiness_summary
from .performance_ingestion import ingest_performance_batch


def build_organization_performance(*, package_id: str, organization_id: str, season: str, batch_id: str, records: list[dict[str, Any]], source_manifest: dict[str, Any], readiness_summaries: list[dict[str, Any]], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-PERFORMANCE-"):
        issues.append({"code": "ORG-PERF-ID", "message": "Package id must use ORG-PERFORMANCE- prefix", "path": "id"})
    if not organization_id.startswith("ORG-") or not season or not batch_id or not compiler:
        issues.append({"code": "ORG-PERF-METADATA", "message": "organization, season, batch, and compiler are required", "path": "metadata"})
    result = ingest_performance_batch(batch_id=batch_id, organization_id=organization_id, records=records, source_manifest=source_manifest, actor=compiler)
    if not result.get("accepted"):
        issues.append({"code": "ORG-PERF-OBSERVATIONS", "message": "At least one valid performance observation is required", "path": "records"})
    if result.get("status") == "rejected":
        issues.extend({"code": "ORG-PERF-BATCH", "message": issue, "path": "batch"} for issue in result.get("batch_issues", []))
    observation_by_athlete: dict[str, list[dict[str, Any]]] = {}
    for observation in result.get("accepted", []):
        observation_by_athlete.setdefault(observation["athlete_id"], []).append(observation)
    summaries: list[dict[str, Any]] = []
    for index, summary in enumerate(readiness_summaries):
        athlete_id = summary.get("athlete_id", "")
        built = build_readiness_summary(summary_id=summary.get("summary_id", f"READINESS-{package_id.removeprefix('ORG-PERFORMANCE-')}-{index + 1:03d}"), athlete_id=athlete_id, observations=observation_by_athlete.get(athlete_id, []), signals=summary.get("signals", []))
        summaries.append(built)
        if built.get("issues"):
            issues.extend({"code": item["code"], "message": item["message"], "path": f"readiness_summaries[{index}]"} for item in built["issues"])
    return {"id": package_id, "organization_id": organization_id, "season": season, "batch_id": batch_id, "source_manifest": result.get("source_manifest"), "observations": result.get("accepted", []), "rejected_observations": result.get("rejected", []), "readiness_summaries": summaries, "compiler": compiler, "status": "under_review" if not issues else "rejected", "human_review_required": True, "medical_decision_performed": False, "external_provider_called": False, "external_state_changed": False, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": issues, "production_implementation_allowed": False, "stage_advance_authorized": False}


def approve_organization_performance(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code": "ORG-PERF-STATE", "message": "Only an under_review package can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-PERF-ROLE", "message": "Only a program_owner may validate performance packages", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-PERF-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
