"""Callable specialist-agent registry and lifecycle controls."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, dict[str, Any]] = {}
        self._active: set[str] = set()

    def register(self, *, agent_id: str, name: str, family: str, capabilities: list[str], permissions: list[str]) -> dict[str, Any]:
        issues: list[dict[str, str]] = []
        if not agent_id.startswith("AGT-"):
            issues.append({"code": "AGENT-ID", "message": "Agent id must start with AGT-", "path": "agent_id"})
        if not name or not family or not capabilities:
            issues.append({"code": "AGENT-METADATA", "message": "Name, family, and capabilities are required", "path": "metadata"})
        if agent_id in self._agents:
            issues.append({"code": "AGENT-DUPLICATE", "message": "Agent id is already registered", "path": "agent_id"})
        record = {
            "id": agent_id, "name": name, "family": family, "capabilities": capabilities,
            "permissions": permissions, "lifecycle": "callable", "status": "invalid" if issues else "registered", "issues": issues,
        }
        if not issues:
            self._agents[agent_id] = record
        return deepcopy(record)

    def activate(self, agent_id: str, *, requested_capability: str) -> dict[str, Any]:
        agent = self._agents.get(agent_id)
        if not agent:
            return {"status": "rejected", "code": "AGENT-UNKNOWN", "agent_id": agent_id}
        if requested_capability not in agent["capabilities"]:
            return {"status": "rejected", "code": "AGENT-CAPABILITY", "agent_id": agent_id, "requested_capability": requested_capability}
        self._active.add(agent_id)
        agent["lifecycle"] = "active"
        return {"status": "active", "agent": deepcopy(agent), "requested_capability": requested_capability}

    def deactivate(self, agent_id: str) -> dict[str, Any]:
        agent = self._agents.get(agent_id)
        if not agent:
            return {"status": "rejected", "code": "AGENT-UNKNOWN", "agent_id": agent_id}
        self._active.discard(agent_id)
        agent["lifecycle"] = "deactivated"
        return {"status": "deactivated", "agent": deepcopy(agent)}

    def resolve(self, *, family: str, capability: str, active_only: bool = False) -> list[dict[str, Any]]:
        candidates = [agent for agent in self._agents.values() if agent["family"] == family and capability in agent["capabilities"]]
        if active_only:
            candidates = [agent for agent in candidates if agent["id"] in self._active]
        return deepcopy(candidates)

    def active_ids(self) -> list[str]:
        return sorted(self._active)

    def get(self, agent_id: str) -> dict[str, Any] | None:
        """Return a defensive copy of a registered agent, if present."""
        agent = self._agents.get(agent_id)
        return deepcopy(agent) if agent is not None else None
