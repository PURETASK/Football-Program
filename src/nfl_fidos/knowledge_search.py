"""Organization-scoped provenance-aware knowledge retrieval index."""

from __future__ import annotations

import re
import sqlite3
import threading
from typing import Any

from .tenant_repository import TenantRepository


SEARCH_COLLECTIONS = ("knowledge_items", "knowledge_claims", "knowledge_sources")


class KnowledgeSearchIndex:
    TABLE = "knowledge_search_fts"

    def __init__(self, connection: sqlite3.Connection | None = None):
        self.connection = connection
        self._lock = threading.RLock()
        self.available = False
        if connection is not None:
            try:
                with self._lock:
                    connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search_fts USING fts5(record_id UNINDEXED, organization_id UNINDEXED, collection UNINDEXED, classification UNINDEXED, state UNINDEXED, searchable)")
                    connection.commit()
                self.available = True
            except sqlite3.OperationalError:
                self.available = False

    def upsert(self, *, collection: str, record: dict[str, Any]) -> None:
        if not self.available or collection not in SEARCH_COLLECTIONS:
            return
        searchable = " ".join(str(record.get(field, "")) for field in ("id", "question", "claim", "normalized_claim", "raw_excerpt", "ref", "kind", "citation", "context", "uncertainty", "ontology_refs"))
        with self._lock:
            self.connection.execute("DELETE FROM knowledge_search_fts WHERE record_id = ? AND organization_id = ? AND collection = ?", (record.get("id"), record.get("organization_id"), collection))
            self.connection.execute("INSERT INTO knowledge_search_fts(record_id, organization_id, collection, classification, state, searchable) VALUES (?, ?, ?, ?, ?, ?)", (record.get("id"), record.get("organization_id"), collection, record.get("classification", ""), record.get("state", record.get("status", "")), searchable))
            self.connection.commit()

    def search(self, *, organization_id: str, query: str = "", classification: str | None = None, state: str | None = None, collection: str | None = None) -> list[dict[str, str]]:
        if not self.available:
            return []
        clauses = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if query.strip():
            terms = re.findall(r"[A-Za-z0-9_:-]+", query.lower())
            if terms:
                clauses.append("knowledge_search_fts MATCH ?")
                params.append(" AND ".join(f'"{term.replace(chr(34), "")}"' for term in terms))
        for field, value in (("classification", classification), ("state", state), ("collection", collection)):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        with self._lock:
            rows = self.connection.execute(f"SELECT record_id, collection FROM knowledge_search_fts WHERE {' AND '.join(clauses)} ORDER BY record_id", params).fetchall()
        return [{"record_id":row[0], "collection":row[1]} for row in rows]


class KnowledgeRetrievalService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository
        self.index = KnowledgeSearchIndex(getattr(repository.repository, "connection", None))
        self.rebuild()

    def rebuild(self) -> int:
        count = 0
        for collection in SEARCH_COLLECTIONS:
            for record in self.repository.list(collection):
                self.index.upsert(collection=collection, record=record)
                count += 1
        return count

    def index_record(self, *, collection: str, record: dict[str, Any]) -> None:
        if collection not in SEARCH_COLLECTIONS:
            raise ValueError("collection is not searchable")
        if record.get("organization_id") != self.repository.organization_id:
            raise PermissionError("record organization does not match retrieval scope")
        self.index.upsert(collection=collection, record=record)

    def search(self, *, query: str = "", classification: str | None = None, state: str | None = None, collection: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        hits = self.index.search(organization_id=self.repository.organization_id, query=query, classification=classification, state=state, collection=collection)
        if not self.index.available:
            hits = []
            for source_collection in ((collection,) if collection else SEARCH_COLLECTIONS):
                if source_collection not in SEARCH_COLLECTIONS:
                    raise ValueError("collection is not searchable")
                for record in self.repository.list(source_collection):
                    text = " ".join(str(record.get(field, "")) for field in ("id", "question", "claim", "normalized_claim", "raw_excerpt", "ref", "kind", "context", "uncertainty"))
                    if query.strip() and query.lower() not in text.lower():
                        continue
                    if classification and record.get("classification") != classification:
                        continue
                    if state and record.get("state", record.get("status")) != state:
                        continue
                    hits.append({"record_id":record.get("id"), "collection":source_collection})
        results: list[dict[str, Any]] = []
        for hit in hits[:limit]:
            record = self.repository.get(hit["collection"], hit["record_id"])
            if record is not None:
                results.append({"collection":hit["collection"], "record":record})
        return results
