"""Organization-scoped game-week deadlines, tasks, and delivery packets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _due(record: dict[str, Any]) -> str | None:
    return record.get("due_at") or record.get("due_date") or record.get("scheduled_for") or record.get("deadline")


def _task_state(record: dict[str, Any]) -> str:
    if record.get("status") in {"complete", "completed", "cancelled", "blocked"}:
        return str(record["status"])
    due = _due(record)
    if due:
        try:
            point = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
            if point.date() == datetime.now(timezone.utc).date():
                return "due_today"
            if point < datetime.now(timezone.utc):
                return "overdue"
        except ValueError:
            pass
    return str(record.get("status") or "scheduled")


def _packet_readiness(*, week: str | None, plans: list[dict[str, Any]], practices: list[dict[str, Any]], snapshots: list[dict[str, Any]], packets: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose packet prerequisites without pretending to generate or publish them."""
    plan_ids = {str(plan.get("id")) for plan in plans if plan.get("id")}
    practice_ids = {str(plan.get("id")) for plan in practices if plan.get("id")}
    release = next((snapshot for snapshot in snapshots if snapshot.get("locked") and snapshot.get("status") == "approved"), None)
    open_blockers = [str(task.get("id")) for task in tasks if task.get("computed_state") in {"overdue", "blocked"}]
    package_ids = {str(packet.get("id")) for packet in packets if packet.get("id")}

    definitions = [
        ("coach_packet", "Coach packet", "coaching staff", ["game_plan", "practice_plan", "approved_release"]),
        ("player_install_packet", "Player install packet", "players and position groups", ["game_plan", "practice_plan", "approved_release"]),
        ("coordinator_call_sheet", "Coordinator call sheet", "coordinators", ["game_plan", "approved_release"]),
        ("wristband_layout", "Wristband layout", "game-day operators", ["game_plan", "approved_release"]),
        ("administrator_audit_packet", "Administrator audit packet", "program administrators", ["game_plan", "delivery_package"]),
    ]
    available = {
        "game_plan": bool(plan_ids),
        "practice_plan": bool(practice_ids),
        "approved_release": bool(release),
        "delivery_package": bool(package_ids),
    }
    linked = {
        "game_plan": sorted(plan_ids),
        "practice_plan": sorted(practice_ids),
        "approved_release": [str(release.get("id"))] if release else [],
        "delivery_package": sorted(package_ids),
    }
    readiness = []
    for packet_id, label, audience, required in definitions:
        missing = [requirement for requirement in required if not available[requirement]]
        blockers = list(open_blockers)
        if missing:
            blockers.extend(f"missing:{requirement}" for requirement in missing)
        readiness.append({
            "id": packet_id,
            "label": label,
            "audience": audience,
            "week": week,
            "status": "blocked" if blockers else "ready_for_assembly",
            "required": required,
            "linked_records": sorted({ref for requirement in required for ref in linked[requirement]}),
            "missing": missing,
            "blockers": blockers,
            "human_review_required": True,
            "boundary": "Readiness is an assembly signal. Staff must verify content, approvals, branding, and recipient access before delivery.",
        })
    return readiness


def create_delivery_packet(*, repository: TenantRepository, packet_id: str, packet_type: str, week: str, linked_records: list[str], actor: str) -> dict[str, Any]:
    allowed_types = {"coach_packet", "player_install_packet", "coordinator_call_sheet", "wristband_layout", "administrator_audit_packet"}
    issues: list[str] = []
    if not packet_id.startswith("DELIVERY-PACKET-"):
        issues.append("packet_id must start with DELIVERY-PACKET-")
    if packet_type not in allowed_types:
        issues.append("packet_type is not a supported delivery packet")
    if not week:
        issues.append("week is required")
    if repository.get("delivery_packets", packet_id):
        issues.append("packet_id already exists")
    if issues:
        return {"id": packet_id, "status": "invalid", "issues": issues, "organization_id": repository.organization_id}

    workspace = build_delivery_workspace(repository=repository, week=week)
    readiness = next((item for item in workspace["packet_readiness"] if item["id"] == packet_type), None)
    if readiness is None:
        return {"id": packet_id, "status": "invalid", "issues": ["packet readiness definition is unavailable"], "organization_id": repository.organization_id}
    refs = sorted({str(reference).strip() for reference in linked_records if str(reference).strip()} | set(readiness["linked_records"]))
    packet = {
        "id": packet_id,
        "organization_id": repository.organization_id,
        "packet_type": packet_type,
        "label": readiness["label"],
        "audience": readiness["audience"],
        "week": week,
        "status": "blocked" if readiness["status"] == "blocked" else "under_review",
        "linked_records": refs,
        "missing": readiness["missing"],
        "blockers": readiness["blockers"],
        "human_review_required": True,
        "created_by": actor,
        "created_at": _now(),
        "boundary": "This packet is an assembled, reviewable handoff record. It does not publish externally or bypass approval.",
    }
    return repository.put("delivery_packets", packet_id, packet, actor=actor, reason="delivery_packet_assembled")


