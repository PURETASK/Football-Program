"""Non-destructive media retention planning with explicit human review."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def plan_media_retention(*, repository: TenantRepository, retention_days: int = 365, now: datetime | None = None) -> dict[str, Any]:
    if retention_days <= 0:
        raise ValueError("retention_days must be positive")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    candidates: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    for asset in repository.list("film_assets"):
        managed = asset.get("managed_storage", {})
        captured = _parse_timestamp(asset.get("captured_at"))
        item = {"asset_id":asset.get("id"), "path":managed.get("destination_path") or asset.get("uri"), "captured_at":asset.get("captured_at"), "organization_id":repository.organization_id}
        if captured is None:
            unknown.append({**item, "reason":"captured_at is missing or invalid", "action":"retain_until_review"})
            continue
        age_days = (reference - captured).total_seconds() / 86400
        item["age_days"] = round(age_days, 2)
        if age_days >= retention_days:
            candidates.append({**item, "action":"review_for_retention", "destructive_action_required":True})
        else:
            retained.append({**item, "action":"retain"})
    return {"status":"review_required" if candidates or unknown else "current", "organization_id":repository.organization_id, "retention_days":retention_days, "as_of":reference.isoformat(), "candidates":candidates, "retained":retained, "unknown":unknown, "destructive_action_required":bool(candidates), "human_approval_required":bool(candidates or unknown), "delete_performed":False}
