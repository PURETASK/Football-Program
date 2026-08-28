"""Organization-scoped operational inbox and notification aggregation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from .approval_inbox import build_approval_inbox
from .tenant_repository import TenantRepository


INBOX_COLLECTIONS = (
    "tasks",
    "collaboration_threads",
    "notifications",
    "practice_plans",
    "scouting_reports",
    "game_plans",
    "release_candidates",
    "play_designs",
    "media_processing_jobs",
    "knowledge_sources",
    "player_assignments",
    "analytics_reports",
    "film_observations",
    "film_playlists",
    "delivery_packets",
)

COLLECTION_METADATA: dict[str, dict[str, str]] = {
    "tasks": {"category": "task", "item_type": "task", "deep_link": "/"},
    "collaboration_threads": {"category": "review", "item_type": "collaboration", "deep_link": "/collaboration"},
    "notifications": {"category": "notification", "item_type": "notification", "deep_link": "/"},
    "practice_plans": {"category": "practice", "item_type": "workflow", "deep_link": "/practice"},
    "scouting_reports": {"category": "scouting", "item_type": "workflow", "deep_link": "/scouting"},
    "game_plans": {"category": "game_plan", "item_type": "workflow", "deep_link": "/game-plan"},
    "release_candidates": {"category": "game_plan", "item_type": "release", "deep_link": "/game-plan"},
    "play_designs": {"category": "playbook", "item_type": "workflow", "deep_link": "/playbook"},
    "media_processing_jobs": {"category": "media", "item_type": "validation", "deep_link": "/film"},
    "knowledge_sources": {"category": "source", "item_type": "source", "deep_link": "/admin"},
    "player_assignments": {"category": "player", "item_type": "assignment", "deep_link": "/player"},
    "analytics_reports": {"category": "analytics", "item_type": "workflow", "deep_link": "/"},
    "film_observations": {"category": "film", "item_type": "evidence", "deep_link": "/film"},
    "film_playlists": {"category": "film", "item_type": "workflow", "deep_link": "/film"},
    "delivery_packets": {"category": "delivery", "item_type": "packet", "deep_link": "/delivery"},
}

ROLE_CATEGORIES: dict[str, set[str]] = {
    "player": {"notification", "task", "player", "playbook", "film"},
    "coach_staff": {"notification", "task", "review", "practice", "scouting", "game_plan", "playbook", "film", "player", "media", "delivery"},
    "analyst": {"notification", "task", "review", "scouting", "game_plan", "film", "media", "source", "analytics", "delivery"},
    "program_owner": {"notification", "task", "review", "practice", "scouting", "game_plan", "playbook", "film", "player", "media", "source", "analytics", "delivery"},
    "validator": {"notification", "task", "review", "media", "source", "delivery"},
    "performance_staff": {"notification", "task", "practice", "player", "analytics", "delivery"},
}

REVIEW_STATES = {"draft", "under_review", "needs_review", "pending_approval"}
BLOCKED_STATES = {"blocked", "failed", "invalid", "retryable", "error"}


def _values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return ", ".join(_text(item) for item in _values(value))
    return str(value)


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{value}T23:59:59+00:00")
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _due(record: dict[str, Any], *, now: datetime) -> tuple[str, str | None]:
    for key in ("due_at", "due_date", "deadline", "due_by", "scheduled_for"):
        parsed = _parse_datetime(record.get(key))
        if parsed is None:
            continue
        if parsed < now:
            return "overdue", parsed.isoformat()
        if parsed <= now + timedelta(days=1):
            return "due_today", parsed.isoformat()
        return "upcoming", parsed.isoformat()
    return "unscheduled", None


def _owner(record: dict[str, Any]) -> str | None:
    for key in ("assigned_to", "assignee", "owner", "requester", "analyst", "requested_by"):
        value = record.get(key)
        if value:
            return _text(value)
    return None


def _priority(record: dict[str, Any], *, due_state: str, status: str | None) -> str:
    requested = _text(record.get("urgency") or record.get("priority")).lower()
    if requested in {"critical", "high", "normal", "low"}:
        return requested
    if status in BLOCKED_STATES:
        return "critical"
    if due_state == "overdue":
        return "high"
    if due_state == "due_today" or status in REVIEW_STATES:
        return "high"
    return "normal"


def _record_item(
    *,
    collection: str,
    record: dict[str, Any],
    role: str,
    actor: str,
    now: datetime,
    forced_category: str | None = None,
    forced_item_type: str | None = None,
) -> dict[str, Any] | None:
    metadata = COLLECTION_METADATA.get(collection, {"category": "task", "item_type": "workflow", "deep_link": "/"})
    origin_category = metadata["category"]
    category = forced_category or metadata["category"]
    if category not in ROLE_CATEGORIES.get(role, {category}):
        return None

    record_id = _text(record.get("id") or record.get("_id"))
    if not record_id:
        return None
    owner = _owner(record)
    assigned = _text(record.get("assigned_to") or record.get("assignee")) or owner
    player_id = _text(record.get("player_id"))
    if role == "player" and actor not in {owner, assigned, player_id, _text(record.get("visible_to"))}:
        return None

    status = _text(record.get("status") or record.get("approval_state"), "open")
    due_state, due_at = _due(record, now=now)
    unread = collection == "notifications" and not record.get("read_at") and record.get("status") != "read"
    blockers = _values(record.get("blockers")) + _values(record.get("issues"))
    evidence = _values(record.get("evidence_refs")) + _values(record.get("source_refs")) + _values(record.get("output_refs"))
    title = _text(record.get("title") or record.get("name") or record.get("label") or record.get("subject"))
    if not title:
        title = f"{category.replace('_', ' ').title()} {record_id}"
    if forced_category == "review" and not title.lower().startswith("review "):
        title = f"Review {title}"
    deep_link = _text(record.get("deep_link"), metadata["deep_link"])
    priority = _priority(record, due_state=due_state, status=status)
    return {
        "id": f"INBOX-{collection}-{record_id}",
        "collection": collection,
        "record_id": record_id,
        "item_type": forced_item_type or metadata["item_type"],
        "category": category,
        "origin_category": origin_category,
        "title": title,
        "description": _text(record.get("description") or record.get("summary") or record.get("rationale")),
        "status": status,
        "urgency": priority,
        "priority": priority,
        "owner": owner,
        "assigned_to": assigned,
        "assigned_to_me": assigned == actor or owner == actor,
        "due_at": due_at,
        "due_state": due_state,
        "blockers": blockers,
        "evidence_refs": evidence,
        "notification_unread": unread,
        "deep_link": deep_link,
        "action_label": _text(record.get("action_label"), "Open details"),
        "can_act": bool(record.get("can_act", role in {"coach_staff", "analyst", "program_owner", "performance_staff"})),
        "operation": _text(record.get("operation")) or None,
        "asset_id": _text(record.get("asset_id")) or None,
        "attempt": record.get("attempt"),
        "last_error": record.get("last_error"),
        "next_action": _text(record.get("next_action")) or None,
        "created_at": _text(record.get("created_at") or record.get("_saved_at")),
        "updated_at": _text(record.get("updated_at") or record.get("_saved_at")),
    }


def _matches(item: dict[str, Any], filters: dict[str, str]) -> bool:
    for key in ("category", "origin_category", "status", "urgency", "due_state"):
        value = filters.get(key)
        if value and value != "all" and item.get(key) != value:
            return False
    if filters.get("assigned_to") and item.get("assigned_to") != filters["assigned_to"]:
        return False
    if filters.get("assigned_to_me") == "true" and not item.get("assigned_to_me"):
        return False
    if filters.get("unread_only") == "true" and not item.get("notification_unread"):
        return False
    needle = filters.get("search", "").strip().lower()
    if needle and needle not in _text(item).lower():
        return False
    return True


def build_operations_inbox(
    *,
    repository: TenantRepository,
    role: str,
    actor: str,
    filters: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    active_filters = filters or {}
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    governance = build_approval_inbox(repository=repository, role=role)
    for review in governance["items"]:
        record_id = _text(review.get("id"))
        record = repository.get(review["collection"], record_id) or review
        item = _record_item(collection=review["collection"], record=record, role=role, actor=actor, now=current, forced_category="review", forced_item_type="review")
        if item is not None:
            item.update({"human_review_required": bool(review.get("human_review_required")), "can_approve": bool(review.get("can_approve"))})
            items.append(item)
            seen.add((review["collection"], record_id))

    for collection in INBOX_COLLECTIONS:
        for record in repository.list(collection):
            record_id = _text(record.get("id") or record.get("_id"))
            if (collection, record_id) in seen:
                continue
            if collection == "collaboration_threads" and record.get("status") == "resolved" and active_filters.get("include_resolved") != "true":
                continue
            if collection == "notifications" and record.get("read_at") and active_filters.get("unread_only") == "true":
                continue
            item = _record_item(collection=collection, record=record, role=role, actor=actor, now=current)
            if item is not None and (item["notification_unread"] or collection != "notifications" or active_filters.get("include_read") == "true"):
                items.append(item)

    visible = [item for item in items if _matches(item, active_filters)]
    visible.sort(key=lambda item: (0 if item["due_state"] == "overdue" else 1 if item["urgency"] == "critical" else 2 if item["due_state"] == "due_today" else 3, item["due_at"] or "9999", item["title"]))
    by_category = Counter(item["category"] for item in visible)
    by_urgency = Counter(item["urgency"] for item in visible)
    by_due_state = Counter(item["due_state"] for item in visible)
    return {
        "organization_id": repository.organization_id,
        "role": role,
        "actor": actor,
        "items": visible,
        "count": len(visible),
        "counts": {"by_category": dict(by_category), "by_urgency": dict(by_urgency), "by_due_state": dict(by_due_state), "unread_notifications": sum(1 for item in visible if item["notification_unread"]), "assigned_to_me": sum(1 for item in visible if item["assigned_to_me"]), "overdue": sum(1 for item in visible if item["due_state"] == "overdue")},
        "filters": active_filters,
        "generated_at": current.isoformat(),
        "automation_boundary": "The inbox prioritizes and links work; it never silently approves, publishes, changes player status, or changes external provider state.",
    }


def mark_notifications_read(*, repository: TenantRepository, notification_ids: list[str], actor: str, read_at: str | None = None) -> dict[str, Any]:
    timestamp = read_at or datetime.now(timezone.utc).isoformat()
    marked: list[str] = []
    for notification_id in notification_ids:
        record = repository.get("notifications", notification_id)
        if record is None:
            continue
        recipient = _text(record.get("recipient") or record.get("assigned_to") or record.get("owner"))
        if recipient and recipient != actor and record.get("visibility") == "private":
            continue
        record.update({"status": "read", "read_at": timestamp, "read_by": actor})
        repository.put("notifications", notification_id, record, actor=actor, reason="operations_notification_read")
        marked.append(notification_id)
    return {"organization_id": repository.organization_id, "marked_count": len(marked), "notification_ids": marked, "read_at": timestamp}
