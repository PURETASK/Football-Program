"""Bounded specialist-agent runtime with auditable dispatch and adapters."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .agent_contracts import create_handoff
from .agent_registry import AgentRegistry
from .tenant_repository import TenantRepository


AgentAdapter = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


def load_agent_bible(path: str | Path) -> dict[str, Any]:
    """Load the controlled agent organization artifact without mutating it."""
    source = Path(path)
    with source.open(encoding="utf-8") as handle:
        bible = json.load(handle)
    if not isinstance(bible, dict) or not isinstance(bible.get("roles"), list):
        raise ValueError("agent bible must contain a roles list")
    return deepcopy(bible)


class AgentRuntime:
    """Dispatch active agents only; never silently publishes or locks artifacts."""

    def __init__(self, repository: TenantRepository, *, registry: AgentRegistry | None = None):
        self.repository = repository
        self.registry = registry or AgentRegistry()
        self._adapters: dict[tuple[str, str], AgentAdapter] = {}

    def register_bible(self, bible: dict[str, Any]) -> list[dict[str, Any]]:
        registered = []
        for role in bible.get("roles", []):
            registered.append(self.registry.register(
                agent_id=role["id"], name=role["name"], family=role["family"],
                capabilities=role.get("authority", []), permissions=role.get("authority", []),
            ))
        return registered

    def register_adapter(self, *, agent_id: str, capability: str, adapter: AgentAdapter) -> None:
        if not callable(adapter):
            raise TypeError("adapter must be callable")
        agent = self.registry.get(agent_id)
        if agent is None:
            raise ValueError(f"unknown agent: {agent_id}")
        if capability not in agent.get("capabilities", []):
            raise ValueError(f"agent {agent_id} does not declare capability: {capability}")
        self._adapters[(agent_id, capability)] = adapter

    def activate(self, *, agent_id: str, capability: str) -> dict[str, Any]:
        return self.registry.activate(agent_id, requested_capability=capability)

    def dispatch(
        self,
        *,
        run_id: str,
        from_agent: str,
        family: str,
        capability: str,
        workflow_id: str,
        payload: dict[str, Any],
        requested_permissions: set[str] | None = None,
        human_review_required: bool = True,
    ) -> dict[str, Any]:
        if not run_id.startswith("RUN-"):
            raise ValueError("run_id must start with RUN-")
        if not payload:
            raise ValueError("payload cannot be empty")
        candidates = self.registry.resolve(family=family, capability=capability, active_only=True)
        if not candidates:
            result = {"id": run_id, "status": "blocked", "reason": "no active agent matches family and capability", "family": family, "capability": capability, "human_review_required": True}
            return self.repository.put("agent_runs", run_id, {"organization_id": self.repository.organization_id, **result}, actor=self.repository.actor, reason="agent_run_blocked")
        selected = candidates[0]
        handoff = create_handoff(
            handoff_id=f"HANDOFF-{run_id.removeprefix('RUN-')}", from_agent=from_agent, to_agent=selected["id"],
            workflow_id=workflow_id, payload=payload, requested_permissions=requested_permissions,
            human_review_required=human_review_required,
        )
        base = {"id": run_id, "organization_id": self.repository.organization_id, "agent_id": selected["id"], "family": family, "capability": capability, "handoff": handoff, "human_review_required": True}
        if handoff["status"] != "ready":
            return self.repository.put("agent_runs", run_id, {**base, "status": "rejected", "output": None}, actor=self.repository.actor, reason="agent_handoff_rejected")
        adapter = self._adapters.get((selected["id"], capability))
        if adapter is None:
            return self.repository.put("agent_runs", run_id, {**base, "status": "awaiting_adapter", "output": None}, actor=self.repository.actor, reason="agent_adapter_missing")
        try:
            output = adapter(deepcopy(payload), {"organization_id": self.repository.organization_id, "agent_id": selected["id"], "workflow_id": workflow_id})
        except Exception as exc:  # adapters must not take down the control plane
            return self.repository.put("agent_runs", run_id, {**base, "status": "failed", "output": None, "error": str(exc)}, actor=self.repository.actor, reason="agent_adapter_failed")
        if not isinstance(output, dict):
            return self.repository.put("agent_runs", run_id, {**base, "status": "failed", "output": None, "error": "adapter output must be an object"}, actor=self.repository.actor, reason="agent_output_invalid")
        return self.repository.put("agent_runs", run_id, {**base, "status": "completed", "output": deepcopy(output)}, actor=self.repository.actor, reason="agent_run_completed")
