"""Provider-neutral adapter registration and certification boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


ALLOWED_KINDS = {"analytics", "performance", "calendar", "media", "source", "search"}
ALLOWED_CAPABILITIES = {"analytics", "performance", "practice_resources", "media", "source_refresh", "search"}


def build_provider_adapter_registration(*, adapter_id: str, organization_id: str, provider: dict[str, Any], capabilities: list[str], credential_ref: str, healthcheck_ref: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not adapter_id.startswith("ADAPTER-"):
        issues.append({"code":"ADAPTER-ID","message":"Adapter id must use ADAPTER- prefix","path":"id"})
    if not organization_id.startswith("ORG-"):
        issues.append({"code":"ADAPTER-TENANCY","message":"organization_id must use ORG- prefix","path":"organization_id"})
    if provider.get("kind") not in ALLOWED_KINDS:
        issues.append({"code":"ADAPTER-KIND","message":"Provider kind is not approved","path":"provider.kind"})
    if provider.get("mode") != "read_only":
        issues.append({"code":"ADAPTER-MODE","message":"Provider mode must be read_only","path":"provider.mode"})
    source_ref = str(provider.get("source_ref", ""))
    if not source_ref.startswith(("SOURCE-", "PROVIDER-")):
        issues.append({"code":"ADAPTER-SOURCE","message":"Provider must reference an approved SOURCE-* or PROVIDER-* record","path":"provider.source_ref"})
    if not capabilities or any(capability not in ALLOWED_CAPABILITIES for capability in capabilities):
        issues.append({"code":"ADAPTER-CAPABILITY","message":"Capabilities must be non-empty and approved","path":"capabilities"})
    if not credential_ref.startswith(("SECRET-", "CREDENTIAL-")) or any(term in credential_ref.lower() for term in ("value", "token", "password")):
        issues.append({"code":"ADAPTER-CREDENTIAL","message":"Only a non-secret credential reference is permitted","path":"credential_ref"})
    if not healthcheck_ref:
        issues.append({"code":"ADAPTER-HEALTHCHECK","message":"Healthcheck evidence reference is required","path":"healthcheck_ref"})
    return {"id":adapter_id,"organization_id":organization_id,"provider":deepcopy(provider),"capabilities":list(capabilities),"credential_ref":credential_ref,"healthcheck_ref":healthcheck_ref,"owner_decision_ref":owner_decision_ref,"approved_by":None,"status":"under_review" if not issues else "rejected","human_review_required":True,"created_at":datetime.now(timezone.utc).isoformat(),"issues":issues,"external_provider_called":False,"external_registration_performed":False,"external_state_changed":False,"production_implementation_allowed":False,"stage_advance_authorized":False}


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
