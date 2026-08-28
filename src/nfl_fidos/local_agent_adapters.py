"""Deterministic, non-provider adapters for local agent-runtime rehearsal."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .agent_runtime import AgentRuntime, AgentAdapter


def build_local_validation_adapter(*, agent_id: str, capability: str) -> AgentAdapter:
    """Return an adapter that proves routing without exposing or acting on payload data."""
    def adapter(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return {
            "status": "local_validation_only",
            "agent_id": agent_id,
            "capability": capability,
            "organization_id": context.get("organization_id"),
            "workflow_id": context.get("workflow_id"),
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
            "payload_keys": sorted(payload),
            "human_review_required": True,
            "external_provider_called": False,
            "canonical_write_performed": False,
            "production_implementation_allowed": False,
        }
    return adapter


def register_local_validation_adapters(
    runtime: AgentRuntime, bible: dict[str, Any], *, activate: bool = False,
) -> dict[str, Any]:
    """Register local adapters for every declared capability; activation is opt-in."""
    registered: list[str] = []
    active: list[str] = []
    for role in bible.get("roles", []):
        agent_id = role["id"]
        if runtime.registry.get(agent_id) is None:
            runtime.register_bible({"roles": [role]})
        for capability in role.get("authority", []):
            runtime.register_adapter(agent_id=agent_id, capability=capability, adapter=build_local_validation_adapter(agent_id=agent_id, capability=capability))
            registered.append(f"{agent_id}:{capability}")
            if activate:
                result = runtime.activate(agent_id=agent_id, capability=capability)
                if result.get("status") == "active":
                    active.append(f"{agent_id}:{capability}")
    return {
        "status": "ready",
        "registered_adapters": registered,
        "active_capabilities": active,
        "activation_performed": bool(active),
        "external_provider_called": False,
        "canonical_write_performed": False,
        "production_implementation_allowed": False,
    }
