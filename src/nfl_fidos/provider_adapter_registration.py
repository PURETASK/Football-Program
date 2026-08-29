"""Provider-neutral adapter registration and certification boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


ALLOWED_KINDS = {"analytics", "performance", "calendar", "media", "source", "search"}
ALLOWED_CAPABILITIES = {"analytics", "performance", "practice_resources", "media", "source_refresh", "search"}


def build_provider_adapter_registration(*, adapter_id: str, organization_id: str, provider: dict[str, Any], capabilities: list[str], credential_ref: str, healthcheck_ref: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    adapter_value = adapter_id if isinstance(adapter_id, str) else ""
    organization_value = organization_id if isinstance(organization_id, str) else ""
    if not isinstance(adapter_id, str):
        issues.append({"code":"ADAPTER-ID-SHAPE","message":"Adapter id must be a string","path":"id"})
    if not adapter_value.startswith("ADAPTER-"):
        issues.append({"code":"ADAPTER-ID","message":"Adapter id must use ADAPTER- prefix","path":"id"})
    if not isinstance(organization_id, str):
        issues.append({"code":"ADAPTER-TENANCY-SHAPE","message":"organization_id must be a string","path":"organization_id"})
    if not organization_value.startswith("ORG-"):
        issues.append({"code":"ADAPTER-TENANCY","message":"organization_id must use ORG- prefix","path":"organization_id"})
    provider_value = provider if isinstance(provider, dict) else {}
    if not isinstance(provider, dict):
        issues.append({"code":"ADAPTER-PROVIDER","message":"Provider configuration must be an object","path":"provider"})
    if provider_value.get("kind") not in ALLOWED_KINDS:
        issues.append({"code":"ADAPTER-KIND","message":"Provider kind is not approved","path":"provider.kind"})
    if provider_value.get("mode") != "read_only":
        issues.append({"code":"ADAPTER-MODE","message":"Provider mode must be read_only","path":"provider.mode"})
    source_ref = str(provider_value.get("source_ref", ""))
    if not source_ref.startswith(("SOURCE-", "PROVIDER-")):
        issues.append({"code":"ADAPTER-SOURCE","message":"Provider must reference an approved SOURCE-* or PROVIDER-* record","path":"provider.source_ref"})
    capability_values = capabilities if isinstance(capabilities, list) else []
    if not isinstance(capabilities, list):
        issues.append({"code":"ADAPTER-CAPABILITY-SHAPE","message":"Capabilities must be a list","path":"capabilities"})
    if not capability_values or any(not isinstance(capability, str) or capability not in ALLOWED_CAPABILITIES for capability in capability_values):
        issues.append({"code":"ADAPTER-CAPABILITY","message":"Capabilities must be non-empty and approved","path":"capabilities"})
    credential_value = credential_ref if isinstance(credential_ref, str) else ""
    if not isinstance(credential_ref, str):
        issues.append({"code":"ADAPTER-CREDENTIAL-SHAPE","message":"Credential reference must be a non-secret string reference","path":"credential_ref"})
    if not credential_value.startswith(("SECRET-", "CREDENTIAL-")) or any(term in credential_value.lower() for term in ("value", "token", "password")):
        issues.append({"code":"ADAPTER-CREDENTIAL","message":"Only a non-secret credential reference is permitted","path":"credential_ref"})
    healthcheck_value = healthcheck_ref if isinstance(healthcheck_ref, str) else ""
    if not isinstance(healthcheck_ref, str):
        issues.append({"code":"ADAPTER-HEALTHCHECK-SHAPE","message":"Healthcheck evidence reference must be a string","path":"healthcheck_ref"})
    if not healthcheck_value.strip():
        issues.append({"code":"ADAPTER-HEALTHCHECK","message":"Healthcheck evidence reference is required","path":"healthcheck_ref"})
    return {"id":adapter_value,"organization_id":organization_value,"provider":deepcopy(provider_value),"capabilities":list(capability_values),"credential_ref":credential_value,"healthcheck_ref":healthcheck_value,"owner_decision_ref":owner_decision_ref,"approved_by":None,"status":"under_review" if not issues else "rejected","human_review_required":True,"created_at":datetime.now(timezone.utc).isoformat(),"issues":issues,"external_provider_called":False,"external_registration_performed":False,"external_state_changed":False,"production_implementation_allowed":False,"stage_advance_authorized":False}


def approve_provider_adapter_registration(*, registration: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(registration)
    issues: list[dict[str, str]] = []
    if registration.get("status") != "under_review":
        issues.append({"code":"ADAPTER-STATE","message":"Only an under_review adapter registration can be validated","path":"status"})
    if approver_role != "program_owner":
        issues.append({"code":"ADAPTER-ROLE","message":"Only a program_owner may validate an adapter registration","path":"approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code":"ADAPTER-DECISION","message":"A DEC-* or APPROVAL-* reference is required","path":"decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status":"validated","human_review_required":False,"approved_by":approver,"owner_decision_ref":decision_ref,"approved_at":datetime.now(timezone.utc).isoformat(),"issues":[],"external_provider_called":False,"external_registration_performed":False,"external_state_changed":False,"production_implementation_allowed":False,"stage_advance_authorized":False})
    return result
