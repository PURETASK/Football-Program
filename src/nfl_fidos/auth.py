"""Small signed-token authentication and organization-scope primitives.

This is a dependency-free local/validation implementation. Production
deployment may replace token issuance with an identity provider, but the
principal and tenancy contract remains the same.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from .access import ROLE_PERMISSIONS


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str
    organization_id: str
    expires_at: int


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(*, subject: str, role: str, organization_id: str, secret: str, ttl_seconds: int = 3600, now: int | None = None) -> str:
    if not subject or role not in ROLE_PERMISSIONS or not organization_id or not secret or ttl_seconds <= 0:
        raise ValueError("subject, known role, organization, secret, and positive TTL are required")
    issued = int(time.time()) if now is None else now
    payload = {"sub": subject, "role": role, "org": organization_id, "exp": issued + ttl_seconds}
    encoded = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_encode(signature)}"


def verify_token(token: str, *, secret: str, now: int | None = None) -> Principal:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_decode(signature), expected):
            raise ValueError("invalid token signature")
        payload: dict[str, Any] = json.loads(_decode(encoded).decode("utf-8"))
        principal = Principal(subject=payload["sub"], role=payload["role"], organization_id=payload["org"], expires_at=int(payload["exp"]))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid authentication token") from exc
    current = int(time.time()) if now is None else now
    if principal.role not in ROLE_PERMISSIONS or not principal.subject or not principal.organization_id or principal.expires_at <= current:
        raise ValueError("expired or invalid authentication token")
    return principal


def authorize_principal(*, principal: Principal, action: str, organization_id: str) -> dict[str, Any]:
    if not organization_id or principal.organization_id != organization_id:
        return {"allowed": False, "status": "denied", "reason": "organization scope mismatch"}
    permissions = ROLE_PERMISSIONS.get(principal.role, set())
    allowed = (
        action in permissions
        or action in {"read_own_development", "read_assigned_playbook"}
        or (action.startswith("read_") and "read_all" in permissions)
    )
    return {"allowed": allowed, "status": "allowed" if allowed else "denied", "reason": None if allowed else "role lacks action", "organization_id": organization_id, "subject": principal.subject}
