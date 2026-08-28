"""Approval-gated execution for managed-media retention candidates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .media_retention import plan_media_retention
from .tenant_repository import TenantRepository


def execute_media_retention(
    *,
    repository: TenantRepository,
    actor: str,
    actor_role: str,
    approval_ref: str | None,
    managed_root: str | Path,
    retention_days: int = 365,
    now: datetime | None = None,
    execute: bool = False,
    environment: str = "validation",
    production_implementation_allowed: bool = False,
) -> dict[str, Any]:
    """Plan or execute bounded owner-approved retention.

    Dry-run is the default. Unknown timestamps are never eligible, and only
    regular files beneath the explicitly supplied managed root are removed.
    """
    if not actor or actor_role != "program_owner":
        return {"status":"blocked", "blocker":"program_owner role is required", "execute_requested":execute, "deleted":[], "delete_performed":False}
    if execute and not approval_ref:
        return {"status":"blocked", "blocker":"approval_ref is required for retention execution", "execute_requested":True, "deleted":[], "delete_performed":False}
    if execute and environment == "production" and not production_implementation_allowed:
        return {"status":"blocked", "blocker":"production implementation is disabled by the Stage 0 control gate", "execute_requested":True, "deleted":[], "delete_performed":False}

    report = plan_media_retention(repository=repository, retention_days=retention_days, now=now)
    root = Path(managed_root).resolve()
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    for candidate in report["candidates"]:
        raw_path = candidate.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            rejected.append({**candidate, "reason":"managed path is missing"})
            continue
        path = Path(raw_path)
        resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
        if root not in resolved.parents or resolved == root or resolved.is_symlink() or not resolved.is_file():
            rejected.append({**candidate, "path":str(resolved), "reason":"path is not a regular file inside managed_root"})
            continue
        item = {**candidate, "path":str(resolved), "approval_ref":approval_ref, "action":"delete_managed_media"}
        candidates.append(item)
        if execute:
            try:
                resolved.unlink()
                deleted.append(item)
                current = repository.get("film_assets", candidate["asset_id"])
                if current:
                    repository.put("film_assets", candidate["asset_id"], {**current, "retention_status":"media_deleted", "retention_deleted_at":(now or datetime.now(timezone.utc)).isoformat(), "retention_approval_ref":approval_ref}, actor=actor, reason="approved_media_retention_execution")
            except OSError as exc:
                rejected.append({**item, "reason":str(exc)})
    return {"status":"executed" if execute and not rejected else ("partial_failure" if execute and rejected else "planned"), "organization_id":repository.organization_id, "environment":environment, "retention_days":retention_days, "approval_ref":approval_ref, "execute_requested":execute, "candidates":candidates, "rejected":rejected, "deleted":deleted, "delete_performed":bool(deleted), "human_approval_required":True, "production_implementation_allowed":production_implementation_allowed, "external_state_changed":False}
