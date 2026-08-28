"""Game-plan release snapshots and approval boundaries.

The release room deliberately stores a frozen snapshot instead of mutating the
weekly plan.  A later change must produce a new snapshot, which makes rollback
and "what changed" reviewable without pretending that a release is a live
editable document.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import re

from .tenant_repository import TenantRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _week(record: dict[str, Any]) -> str | None:
    return record.get("week") or record.get("week_context")


def _changed_keys(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[str]:
    if not previous:
        return ["initial release"]
    ignored = {"_saved_at", "created_at", "updated_at"}
    return sorted(key for key in set(previous) | set(current) if key not in ignored and previous.get(key) != current.get(key))


_REFERENCE_PATTERN = re.compile(r"^(?:PLAY|PLAYLIST|FILM|SCOUT|PRACTICE|DRILL|ROSTER|PLAYER|DELIVERY|GAMEPLAN|SOURCE|RELEASE|VISUAL|QUIZ|ASSIGNMENT|PERSONNEL|DEPTH|OBS|ANALYTICS|METRIC|RULE)-[A-Z0-9_-]+$", re.IGNORECASE)
_DEPENDENCY_COLLECTIONS = (
    "play_designs", "play_design_versions", "film_assets", "film_clips", "film_observations", "film_playlists",
    "scouting_reports", "practice_plans", "drills", "player_assignments", "delivery_tasks", "analytics_reports",
    "metric_observations", "rule_recommendations", "release_candidates", "sources", "roster_players", "personnel_packages",
)


def _collect_reference_ids(value: Any) -> set[str]:
    references: set[str] = set()
    if isinstance(value, str):
        if _REFERENCE_PATTERN.match(value.strip()):
            references.add(value.strip())
    elif isinstance(value, list):
        for item in value:
            references.update(_collect_reference_ids(item))
    elif isinstance(value, dict):
        for item in value.values():
            references.update(_collect_reference_ids(item))
    return references


def _build_dependency_manifest(*, repository: TenantRepository, plan: dict[str, Any], explicit_refs: list[str] | None) -> dict[str, Any]:
    references = _collect_reference_ids(plan)
    references.discard(str(plan.get("id", "")))
    references.update(reference.strip() for reference in (explicit_refs or []) if isinstance(reference, str) and reference.strip())
    records_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection in _DEPENDENCY_COLLECTIONS:
        for record in repository.list(collection):
            record_id = str(record.get("id", ""))
            if record_id:
                records_by_id.setdefault(record_id, (collection, record))
    artifacts = []
    for reference in sorted(references):
        collection_record = records_by_id.get(reference)
        if collection_record is None:
            artifacts.append({"id": reference, "status": "unresolved", "collection": None, "checksum": None, "version": None})
            continue
        collection, record = collection_record
        artifacts.append({
            "id": reference,
            "status": "linked",
            "collection": collection,
            "checksum": _hash(record),
            "version": record.get("version") or record.get("renderer_version") or record.get("_revision"),
        })
    linked = sum(1 for artifact in artifacts if artifact["status"] == "linked")
    unresolved = [artifact["id"] for artifact in artifacts if artifact["status"] == "unresolved"]
    return {"status": "ready" if not unresolved else "needs_review", "artifacts": artifacts, "linked_count": linked, "unresolved_refs": unresolved, "artifact_count": len(artifacts)}


def build_release_room(*, repository: TenantRepository, week: str | None = None) -> dict[str, Any]:
    plans = repository.list("game_plans")
    if week:
        plans = [plan for plan in plans if _week(plan) == week]
    snapshots = repository.list("game_plan_release_snapshots")
    if week:
        snapshots = [snapshot for snapshot in snapshots if snapshot.get("week") == week]
    snapshots.sort(key=lambda record: record.get("created_at") or record.get("_saved_at") or "", reverse=True)
    latest = snapshots[0] if snapshots else None
    return {
        "organization_id": repository.organization_id,
        "status": "ready" if plans or snapshots else "empty",
        "week": week,
        "plans": plans,
        "snapshots": snapshots,
        "latest_snapshot": latest,
        "pending_approval_count": sum(1 for item in snapshots if item.get("status") == "pending_approval"),
        "locked_count": sum(1 for item in snapshots if item.get("locked")),
        "rollback_available": any(item.get("status") == "approved" for item in snapshots),
        "human_approval_required": bool(snapshots),
        "boundary": "Snapshots are immutable release evidence. Approval, rollback, and game-day publication remain human-controlled.",
    }


def create_release_snapshot(*, repository: TenantRepository, snapshot_id: str, plan_id: str, week: str, note: str, actor: str, artifact_refs: list[str] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    if not snapshot_id.startswith("RELEASE-SNAPSHOT-"):
        issues.append("snapshot_id must start with RELEASE-SNAPSHOT-")
    if not plan_id or not week or not note:
        issues.append("plan_id, week, and note are required")
    if repository.get("game_plan_release_snapshots", snapshot_id):
        issues.append("snapshot_id already exists")
    plan = repository.get("game_plans", plan_id)
    if plan is None:
        issues.append(f"Unknown game plan: {plan_id}")
    if issues:
        return {"id": snapshot_id, "status": "invalid", "issues": issues, "organization_id": repository.organization_id}
    prior = next((item for item in repository.list("game_plan_release_snapshots") if item.get("week") == week and item.get("status") in {"approved", "pending_approval"}), None)
    dependency_manifest = _build_dependency_manifest(repository=repository, plan=plan, explicit_refs=artifact_refs)
    release_manifest = {"plan": plan, "dependencies": dependency_manifest}
    snapshot = {
        "id": snapshot_id,
        "organization_id": repository.organization_id,
        "plan_id": plan_id,
        "week": week,
        "status": "pending_approval",
        "locked": False,
        "immutable": True,
        "note": note,
        "content_hash": _hash(release_manifest),
        "renderer_version": "web-renderer-v1",
        "created_by": actor,
        "created_at": _now(),
        "previous_snapshot_id": prior.get("id") if prior else None,
        "what_changed": _changed_keys(prior.get("source_plan") if prior else None, plan),
        "source_plan": plan,
        "dependency_manifest": dependency_manifest,
        "release_manifest_hash": _hash(release_manifest),
        "human_approval_required": True,
    }
    return repository.put("game_plan_release_snapshots", snapshot_id, snapshot, actor=actor, reason="game_plan_release_snapshot_created")


def approve_release_snapshot(*, repository: TenantRepository, snapshot_id: str, decision_ref: str, actor: str) -> dict[str, Any]:
    snapshot = repository.get("game_plan_release_snapshots", snapshot_id)
    if snapshot is None:
        raise KeyError(f"Unknown release snapshot: {snapshot_id}")
    if snapshot.get("status") != "pending_approval":
        raise ValueError("Only a pending release snapshot can be approved")
    if not decision_ref.startswith("DEC-"):
        raise ValueError("decision_ref must start with DEC-")
    snapshot.update({"status": "approved", "locked": True, "approved_by": actor, "approved_at": _now(), "decision_ref": decision_ref, "human_approval_required": False})
    return repository.put("game_plan_release_snapshots", snapshot_id, snapshot, actor=actor, reason="game_plan_release_snapshot_approved")


def rollback_release_snapshot(*, repository: TenantRepository, snapshot_id: str, decision_ref: str, actor: str) -> dict[str, Any]:
    snapshot = repository.get("game_plan_release_snapshots", snapshot_id)
    if snapshot is None:
        raise KeyError(f"Unknown release snapshot: {snapshot_id}")
    if snapshot.get("status") != "approved":
        raise ValueError("Only an approved release snapshot can be rolled back")
    if not decision_ref.startswith("DEC-"):
        raise ValueError("decision_ref must start with DEC-")
    snapshot.update({"status": "rolled_back", "locked": False, "rolled_back_by": actor, "rolled_back_at": _now(), "rollback_decision_ref": decision_ref, "human_approval_required": False})
    return repository.put("game_plan_release_snapshots", snapshot_id, snapshot, actor=actor, reason="game_plan_release_snapshot_rolled_back")