def build_delivery_workspace(*, repository: TenantRepository, week: str | None = None) -> dict[str, Any]:
    tasks = repository.list("delivery_tasks")
    if week:
        tasks = [task for task in tasks if task.get("week") == week]
    tasks.sort(key=lambda record: (_due(record) or "9999", record.get("title") or record.get("id") or ""))
    packets = repository.list("weekly_delivery_packages")
    delivery_packets = repository.list("delivery_packets")
    snapshots = repository.list("game_plan_release_snapshots")
    practices = repository.list("practice_plans")
    plans = repository.list("game_plans")
    if week:
        snapshots = [snapshot for snapshot in snapshots if snapshot.get("week") == week]
        practices = [practice for practice in practices if practice.get("week_context") == week or practice.get("week") == week]
        plans = [plan for plan in plans if plan.get("week_context") == week or plan.get("week") == week]
    for task in tasks:
        task["computed_state"] = _task_state(task)
    return {
        "organization_id": repository.organization_id,
        "status": "ready" if tasks or packets or snapshots or practices else "empty",
        "week": week,
        "tasks": tasks,
        "packets": packets,
        "delivery_packets": delivery_packets,
        "release_snapshots": snapshots,
        "practice_plans": practices,
        "packet_readiness": _packet_readiness(week=week, plans=plans, practices=practices, snapshots=snapshots, packets=packets, tasks=tasks),
        "counts": {
            "tasks": len(tasks),
            "overdue": sum(1 for task in tasks if task.get("computed_state") == "overdue"),
            "due_today": sum(1 for task in tasks if task.get("computed_state") == "due_today"),
            "completed": sum(1 for task in tasks if task.get("computed_state") in {"complete", "completed"}),
            "packets": len(packets),
            "locked_releases": sum(1 for snapshot in snapshots if snapshot.get("locked")),
        },
        "delivery_packet_outputs": ["coach packet", "player install packet", "coordinator call sheet", "wristband layout", "administrator audit packet"],
        "human_review_required": bool(any(task.get("computed_state") in {"overdue", "blocked"} for task in tasks) or any(packet.get("status") in {"under_review", "blocked"} for packet in packets)),
        "boundary": "The delivery center schedules and assembles references. It does not silently publish a plan, notify an external provider, or replace staff approval.",
    }


def create_delivery_task(*, repository: TenantRepository, task_id: str, title: str, category: str, owner: str, due_at: str, week: str, linked_records: list[str], priority: str, actor: str) -> dict[str, Any]:
    issues: list[str] = []
    if not task_id.startswith("DELIVERY-TASK-"):
        issues.append("task_id must start with DELIVERY-TASK-")
    if not title or not category or not owner or not due_at or not week:
        issues.append("title, category, owner, due_at, and week are required")
    if repository.get("delivery_tasks", task_id):
        issues.append("task_id already exists")
    if issues:
        return {"id": task_id, "status": "invalid", "issues": issues, "organization_id": repository.organization_id}
    notification_id = f"NOTIFY-DELIVERY-{task_id}"
    task = {"id": task_id, "organization_id": repository.organization_id, "title": title, "category": category, "owner": owner, "assigned_to": owner, "due_at": due_at, "week": week, "priority": priority or "normal", "linked_records": linked_records, "status": "scheduled", "created_by": actor, "created_at": _now(), "human_review_required": False, "notification_id": notification_id}
    saved = repository.put("delivery_tasks", task_id, task, actor=actor, reason="delivery_task_created")
    if repository.get("notifications", notification_id) is None:
        repository.put(
            "notifications",
            notification_id,
            {
                "id": notification_id,
                "organization_id": repository.organization_id,
                "recipient": owner,
                "assigned_to": owner,
                "title": f"Game-week responsibility assigned: {title}",
                "description": f"{category.title()} responsibility due {due_at} for {week}.",
                "body": f"{category.title()} responsibility due {due_at} for {week}.",
                "kind": "delivery_task",
                "category": "delivery",
                "related_record_id": task_id,
                "deep_link": f"/app/delivery?record={task_id}",
                "status": "unread",
                "visibility": "private",
                "created_at": saved["created_at"],
            },
            actor=actor,
            reason="delivery_task_owner_notified",
        )
    return saved


def complete_delivery_task(*, repository: TenantRepository, task_id: str, actor: str, note: str = "") -> dict[str, Any]:
    task = repository.get("delivery_tasks", task_id)
    if task is None:
        raise KeyError(f"Unknown delivery task: {task_id}")
    task.update({"status": "completed", "completed_by": actor, "completed_at": _now(), "completion_note": note})
    return repository.put("delivery_tasks", task_id, task, actor=actor, reason="delivery_task_completed")
