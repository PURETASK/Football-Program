"""Controlled first-organization and terminology-bundle initialization."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .organization import build_organization_context
from .organization_terminology import validate_organization_terminology


def build_onboarding_package(
    *, organization_id: str, name: str, season: str, team_id: str, people: list[dict[str, Any]],
    terminology_version: str, owner: str, source: dict[str, str], terminology_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = build_organization_context(organization_id=organization_id, name=name, season=season, people=people, terminology_version=terminology_version, owner=owner, source=source)
    bundle = deepcopy(terminology_bundle) if terminology_bundle is not None else {
        "id":f"TERM-BUNDLE-{organization_id}-{season}", "organization_id":organization_id, "team_id":team_id,
        "season":season, "version":terminology_version, "owner":owner, "source_refs":[source.get("ref", "")],
        "approval_ref":"PENDING-OWNER-APPROVAL", "aliases":[], "status":"draft",
    }
    bundle.setdefault("organization_id", organization_id)
    bundle.setdefault("team_id", team_id)
    bundle.setdefault("season", season)
    bundle.setdefault("version", terminology_version)
    bundle.setdefault("owner", owner)
    bundle_result = validate_organization_terminology(bundle)
    issues = list(context.get("issues", []))
    if not team_id.startswith("TEAM-"):
        issues.append({"code":"ORG-TEAM-ID", "message":"team_id must start with TEAM-", "path":"team_id"})
    if bundle_result["status"] != "valid":
        issues.extend({"code":"ORG-TERMINOLOGY", "message":error, "path":"terminology_bundle"} for error in bundle_result["errors"])
    return {
        "organization": context,
        "terminology_bundle": bundle,
        "status":"draft" if not issues else "rejected",
        "issues":issues,
        "approval_required":True,
        "production_implementation_allowed":False,
        "human_review_required":True,
    }


def approve_onboarding_package(*, organization: dict[str, Any], terminology_bundle: dict[str, Any], approver: str, decision_ref: str) -> dict[str, Any]:
    """Approve draft organization artifacts through an explicit owner decision."""
    issues: list[dict[str, str]] = []
    if not approver:
        issues.append({"code":"ORG-APPROVAL-ACTOR", "message":"Approver is required", "path":"approver"})
    if not decision_ref.startswith("DEC-"):
        issues.append({"code":"ORG-APPROVAL-DECISION", "message":"Approval must reference a DEC-* decision record", "path":"decision_ref"})
    if organization.get("status") != "draft":
        issues.append({"code":"ORG-APPROVAL-STATE", "message":"Only draft organization contexts can be approved", "path":"organization.status"})
    if terminology_bundle.get("status") not in {"draft", "under_review"}:
        issues.append({"code":"ORG-TERMINOLOGY-STATE", "message":"Only draft or under-review terminology bundles can be approved", "path":"terminology_bundle.status"})
    if organization.get("id") != terminology_bundle.get("organization_id"):
        issues.append({"code":"ORG-APPROVAL-SCOPE", "message":"Organization and terminology bundle must share organization scope", "path":"scope"})
    approved_at = datetime.now(timezone.utc).isoformat()
    if issues:
        return {"status":"rejected", "issues":issues, "production_implementation_allowed":False, "human_review_required":True}
    context = deepcopy(organization)
    context.update({"status":"active", "approved_by":approver, "approval_ref":decision_ref, "approved_at":approved_at, "organization_id":context.get("id")})
    bundle = deepcopy(terminology_bundle)
    bundle.update({"status":"approved", "approval_ref":decision_ref, "approved_by":approver, "approved_at":approved_at})
    return {"status":"approved", "organization":context, "terminology_bundle":bundle, "decision_ref":decision_ref, "production_implementation_allowed":False, "human_review_required":False, "issues":[]}
