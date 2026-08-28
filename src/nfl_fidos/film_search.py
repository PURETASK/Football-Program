"""Optional persistent SQLite FTS index for organization-scoped film observations."""

from __future__ import annotations

import re
import sqlite3
import threading
from typing import Any


class FilmSearchIndex:
    TABLE = "film_observation_fts"

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self._lock = threading.RLock()
        self.available = False
        try:
            with self._lock:
                self.connection.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS film_observation_fts USING fts5(record_id UNINDEXED, organization_id UNINDEXED, team UNINDEXED, opponent UNINDEXED, domain UNINDEXED, label UNINDEXED, confidence UNINDEXED, searchable)"
                )
                self.connection.commit()
            self.available = True
        except sqlite3.OperationalError:
            # Some minimal SQLite builds omit FTS5; FilmRoomService retains its safe fallback.
            self.available = False

    def upsert(self, observation: dict[str, Any]) -> None:
        if not self.available:
            return
        context = observation.get("context", {})
        searchable = " ".join(str(observation.get(field, "")) for field in ("id", "label", "domain", "evidence")) + " " + str(context)
        with self._lock:
            self.connection.execute("DELETE FROM film_observation_fts WHERE record_id = ? AND organization_id = ?", (observation.get("id"), observation.get("organization_id")))
            self.connection.execute("INSERT INTO film_observation_fts(record_id, organization_id, team, opponent, domain, label, confidence, searchable) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (observation.get("id"), observation.get("organization_id"), context.get("team"), context.get("opponent"), observation.get("domain"), observation.get("label"), observation.get("confidence"), searchable))
            self.connection.commit()

    def search(self, *, organization_id: str, query: str = "", team: str | None = None, opponent: str | None = None, domain: str | None = None, label: str | None = None, confidence: str | None = None) -> list[str]:
        if not self.available:
            return []
        clauses = ["organization_id = ?"]
        params: list[Any] = [organization_id]
        if query.strip():
            terms = re.findall(r"[A-Za-z0-9_:-]+", query.lower())
            if terms:
                clauses.append("film_observation_fts MATCH ?")
                params.append(" AND ".join(f'"{term.replace(chr(34), "")}"' for term in terms))
        for field, value in (("team", team), ("opponent", opponent), ("domain", domain), ("label", label), ("confidence", confidence)):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        with self._lock:
            rows = self.connection.execute(f"SELECT record_id FROM film_observation_fts WHERE {' AND '.join(clauses)} ORDER BY record_id", params).fetchall()
        return [row[0] for row in rows]
