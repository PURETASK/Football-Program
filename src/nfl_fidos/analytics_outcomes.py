"""Structured intended-versus-actual outcome records for the analytics loop."""

from __future__ import annotations

from typing import Any

from .analytics_dictionary import _wilson_interval
from .tenant_repository import TenantRepository

OUTCOME_RESULTS = {"success", "partial", "failure", "neutral", "not_scored"}


def _confidence(denominator: int) -> str:
    return "low" if denominator < 10 else "moderate" if denominator < 30 else "high"


def build_outcome_observation(
    *,
    outcome_id: str,
    organization_id: str,
    intended_record_type: str,
    intended_record_id: str,
    actual_result: str,
    success_count: int,
    sample_size: int,
    context: dict[str, Any],
    evidence_refs: list[str],
    recorded_by: str,
    linked_play_id: str | None = None,
    linked_assignment_id: str | None = None,
    teaching_step_id: str | None = None,
    responsibility_phase: str | None = None,
    practice_id: str | None = None,
    film_observation_ids: list[str] | None = None,
    game_plan_id: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    result = actual_result.strip().lower()
    if not outcome_id.startswith("OUTCOME-"):
        issues.append({"code": "OUTCOME-ID", "message": "outcome id must start with OUTCOME-", "path": "outcome_id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "OUTCOME-ORG", "message": "organization id must start with ORG-", "path": "organization_id"})
    if not intended_record_type.strip() or not intended_record_id.strip():
        issues.append({"code": "OUTCOME-INTENT", "message": "intended record type and id are required", "path": "intended_record"})
    if result not in OUTCOME_RESULTS:
        issues.append({"code": "OUTCOME-RESULT", "message": f"actual result must be one of {sorted(OUTCOME_RESULTS)}", "path": "actual_result"})
    valid_sample = isinstance(sample_size, int) and not isinstance(sample_size, bool) and sample_size > 0
    if not valid_sample:
        issues.append({"code": "OUTCOME-SAMPLE", "message": "sample size must be a positive integer", "path": "sample_size"})
    valid_success = isinstance(success_count, int) and not isinstance(success_count, bool) and success_count >= 0 and valid_sample and success_count <= sample_size
    if not valid_success:
        issues.append({"code": "OUTCOME-SUCCESS-BOUNDS", "message": "success count must be between zero and sample size", "path": "success_count"})
    if not context:
        issues.append({"code": "OUTCOME-CONTEXT", "message": "football context is required", "path": "context"})
    if not evidence_refs:
        issues.append({"code": "OUTCOME-EVIDENCE", "message": "at least one evidence reference is required", "path": "evidence_refs"})
    if not recorded_by.strip():
        issues.append({"code": "OUTCOME-RECORDER", "message": "recorded_by is required", "path": "recorded_by"})
    interval = _wilson_interval(success_count, sample_size) if valid_success else (None, None)
    return {
        "id": outcome_id,
        "organization_id": organization_id,
        "intended_record_type": intended_record_type.strip(),
        "intended_record_id": intended_record_id.strip(),
        "actual_result": result,
        "success_count": success_count,
        "sample_size": sample_size,
        "success_rate": success_count / sample_size if valid_success else None,
        "confidence": _confidence(sample_size) if valid_sample else "unrated",
        "uncertainty": {"method": "wilson_95_percent", "interval": interval},
        "context": context,
        "evidence_refs": evidence_refs,
        "linked_play_id": linked_play_id,
        "linked_assignment_id": linked_assignment_id,
        "teaching_step_id": teaching_step_id,
        "responsibility_phase": responsibility_phase,
        "practice_id": practice_id,
        "film_observation_ids": film_observation_ids or [],
        "game_plan_id": game_plan_id,
        "notes": notes.strip(),
        "recorded_by": recorded_by.strip(),
        "status": "recorded" if not issues else "invalid",
        "issues": issues,
        "human_review_required": result in {"failure", "partial", "not_scored"} or (valid_sample and sample_size < 10),
        "generalization_allowed": valid_sample and sample_size >= 10,
    }


class AnalyticsOutcomeService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def record(self, **values: Any) -> dict[str, Any]:
        record = build_outcome_observation(organization_id=self.repository.organization_id, **values)
        if record["issues"]:
            return record
        return self.repository.put("outcome_observations", record["id"], record, actor=record["recorded_by"], reason="analytics_outcome_recorded")

    def workspace(self, *, intended_record_id: str | None = None) -> dict[str, Any]:
        records = self.repository.list("outcome_observations")
        if intended_record_id:
            records = [record for record in records if record.get("intended_record_id") == intended_record_id]
        phase_buckets: dict[str, dict[str, Any]] = {}
        for record in records:
            context = record.get("context") if isinstance(record.get("context"), dict) else {}
            phase = str(record.get("responsibility_phase") or context.get("responsibility_phase") or "general").strip().lower() or "general"
            bucket = phase_buckets.setdefault(phase, {
                "phase": phase,
                "record_count": 0,
                "success_count": 0,
                "sample_size": 0,
                "human_review_required": False,
                "linked_assignment_ids": set(),
                "teaching_step_ids": set(),
                "linked_play_ids": set(),
            })
            bucket["record_count"] += 1
            bucket["success_count"] += int(record.get("success_count") or 0)
            bucket["sample_size"] += int(record.get("sample_size") or 0)
            bucket["human_review_required"] = bucket["human_review_required"] or bool(record.get("human_review_required"))
            for field in ("linked_assignment_id", "teaching_step_id", "linked_play_id"):
                value = record.get(field)
                if value:
                    bucket[f"{field}s" if field != "linked_play_id" else "linked_play_ids"].add(str(value))
        phase_summary = []
        for phase in sorted(phase_buckets):
            bucket = phase_buckets[phase]
            sample_size = bucket["sample_size"]
            phase_summary.append({
                **bucket,
                "success_rate": bucket["success_count"] / sample_size if sample_size else None,
                "confidence": _confidence(sample_size) if sample_size else "unrated",
                "linked_assignment_ids": sorted(bucket["linked_assignment_ids"]),
                "teaching_step_ids": sorted(bucket["teaching_step_ids"]),
                "linked_play_ids": sorted(bucket["linked_play_ids"]),
            })
            phase_summary[-1].pop("linked_assignments", None)
        return {
            "organization_id": self.repository.organization_id,
            "records": records,
            "total": len(records),
            "result_counts": {result: sum(1 for record in records if record.get("actual_result") == result) for result in sorted(OUTCOME_RESULTS)},
            "sample_size": sum(int(record.get("sample_size") or 0) for record in records),
            "human_review_required": any(record.get("human_review_required") for record in records),
            "responsibility_phase_summary": phase_summary,
            "production_implementation_allowed": False,
        }
