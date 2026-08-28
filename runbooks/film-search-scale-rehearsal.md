# Film search scale rehearsal

Run `python scripts/film_search_scale_rehearsal.py --observations-per-tenant 250` to exercise the temporary SQLite FTS5 index with two synthetic organizations.

The rehearsal checks bounded indexing, filtered search counts, persistence after reopening the database, and cross-organization isolation. It uses a temporary workspace and never contacts a provider, changes external state, or authorizes production search infrastructure.

If FTS5 is unavailable, the existing Film Room service retains its safe JSON fallback; a production search deployment must separately validate the chosen database build, indexing capacity, backup/restore, retention, and monitoring behavior.
