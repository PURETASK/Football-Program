"""Tenant-scoped composition of authorized media and film QA evidence."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .film_intelligence import validate_film_qa


def build_organization_media_review(*, package_id: str, organization_id: str, season: str, assets: list[dict[str, Any]], clips: list[dict[str, Any]], playlists: list[dict[str, Any]], observations: list[dict[str, Any]], qa_id: str, reviewer: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not package_id.startswith("ORG-MEDIA-REVIEW-"):
        issues.append({"code":"ORG-MEDIA-ID","message":"Package id must use ORG-MEDIA-REVIEW- prefix","path":"id"})
    if not organization_id.startswith("ORG-") or not season or not reviewer:
        issues.append({"code":"ORG-MEDIA-METADATA","message":"Organization, season, and reviewer are required","path":"metadata"})
    if not assets or not clips or not playlists:
        issues.append({"code":"ORG-MEDIA-EMPTY","message":"At least one asset, clip, and playlist are required","path":"media"})
    asset_ids = {asset.get("id") for asset in assets}
    clip_ids = {clip.get("id") for clip in clips}
    for index, asset in enumerate(assets):
        if asset.get("organization_id", organization_id) != organization_id:
            issues.append({"code":"ORG-MEDIA-TENANCY","message":"Asset organization does not match package organization","path":f"assets[{index}].organization_id"})
        if asset.get("status") != "registered" or not asset.get("sha256") or not asset.get("uri"):
            issues.append({"code":"ORG-MEDIA-ASSET","message":"Assets must be registered with URI and SHA-256 integrity metadata","path":f"assets[{index}]"})
    for index, clip in enumerate(clips):
        if clip.get("asset_id") not in asset_ids or clip.get("status") != "ready":
            issues.append({"code":"ORG-MEDIA-CLIP","message":"Clip must be ready and reference a package asset","path":f"clips[{index}]"})
    for index, playlist in enumerate(playlists):
        if playlist.get("status") not in {"draft", "ready"} or not set(playlist.get("clip_ids", [])) <= clip_ids:
            issues.append({"code":"ORG-MEDIA-PLAYLIST","message":"Playlist must reference only package clips and remain reviewable","path":f"playlists[{index}]"})
    qa = validate_film_qa(qa_id=qa_id, clips=clips, observations=observations, reviewer=reviewer)
    if qa.get("status") != "passed":
        issues.extend({"code":"ORG-MEDIA-QA","message":item,"path":"qa"} for item in qa.get("issues", []))
    return {"id":package_id,"organization_id":organization_id,"season":season,"assets":deepcopy(assets),"clips":deepcopy(clips),"playlists":deepcopy(playlists),"observations":deepcopy(observations),"qa":qa,"reviewer":reviewer,"owner_decision_ref":owner_decision_ref,"approved_by":None,"status":"under_review" if not issues else "rejected","human_review_required":True,"created_at":datetime.now(timezone.utc).isoformat(),"issues":issues,"production_implementation_allowed":False,"stage_advance_authorized":False,"external_storage_deployed":False,"media_worker_called":False}


def approve_organization_media_review(*, package: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(package)
    issues: list[dict[str, str]] = []
    if package.get("status") != "under_review":
        issues.append({"code":"ORG-MEDIA-STATE","message":"Only an under_review media package can be validated","path":"status"})
    if approver_role != "program_owner":
        issues.append({"code":"ORG-MEDIA-ROLE","message":"Only a program_owner may validate organization media review","path":"approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code":"ORG-MEDIA-DECISION","message":"A DEC-* or APPROVAL-* reference is required","path":"decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status":"validated","human_review_required":False,"approved_by":approver,"owner_decision_ref":decision_ref,"approved_at":datetime.now(timezone.utc).isoformat(),"issues":[],"production_implementation_allowed":False,"stage_advance_authorized":False})
    return result
