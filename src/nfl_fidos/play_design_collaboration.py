"""Organization-scoped collaboration primitives for the Play Designer.

The event log is transport-neutral: the local HTTP adapter exposes it through
an authenticated Server-Sent Events stream with bounded short-poll fallback.
Presence has an expiry, cursors are ephemeral records, and durable
design/comment events remain append-only and auditable.
"""

from __future__ import annotations

import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .tenant_repository import TenantRepository


class PlayDesignCollaborationService:
    PRESENCE_TTL_SECONDS = 45

    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def _require_design(self, design_id: str) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        return design

    def heartbeat(
        self,
        *,
        design_id: str,
        session_id: str,
        subject: str,
        role: str,
        display_name: str,
        color: str,
        cursor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_design(design_id)
        if not session_id or not subject:
            raise ValueError("session_id and subject are required")
        expires_at = time.time() + self.PRESENCE_TTL_SECONDS
        presence = {
            "id": f"PRESENCE-{design_id}-{session_id}",
            "organization_id": self.repository.organization_id,
            "design_id": design_id,
            "session_id": session_id,
            "subject": subject,
            "role": role,
            "display_name": display_name or subject,
            "color": color or "#2563eb",
            "cursor": deepcopy(cursor) if isinstance(cursor, dict) else None,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "status": "active",
        }
        return self.repository.put("play_design_presence", presence["id"], presence, actor=subject, reason="play_design_presence_heartbeat")

    def leave(self, *, design_id: str, session_id: str, actor: str) -> dict[str, Any]:
        self._require_design(design_id)
        presence_id = f"PRESENCE-{design_id}-{session_id}"
        presence = self.repository.get("play_design_presence", presence_id)
        if presence is None:
            return {"id": presence_id, "status": "absent"}
        presence["status"] = "left"
        presence["expires_at"] = 0
        return self.repository.put("play_design_presence", presence_id, presence, actor=actor, reason="play_design_presence_left")

    def active_presence(self, *, design_id: str) -> list[dict[str, Any]]:
        self._require_design(design_id)
        current = time.time()
        output = [item for item in self.repository.list("play_design_presence") if item.get("design_id") == design_id and item.get("status") == "active" and float(item.get("expires_at", 0)) > current]
        return sorted(output, key=lambda item: item.get("last_seen_at", ""))

    def record_event(self, *, design_id: str, event_type: str, actor: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_design(design_id)
        events = [item for item in self.repository.list("play_design_collaboration_events") if item.get("design_id") == design_id]
        sequence = max((int(item.get("sequence", 0)) for item in events), default=0) + 1
        event = {
            "id": f"COLLAB-EVENT-{design_id}-{sequence:06d}",
            "organization_id": self.repository.organization_id,
            "design_id": design_id,
            "sequence": sequence,
            "event_type": event_type,
            "actor": actor,
            "payload": deepcopy(payload or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.repository.put("play_design_collaboration_events", event["id"], event, actor=actor, reason=f"play_design_collaboration_{event_type}")

    def events(self, *, design_id: str, since_sequence: int = 0) -> list[dict[str, Any]]:
        self._require_design(design_id)
        events = [item for item in self.repository.list("play_design_collaboration_events") if item.get("design_id") == design_id and int(item.get("sequence", 0)) > since_sequence]
        return sorted(events, key=lambda item: int(item.get("sequence", 0)))
