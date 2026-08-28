"""Organization-scoped repository adapter for canonical records."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


class RepositoryLike(Protocol):
    def put(self, collection: str, record_id: str, record: dict[str, Any], *, actor: str, reason: str) -> dict[str, Any]: ...
    def get(self, collection: str, record_id: str) -> dict[str, Any] | None: ...
    def list(self, collection: str) -> list[dict[str, Any]]: ...
    def history(self, *, collection: str | None = None, record_id: str | None = None) -> list[dict[str, Any]]: ...


class TenantRepository:
    """Wrap a canonical repository with deny-by-default organization isolation."""

    def __init__(self, repository: RepositoryLike, *, organization_id: str, actor: str, approved_cross_org_scope: bool = False):
        if not organization_id or not actor:
            raise ValueError("organization_id and actor are required")
        self.repository = repository
        self.organization_id = organization_id
        self.actor = actor
        self.approved_cross_org_scope = approved_cross_org_scope

    def _visible(self, record: dict[str, Any] | None) -> dict[str, Any] | None:
        if record is None:
            return None
        if self.approved_cross_org_scope or record.get("organization_id") == self.organization_id:
            return deepcopy(record)
        return None

    def put(self, collection: str, record_id: str, record: dict[str, Any], *, actor: str | None = None, reason: str = "tenant_scoped_write") -> dict[str, Any]:
        if record.get("organization_id") != self.organization_id:
            raise PermissionError("record organization_id does not match repository scope")
        return self.repository.put(collection, record_id, record, actor=actor or self.actor, reason=reason)

    def get(self, collection: str, record_id: str) -> dict[str, Any] | None:
        return self._visible(self.repository.get(collection, record_id))

    def list(self, collection: str) -> list[dict[str, Any]]:
        return [record for record in (self._visible(item) for item in self.repository.list(collection)) if record is not None]

    def history(self, *, collection: str | None = None, record_id: str | None = None) -> list[dict[str, Any]]:
        events = self.repository.history(collection=collection, record_id=record_id)
        if self.approved_cross_org_scope:
            return events
        visible_ids = {record_id for collection_name in self._collections() for record_id in self._record_ids(collection_name)}
        return [event for event in events if event.get("record_id") in visible_ids]

    def _collections(self) -> list[str]:
        # Repository adapters intentionally expose only the current collection
        # through list; known collections are discovered from the event stream.
        return sorted({event.get("collection") for event in self.repository.history() if event.get("collection")})

    def _record_ids(self, collection: str) -> list[str]:
        return [record.get("id") or record.get("_id") for record in self.repository.list(collection) if record.get("organization_id") == self.organization_id]
