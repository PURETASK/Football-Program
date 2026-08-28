"""Small provider-neutral security controls used by the local HTTP foundation.

These controls are deliberately explicit and testable.  They do not replace an
identity provider, WAF, KMS, or production database, but they establish the
contracts those adapters must preserve: bounded requests, redacted evidence,
tenant-safe identifiers, and signed artifacts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
from collections import deque
from copy import deepcopy
from typing import Any


SENSITIVE_KEY_PARTS = ("authorization", "access_token", "refresh_token", "api_key", "password", "secret", "credential", "private_key")


def redact_sensitive(value: Any) -> Any:
    """Return a deep redacted copy suitable for logs and observability sinks."""
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            output[key] = "[REDACTED]" if any(part in normalized for part in SENSITIVE_KEY_PARTS) else redact_sensitive(item)
        return output
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    return deepcopy(value)


def canonical_payload(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_payload(value: Any, *, secret: str) -> str:
    if not isinstance(secret, str) or len(secret) < 16:
        raise ValueError("a signing secret of at least 16 characters is required")
    return hmac.new(secret.encode("utf-8"), canonical_payload(value), hashlib.sha256).hexdigest()


def verify_payload_signature(value: Any, *, signature: str, secret: str) -> bool:
    if not isinstance(signature, str) or not signature:
        return False
    try:
        expected = sign_payload(value, secret=secret)
    except ValueError:
        return False
    return hmac.compare_digest(expected, signature)


class SlidingWindowRateLimiter:
    """Thread-safe in-memory limiter for the local HTTP adapter.

    A production edge/WAF can replace this implementation while keeping the
    result shape and policy semantics.  Keys must be an already-redacted
    identifier; callers should never store raw bearer tokens here.
    """

    def __init__(self, *, limit: int = 120, window_seconds: int = 60):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, now: float | None = None) -> dict[str, Any]:
        if not key:
            raise ValueError("rate-limit key is required")
        current = time.monotonic() if now is None else float(now)
        with self._lock:
            events = self._events.setdefault(key, deque())
            cutoff = current - self.window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            allowed = len(events) < self.limit
            if allowed:
                events.append(current)
            retry_after = 0 if allowed or not events else max(1, int(events[0] + self.window_seconds - current))
            return {"allowed": allowed, "limit": self.limit, "remaining": max(0, self.limit - len(events)), "retry_after_seconds": retry_after, "window_seconds": self.window_seconds}

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


def configured_rate_limit(environ: dict[str, str] | None = None) -> int:
    values = os.environ if environ is None else environ
    raw = values.get("NFL_FIDOS_RATE_LIMIT_PER_MINUTE", "120")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("NFL_FIDOS_RATE_LIMIT_PER_MINUTE must be an integer") from exc
    if value <= 0:
        raise ValueError("NFL_FIDOS_RATE_LIMIT_PER_MINUTE must be positive")
    return value
