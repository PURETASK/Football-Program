"""Roster-linked practice attendance and participation summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository

ATTENDANCE_STATUSES = {"present", "absent", "limited", "late", "excused"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_attendance_record(
    *,
    attendance_id: str,
    organization_id: str,
    practice_id: str,
    player_id: str,
    status: str,
    recorded_by: str,
    recorded_at: str | None = None,
    period_ids: list[str] | None = None,
    minutes_available: int | None = None,
    note: str = "",
    source_refs: list[str] | None = None,
    roster_player: dict[str, Any] | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    normalized_status = status.strip().lower()
    if not attendance_id.startswith("ATTENDANCE-"):
        issues.append("attendance id must start with ATTENDANCE-")
    if not organization_id.startswith("ORG-"):
        issues.append("organization id must start with ORG-")
    if not practice_id.startswith("PRACTICE-"):
        issues.append("practice id must start with PRACTICE-")
    if not player_id.startswith("PLAYER-"):
        issues.append("player id must start with PLAYER-")
    if normalized_status not in ATTENDANCE_STATUSES:
        issues.append(f"status must be one of {sorted(ATTENDANCE_STATUSES)}")
    if not recorded_by.strip():
        issues.append("recorded_by is required")
    if minutes_available is not None and (isinstance(minutes_available, bool) or int(minutes_available) < 0):
        issues.append("minutes_available must be a non-negative integer")
    if roster_player is None:
        issues.append("player must exist in the organization roster")
    record = {
        "id": attendance_id,
        "organization_id": organization_id,
        "practice_id": practice_id,
        "player_id": player_id,
        "player_name": roster_player.get("display_name") if roster_player else None,
        "position": roster_player.get("position") if roster_player else None,
        "position_group": roster_player.get("position_group") if roster_player else None,
        "status": normalized_status if not issues else "invalid",
        "recorded_by": recorded_by.strip(),
        "recorded_at": recorded_at or _now(),
        "period_ids": period_ids or [],
        "minutes_available": int(minutes_available) if minutes_available is not None else None,
        "note": note.strip(),
        "source_refs": source_refs or [],
        "issues": issues,
        "human_review_required": normalized_status in {"absent", "limited"},
    }
    return record


class PracticeAttendanceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def record(
        self,
        *,
        attendance_id: str,
        practice_id: str,
        player_id: str,
        status: str,
        recorded_by: str,
        recorded_at: str | None = None,
        period_ids: list[str] | None = None,
        minutes_available: int | None = None,
        note: str = "",
        source_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        practice = self.repository.get("practice_plans", practice_id)
        if practice is None:
            return {"id": attendance_id, "status": "invalid", "issues": ["practice plan must exist in the organization"], "organization_id": self.repository.organization_id}
        player = self.repository.get("roster_players", player_id)
        record = build_attendance_record(
            attendance_id=attendance_id,
            organization_id=self.repository.organization_id,
            practice_id=practice_id,
            player_id=player_id,
            status=status,
            recorded_by=recorded_by,
            recorded_at=recorded_at,
            period_ids=period_ids,
            minutes_available=minutes_available,
            note=note,
            source_refs=source_refs,
            roster_player=player,
        )
        if record["issues"]:
            return record
        return self.repository.put("practice_attendance", attendance_id, record, actor=recorded_by, reason="practice_attendance_recorded")

    def workspace(self, *, practice_id: str | None = None) -> dict[str, Any]:
        records = self.repository.list("practice_attendance")
        if practice_id:
            records = [record for record in records if record.get("practice_id") == practice_id]
        counts = {status: sum(1 for record in records if record.get("status") == status) for status in sorted(ATTENDANCE_STATUSES)}
        return {
            "organization_id": self.repository.organization_id,
            "practice_id": practice_id,
            "records": sorted(records, key=lambda record: (record.get("recorded_at") or "", record.get("player_name") or ""), reverse=True),
            "counts": counts,
            "total": len(records),
            "limited_or_absent": [record for record in records if record.get("status") in {"absent", "limited"}],
            "human_review_required": any(record.get("human_review_required") for record in records),
            "production_implementation_allowed": False,
        }
