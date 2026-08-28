"""Validated environment configuration for local, validation, and production runtimes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .secret_manager import resolve_secret_manager_mount


@dataclass(frozen=True)
class RuntimeConfig:
    environment: str
    host: str
    port: int
    database_path: Path
    auth_secret: str
    ffmpeg_binary: str
    ffprobe_binary: str
    observability_path: Path


def resolve_auth_secret(*, environ: dict[str, str] | None = None) -> str:
    values = os.environ if environ is None else environ
    if values.get("NFL_FIDOS_SECRET_PROVIDER", "").strip() or values.get("NFL_FIDOS_SECRET_MANAGER_FILE", "").strip():
        return resolve_secret_manager_mount(environ=values)
    secret = values.get("NFL_FIDOS_AUTH_SECRET", "")
    secret_file = values.get("NFL_FIDOS_AUTH_SECRET_FILE", "")
    if secret_file:
        try:
            secret = Path(secret_file).expanduser().resolve().read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(f"NFL_FIDOS_AUTH_SECRET_FILE could not be read: {exc}") from exc
    return secret


def load_config(*, environ: dict[str, str] | None = None, require_auth_secret: bool = True) -> RuntimeConfig:
    values = os.environ if environ is None else environ
    environment = values.get("NFL_FIDOS_ENV", "local").lower()
    if environment not in {"local", "validation", "production"}:
        raise ValueError("NFL_FIDOS_ENV must be local, validation, or production")
    try:
        port = int(values.get("NFL_FIDOS_PORT", "8080"))
    except ValueError as exc:
        raise ValueError("NFL_FIDOS_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("NFL_FIDOS_PORT must be between 1 and 65535")
    secret = resolve_auth_secret(environ=values)
    if require_auth_secret and not secret:
        raise ValueError("NFL_FIDOS_AUTH_SECRET is required")
    if environment == "production" and len(secret) < 32:
        raise ValueError("production auth secret must contain at least 32 characters")
    database = Path(values.get("NFL_FIDOS_DATABASE", ".runtime/nfl_fidos.sqlite3")).expanduser().resolve()
    ffmpeg = values.get("NFL_FIDOS_FFMPEG", "ffmpeg")
    ffprobe = values.get("NFL_FIDOS_FFPROBE", "ffprobe")
    if not ffmpeg or not ffprobe:
        raise ValueError("NFL_FIDOS_FFMPEG and NFL_FIDOS_FFPROBE must be non-empty")
    observability_path = Path(values.get("NFL_FIDOS_OBSERVABILITY_PATH", ".runtime/observability.jsonl")).expanduser().resolve()
    return RuntimeConfig(environment=environment, host=values.get("NFL_FIDOS_HOST", "127.0.0.1"), port=port, database_path=database, auth_secret=secret, ffmpeg_binary=ffmpeg, ffprobe_binary=ffprobe, observability_path=observability_path)
