"""Bounded, evidence-bearing SQLite backup scheduling."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .database_operations import backup_sqlite_database, plan_backup_retention, verify_sqlite_database


class BackupScheduler:
    def __init__(self, *, control_root: str | Path | None = None, environment: str = "local"):
        self.control_root = Path(control_root) if control_root else Path(__file__).resolve().parents[2]
        self.environment = environment

    def _production_allowed(self) -> bool:
        try:
            manifest = json.loads((self.control_root / "control" / "manifest.json").read_text(encoding="utf-8"))
            return bool(manifest.get("production_implementation_allowed"))
        except (OSError, ValueError):
            return False

    @staticmethod
    def _backup_files(directory: Path) -> list[Path]:
        return sorted((item for item in directory.glob("*.sqlite*") if item.is_file()), key=lambda item: item.stat().st_mtime, reverse=True)

    def plan(self, *, source: str | Path, destination_directory: str | Path, now: datetime | None = None, interval_hours: int = 24, keep: int = 7) -> dict[str, Any]:
        if interval_hours <= 0 or keep <= 0:
            raise ValueError("interval_hours and keep must be positive")
        source_path = Path(source).resolve()
        destination = Path(destination_directory).resolve()
        reference = now or datetime.now(timezone.utc)
        existing = self._backup_files(destination) if destination.exists() else []
        latest_at = datetime.fromtimestamp(existing[0].stat().st_mtime, tz=timezone.utc) if existing else None
        due = latest_at is None or reference - latest_at >= timedelta(hours=interval_hours)
        verification = verify_sqlite_database(source_path)
        return {
            "id": f"BACKUP-PLAN-{reference.strftime('%Y%m%d%H%M%S%f')}",
            "environment": self.environment,
            "source": str(source_path),
            "destination_directory": str(destination),
            "as_of": reference.isoformat(),
            "interval_hours": interval_hours,
            "keep": keep,
            "latest_backup": str(existing[0]) if existing else None,
            "latest_backup_at": latest_at.isoformat() if latest_at else None,
            "due": due,
            "source_verification": verification,
            "retention_plan": plan_backup_retention(destination, keep=keep) if destination.exists() else {"directory": str(destination), "keep": keep, "retained": [], "candidates": [], "destructive_action_required": True},
            "destructive_action_required": False,
            "dry_run": True,
        }

    def run(self, *, source: str | Path, destination_directory: str | Path, actor: str, execute: bool = False, now: datetime | None = None, interval_hours: int = 24, keep: int = 7) -> dict[str, Any]:
        plan = self.plan(source=source, destination_directory=destination_directory, now=now, interval_hours=interval_hours, keep=keep)
        if not execute or not plan["due"]:
            return plan
        if self.environment == "production" and not self._production_allowed():
            return {**plan, "status": "blocked", "blocker": "production implementation is disabled by the Stage 0 control gate", "dry_run": False}
        reference = now or datetime.now(timezone.utc)
        destination = Path(destination_directory).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        backup_path = destination / f"nfl-fidos-{reference.strftime('%Y%m%dT%H%M%SZ')}.sqlite3"
        result = backup_sqlite_database(source, backup_path, actor=actor)
        return {**plan, "status": "completed" if result.get("status") == "created" and result.get("content_match") else "invalid", "backup": result, "dry_run": False}
