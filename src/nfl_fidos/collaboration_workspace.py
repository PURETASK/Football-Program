"""Organization-wide collaboration, notification, and presence workspace.

This service deliberately stays below domain approval services. It can create
discussion, assignment, notification, and presence records, but it cannot
approve, publish, lock, or mutate the authoritative football artifact that a
thread references.
"""

from __future__ import annotations

import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


AUTHOR_ROLES = {"coach_staff", "analyst", "program_owner", "validator", "performance_staff"}
RESOLVE_ROLES = {"coach_staff", "program_owner", "validator"}
DECISIONS = {"resolved", "reopened"}
PRESENCE_TTL_SECONDS = 45


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, list):
        return []
    return [_text(item).strip() for item in value if _text(item).strip()]


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_link(value: Any) -> str:
    link = _text(value, "/inbox")
    return link if link.startswith("/") and not link.startswith("//") else "/inbox"


class CollaborationWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def _visible_thread(self, thread: dict[str, Any], *, actor: str, role: str) -> bool:
        if role != "player":
            return True
        participants = set(_list(thread.get("participants")))
        return actor in participants or actor == _text(thread.get("assigned_to"))

    def _visible_notification(self, notification: dict[str, Any], *, actor: str) -> bool:
        recipient = _text(notification.get("recipient") or notification.get("assigned_to"))
        visibility = _text(notification.get("visibility"), "private")
        return not recipient or recipient == actor or visibility == "organization"

    def _activity(self, *, activity_id: str, event_type: str, actor: str, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.repository.list("collaboration_activity")
        sequence = max((max(int(item.get("sequence") or 0), index + 1) for index, item in enumerate(existing)), default=0) + 1
        return self.repository.put(
            "collaboration_activity",
            activity_id,
            {
                "id": activity_id,
                "organization_id": self.repository.organization_id,
                "sequence": sequence,
                "event_type": event_type,
                "actor": actor,
                "subject": subject,
                "payload": deepcopy(payload),
                "created_at": _now(),
            },
            actor=actor,
            reason=f"collaboration_{event_type}",
        )

    def events(self, *, since_sequence: int = 0, actor: str | None = None, role: str | None = None) -> list[dict[str, Any]]:
        """Return organization activity events after a replay cursor."""
        activities = self.repository.list("collaboration_activity")
        normalized: list[dict[str, Any]] = []
        previous_sequence = 0
        for index, activity in enumerate(sorted(activities, key=lambda item: (item.get("created_at", ""), item.get("id", ""))), start=1):
            event = deepcopy(activity)
            event["sequence"] = max(int(event.get("sequence") or 0), index, previous_sequence + 1)
            previous_sequence = event["sequence"]
            if role == "player" and actor:
                payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                thread_id = payload.get("thread_id")
                thread = self.repository.get("collaboration_threads", str(thread_id)) if thread_id else None
                if thread is not None and not self._visible_thread(thread, actor=actor, role=role):
                    continue
            if event["sequence"] > since_sequence:
                normalized.append(event)
        return sorted(normalized, key=lambda item: int(item.get("sequence", 0)))

    def _notify(self, *, notification_id: str, recipient: str, title: str, body: str, thread: dict[str, Any], actor: str, kind: str) -> dict[str, Any]:
        notification = {
            "id": notification_id,
            "organization_id": self.repository.organization_id,
            "recipient": recipient,
            "title": title,
            "description": body,
            "body": body,
            "kind": kind,
            "thread_id": thread["id"],
            "deep_link": thread.get("deep_link", "/collaboration"),
            "status": "unread",
            "visibility": "private",
            "created_at": _now(),
        }
        return self.repository.put("notifications", notification_id, notification, actor=actor, reason="collaboration_notification_created")

    def _notify_targets(self, *, thread: dict[str, Any], actor: str, extra: list[str], title: str, body: str, kind: str) -> None:
        targets = set(_list(thread.get("participants"))) | set(_list(thread.get("mentions"))) | set(extra)
        targets.discard(actor)
        for index, recipient in enumerate(sorted(targets), start=1):
            if not recipient:
                continue
            self._notify(
                notification_id=f"NOTIFY-COLLAB-{thread['id']}-{index:03d}-{len(self.repository.list('notifications')):05d}",
                recipient=recipient,
                title=title,
                body=body,
                thread=thread,
                actor=actor,
                kind=kind,
            )

    def create_thread(
        self,
        *,
        thread_id: str,
        title: str,
        body: str,
        entity_type: str,
        entity_id: str,
        deep_link: str,
        author: str,
        role: str,
        assignee: str | None = None,
        mentions: list[str] | None = None,
        participants: list[str] | None = None,
        priority: str = "normal",
        due_at: str | None = None,
    ) -> dict[str, Any]:
        if role not in AUTHOR_ROLES:
            raise PermissionError("role is not authorized to create collaboration threads")
        if not thread_id.startswith("COLLAB-THREAD-"):
            raise ValueError("thread_id must start with COLLAB-THREAD-")
        if not title.strip() or not body.strip() or not entity_type.strip() or not entity_id.strip():
            raise ValueError("title, body, entity_type, and entity_id are required")
        if priority not in {"critical", "high", "normal", "low"}:
            raise ValueError("priority must be critical, high, normal, or low")
        existing = self.repository.get("collaboration_threads", thread_id)
        if existing is not None:
            same_request = all(existing.get(key) == value for key, value in {
                "title": title.strip(),
                "body": body.strip(),
                "entity_type": entity_type.strip(),
                "entity_id": entity_id.strip(),
                "deep_link": _safe_link(deep_link),
                "created_by": author,
            }.items())
            if same_request:
                return deepcopy(existing)
            raise ValueError("thread_id already identifies a different collaboration thread")
        timestamp = _now()
        mention_list = _list(mentions)
        participant_list = sorted(set(_list(participants)) | set(mention_list) | ({assignee} if assignee else set()) | {author})
        thread = {
            "id": thread_id,
            "organization_id": self.repository.organization_id,
            "title": title.strip(),
            "body": body.strip(),
            "entity_type": entity_type.strip(),
            "entity_id": entity_id.strip(),
            "deep_link": _safe_link(deep_link),
            "status": "open",
            "priority": priority,
            "assigned_to": assignee or None,
            "mentions": mention_list,
            "participants": participant_list,
            "due_at": due_at,
            "created_by": author,
            "created_role": role,
            "created_at": timestamp,
            "updated_at": timestamp,
            "comments": [{
                "id": f"COMMENT-{thread_id}-ROOT",
                "thread_id": thread_id,
                "author": author,
                "role": role,
                "body": body.strip(),
                "mentions": mention_list,
                "created_at": timestamp,
            }],
            "resolution": None,
        }
        saved = self.repository.put("collaboration_threads", thread_id, thread, actor=author, reason="collaboration_thread_created")
        self._activity(activity_id=f"ACTIVITY-{thread_id}-CREATED", event_type="thread_created", actor=author, subject=title.strip(), payload={"thread_id": thread_id, "entity_type": entity_type, "entity_id": entity_id})
        self._notify_targets(thread=saved, actor=author, extra=[assignee] if assignee else [], title=f"New collaboration thread: {title.strip()}", body=body.strip(), kind="thread_created")
        return saved

    def append_comment(self, *, thread_id: str, comment_id: str, body: str, mentions: list[str] | None, author: str, role: str) -> dict[str, Any]:
        if role not in AUTHOR_ROLES:
            raise PermissionError("role is not authorized to comment")
        if not comment_id.startswith("COMMENT-") or not body.strip():
            raise ValueError("comment_id and body are required")
        thread = self.repository.get("collaboration_threads", thread_id)
        if thread is None:
            raise KeyError(f"Unknown collaboration thread: {thread_id}")
        if thread.get("status") != "open":
            raise ValueError("resolved collaboration threads cannot receive comments")
        mention_list = _list(mentions)
        existing_comment = next((item for item in _list_of_dicts(thread.get("comments")) if item.get("id") == comment_id), None)
        if existing_comment is not None:
            same_request = all(existing_comment.get(key) == value for key, value in {
                "thread_id": thread_id,
                "author": author,
                "body": body.strip(),
                "mentions": mention_list,
            }.items())
            if same_request:
                return deepcopy(thread)
            raise ValueError("comment_id already identifies a different collaboration comment")
        comment = {"id": comment_id, "thread_id": thread_id, "author": author, "role": role, "body": body.strip(), "mentions": mention_list, "created_at": _now()}
        thread.setdefault("comments", []).append(comment)
        thread["mentions"] = sorted(set(_list(thread.get("mentions"))) | set(mention_list))
        thread["participants"] = sorted(set(_list(thread.get("participants"))) | set(mention_list) | {author})
        thread["updated_at"] = comment["created_at"]
        saved = self.repository.put("collaboration_threads", thread_id, thread, actor=author, reason="collaboration_comment_added")
        self._activity(activity_id=f"ACTIVITY-{thread_id}-{comment_id}", event_type="comment_added", actor=author, subject=thread.get("title", thread_id), payload={"thread_id": thread_id, "comment_id": comment_id})
        self._notify_targets(thread=saved, actor=author, extra=[], title=f"New reply: {thread.get('title', thread_id)}", body=body.strip(), kind="comment_added")
        return saved

    def assign_thread(self, *, thread_id: str, assignee: str, due_at: str | None, priority: str | None, actor: str, role: str) -> dict[str, Any]:
        if role not in AUTHOR_ROLES:
            raise PermissionError("role is not authorized to assign collaboration work")
        thread = self.repository.get("collaboration_threads", thread_id)
        if thread is None:
            raise KeyError(f"Unknown collaboration thread: {thread_id}")
        if not assignee.strip():
            raise ValueError("assignee is required")
        if priority and priority not in {"critical", "high", "normal", "low"}:
            raise ValueError("priority must be critical, high, normal, or low")
        thread["assigned_to"] = assignee.strip()
        thread["participants"] = sorted(set(_list(thread.get("participants"))) | {assignee.strip()})
        if due_at is not None:
            thread["due_at"] = due_at
        if priority:
            thread["priority"] = priority
        thread["updated_at"] = _now()
        saved = self.repository.put("collaboration_threads", thread_id, thread, actor=actor, reason="collaboration_thread_assigned")
        self._activity(activity_id=f"ACTIVITY-{thread_id}-ASSIGNED-{len(self.repository.list('collaboration_activity')):05d}", event_type="thread_assigned", actor=actor, subject=thread.get("title", thread_id), payload={"thread_id": thread_id, "assignee": assignee, "due_at": due_at, "priority": priority})
        self._notify_targets(thread=saved, actor=actor, extra=[assignee], title=f"Work assigned: {thread.get('title', thread_id)}", body=f"You are accountable for {thread.get('title', thread_id)}.", kind="assignment")
        return saved

    def resolve_thread(self, *, thread_id: str, decision: str, rationale: str, actor: str, role: str) -> dict[str, Any]:
        if role not in RESOLVE_ROLES:
            raise PermissionError("only coaching, owner, or validator roles may resolve collaboration threads")
        if decision not in DECISIONS or not rationale.strip():
            raise ValueError("decision must be resolved or reopened and rationale is required")
        thread = self.repository.get("collaboration_threads", thread_id)
        if thread is None:
            raise KeyError(f"Unknown collaboration thread: {thread_id}")
        thread["status"] = "resolved" if decision == "resolved" else "open"
        thread["resolution"] = {"decision": decision, "rationale": rationale.strip(), "resolved_by": actor, "resolved_role": role, "resolved_at": _now()}
        thread["updated_at"] = thread["resolution"]["resolved_at"]
        saved = self.repository.put("collaboration_threads", thread_id, thread, actor=actor, reason="collaboration_thread_resolved" if decision == "resolved" else "collaboration_thread_reopened")
        self._activity(activity_id=f"ACTIVITY-{thread_id}-RESOLUTION-{len(self.repository.list('collaboration_activity')):05d}", event_type=f"thread_{decision}", actor=actor, subject=thread.get("title", thread_id), payload={"thread_id": thread_id, "rationale": rationale.strip()})
        return saved

    def mark_notifications_read(self, *, notification_ids: list[str], actor: str) -> dict[str, Any]:
        timestamp = _now()
        marked: list[str] = []
        for notification_id in notification_ids:
            notification = self.repository.get("notifications", notification_id)
            if notification is None or not self._visible_notification(notification, actor=actor):
                continue
            notification.update({"status": "read", "read_at": timestamp, "read_by": actor})
            self.repository.put("notifications", notification_id, notification, actor=actor, reason="collaboration_notification_read")
            marked.append(notification_id)
        return {"organization_id": self.repository.organization_id, "marked_count": len(marked), "notification_ids": marked, "read_at": timestamp}

    def heartbeat(self, *, session_id: str, actor: str, role: str, display_name: str, color: str, cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        if not session_id or not actor:
            raise ValueError("session_id and actor are required")
        presence = {
            "id": f"PRESENCE-COLLAB-{session_id}",
            "organization_id": self.repository.organization_id,
            "session_id": session_id,
            "subject": actor,
            "role": role,
            "display_name": display_name or actor,
            "color": color or "#2563eb",
            "cursor": deepcopy(cursor) if isinstance(cursor, dict) else None,
            "last_seen_at": _now(),
            "expires_at": time.time() + PRESENCE_TTL_SECONDS,
            "status": "active",
        }
        return self.repository.put("collaboration_presence", presence["id"], presence, actor=actor, reason="collaboration_presence_heartbeat")

    def leave(self, *, session_id: str, actor: str) -> dict[str, Any]:
        presence_id = f"PRESENCE-COLLAB-{session_id}"
        presence = self.repository.get("collaboration_presence", presence_id)
        if presence is None:
            return {"id": presence_id, "status": "absent"}
        presence.update({"status": "left", "expires_at": 0})
        return self.repository.put("collaboration_presence", presence_id, presence, actor=actor, reason="collaboration_presence_left")

    def workspace(self, *, actor: str, role: str, status: str | None = None, assigned_to: str | None = None, unread_only: bool = False) -> dict[str, Any]:
        threads = [thread for thread in self.repository.list("collaboration_threads") if self._visible_thread(thread, actor=actor, role=role)]
        if status and status != "all":
            threads = [thread for thread in threads if thread.get("status") == status]
        if assigned_to == "me":
            threads = [thread for thread in threads if thread.get("assigned_to") == actor]
        notifications = [item for item in self.repository.list("notifications") if self._visible_notification(item, actor=actor)]
        if unread_only:
            notifications = [item for item in notifications if item.get("status") != "read" and not item.get("read_at")]
        activities = self.repository.list("collaboration_activity")[-100:]
        active_presence = [item for item in self.repository.list("collaboration_presence") if item.get("status") == "active" and float(item.get("expires_at", 0)) > time.time()]
        threads.sort(key=lambda item: (0 if item.get("status") == "open" else 1, 0 if item.get("priority") == "critical" else 1 if item.get("priority") == "high" else 2, item.get("due_at") or "9999", item.get("updated_at") or ""), reverse=False)
        notifications.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return {
            "organization_id": self.repository.organization_id,
            "actor": actor,
            "role": role,
            "threads": threads,
            "notifications": notifications,
            "activity": sorted(activities, key=lambda item: item.get("created_at", ""), reverse=True),
            "presence": sorted(active_presence, key=lambda item: item.get("last_seen_at", "")),
            "counts": {
                "open_threads": sum(1 for item in threads if item.get("status") == "open"),
                "assigned_to_me": sum(1 for item in threads if item.get("assigned_to") == actor and item.get("status") == "open"),
                "unread_notifications": sum(1 for item in notifications if item.get("status") != "read" and not item.get("read_at")),
                "active_presence": len(active_presence),
            },
            "boundary": "Collaboration records discussion, assignment, presence, and notifications. It never silently approves, publishes, locks, or changes the authoritative football record.",
        }
