"""Authorized, non-diagnostic athlete-performance batch ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .athlete_performance import build_performance_observation


AUTHORIZED_SOURCE_KINDS = {"performance_log", "wearable_export", "practice_tracking", "coach_observation", "authorized_analytics"}
FORBIDDEN_MEDICAL_FIELDS = {"diagnosis", "diagnoses", "treatment", "medication", "clearance", "return_to_play"}


def _valid_timestamp(value: Any) -> bool:
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except (TypeError, ValueError):
        return False


def ingest_performance_batch(*, batch_id: str, organization_id: str, records: list[dict[str, Any]], source_manifest: dict[str, Any], actor: str) -> dict[str, Any]:
    issues: list[str] = []
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    if not batch_id.startswith("PERF-BATCH-"):
        issues.append("batch_id must start with PERF-BATCH-")
    if not organization_id.startswith("ORG-") or not actor:
        issues.append("organization_id and actor are required")
    if source_manifest.get("kind") not in AUTHORIZED_SOURCE_KINDS:
        issues.append("source_manifest kind is not authorized")
    if not source_manifest.get("ref") or not _valid_timestamp(source_manifest.get("captured_at")):
        issues.append("source_manifest ref and captured_at are required")
    for index, record in enumerate(records):
        record_issues: list[str] = []
        if record.get("organization_id") != organization_id:
            record_issues.append("organization scope mismatch")
        if FORBIDDEN_MEDICAL_FIELDS & set(record):
            record_issues.append("medical decision fields are not accepted by performance ingestion")
        if not _valid_timestamp(record.get("observed_at")):
            record_issues.append("observed_at must be an ISO timestamp")
        observation = build_performance_observation(observation_id=record.get("observation_id", ""), athlete_id=record.get("athlete_id", ""), session_type=record.get("session_type", ""), duration_minutes=record.get("duration_minutes", 0), repetitions=record.get("repetitions", 0), quality_score=record.get("quality_score", -1), season_phase=record.get("season_phase", ""), position=record.get("position", ""), source={"kind":source_manifest.get("kind", ""), "ref":source_manifest.get("ref", "")}, health_signal=bool(record.get("health_signal", False)))
        record_issues.extend(issue["message"] for issue in observation.get("issues", []))
        if record_issues:
            rejected.append({"index":index, "observation_id":record.get("observation_id"), "issues":record_issues})
        else:
            accepted.append({**observation, "organization_id":organization_id, "batch_id":batch_id, "observed_at":record["observed_at"], "ingested_by":actor, "privacy_scope":"organization", "staff_review_required":bool(record.get("health_signal", False))})
    status = "rejected" if not accepted and (issues or rejected) else "partial" if issues or rejected else "accepted"
    return {"id":batch_id, "organization_id":organization_id, "source_manifest":{"kind":source_manifest.get("kind"), "ref":source_manifest.get("ref"), "captured_at":source_manifest.get("captured_at")}, "accepted":accepted, "rejected":rejected, "batch_issues":issues, "accepted_count":len(accepted), "rejected_count":len(rejected), "status":status, "medical_decision_performed":False, "external_provider_called":False, "human_review_required":bool(rejected or any(item.get("staff_review_required") for item in accepted))}
