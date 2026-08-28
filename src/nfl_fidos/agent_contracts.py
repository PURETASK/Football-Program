"""Callable-agent contracts, permissions, and auditable handoffs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


AGENT_PERMISSIONS = {
    "AGT-001": {"route", "assemble", "request_review"},
    "AGT-007": {"validate", "reject"},
    "AGT-013": {"cite", "explain", "escalate"},
    "AGT-014": {"review", "qualify", "escalate"},
    "AGT-016": {"allow", "deny", "escalate"},
}


@dataclass(frozen=True)
class HandoffIssue:
    code: str
    message: str
    path: str


def create_handoff(
    *,
    handoff_id: str,
    from_agent: str,
    to_agent: str,
    workflow_id: str,
    payload: dict[str, Any],
    requested_permissions: set[str] | None = None,
    human_review_required: bool = False,
) -> dict[str, Any]:
    """Create a handoff envelope; permissions are checked at creation time."""
    requested_permissions = requested_permissions or set()
    issues: list[HandoffIssue] = []
    if not handoff_id.startswith("HANDOFF-"):
        issues.append(HandoffIssue("HANDOFF-ID", "Handoff id must start with HANDOFF-", "handoff_id"))
    if not from_agent.startswith("AGT-") or not to_agent.startswith("AGT-"):
        issues.append(HandoffIssue("HANDOFF-AGENT", "Both handoff endpoints must be AGT-* roles", "agents"))
    allowed = AGENT_PERMISSIONS.get(to_agent, set())
    denied = sorted(requested_permissions - allowed)
    if denied:
        issues.append(HandoffIssue("HANDOFF-PERMISSION", f"Requested permissions are not allowed for {to_agent}: {', '.join(denied)}", "requested_permissions"))
    if not workflow_id.startswith("WF-"):
        issues.append(HandoffIssue("HANDOFF-WORKFLOW", "Workflow must be a WF-* identifier", "workflow_id"))
    if not payload:
        issues.append(HandoffIssue("HANDOFF-PAYLOAD", "Handoff payload cannot be empty", "payload"))
    return {
        "id": handoff_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "workflow_id": workflow_id,
        "payload": payload,
        "requested_permissions": sorted(requested_permissions),
        "human_review_required": human_review_required,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "rejected" if issues else "ready",
        "issues": [issue.__dict__ for issue in issues],
    }
