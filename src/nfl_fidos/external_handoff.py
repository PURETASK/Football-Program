"""Build a value-free handoff packet for remaining external Master Plan actions."""

from __future__ import annotations

from typing import Any


def _category(text: str) -> tuple[str, str, list[str]]:
    value = text.lower()
    if "owner" in value or "approval" in value or "acceptance" in value:
        return "program_owner", "Review evidence and submit the applicable authenticated approval or acceptance record", ["authorized program-owner identity", "rationale", "evidence references", "ISO-8601 decision timestamp"]
    if "organization" in value or "staff records" in value or "learning data" in value or "team records" in value:
        return "operating_organization", "Provide authorized organization-scoped records and source corpus", ["organization identity", "season", "authorized source references", "privacy-approved records"]
    if "provider" in value or "credential" in value or "calendar" in value or "storage" in value or "scheduler" in value or "monitoring" in value or "deployment" in value:
        return "deployment_owner", "Configure and validate the provider or deployment environment", ["provider selection", "approved secret/credential reference", "environment registration evidence", "rollback evidence"]
    if "pilot" in value or "stakeholder" in value or "rollout" in value:
        return "pilot_stakeholders", "Conduct the authorized pilot or stakeholder validation", ["named participants", "approved organization", "acceptance evidence", "rollback confirmation"]
    return "program_owner_and_deployment_owner", "Review the requirement and provide the applicable external evidence", ["named accountable owner", "evidence reference", "decision timestamp"]


def build_external_action_handoff(*, ledger: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for stage in ledger.get("stages", []):
        for item in stage.get("remaining", []):
            owner, action, inputs = _category(item)
            actions.append({"stage":stage.get("stage"), "requirement":item, "responsible_authority":owner, "next_action":action, "required_inputs":inputs, "status":"awaiting_external_evidence"})
    return {"packet_id":"NFL-FIDOS-EXTERNAL-HANDOFF-001", "status":"awaiting_external_authority" if actions else "no_remaining_actions", "current_stage":manifest.get("current_stage"), "current_work_package":manifest.get("current_work_package"), "production_implementation_allowed":manifest.get("production_implementation_allowed"), "stage_advance_authorized":False, "external_state_changed":False, "actions":actions}
