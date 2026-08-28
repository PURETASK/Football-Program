"""Tenant-scoped organization play corpus compilation and approval boundary."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .play_compiler import compile_play


def build_organization_play_corpus(*, corpus_id: str, organization_id: str, team_context: str, season: str, plays: list[dict[str, Any]], source_refs: list[str], compiler: str, owner_decision_ref: str | None = None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not corpus_id.startswith("ORG-PLAY-CORPUS-"):
        errors.append({"code": "ORG-PLAY-ID", "message": "Corpus id must use ORG-PLAY-CORPUS- prefix", "path": "id"})
    if not organization_id.startswith("ORG-"):
        errors.append({"code": "ORG-PLAY-ORG", "message": "organization_id must use ORG- prefix", "path": "organization_id"})
    if not team_context or not season or not compiler:
        errors.append({"code": "ORG-PLAY-METADATA", "message": "team_context, season, and compiler are required", "path": "metadata"})
    if not source_refs:
        errors.append({"code": "ORG-PLAY-SOURCE", "message": "source_refs are required", "path": "source_refs"})
    if not plays:
        errors.append({"code": "ORG-PLAY-PLAYS", "message": "at least one play is required", "path": "plays"})
    compiled: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, play in enumerate(plays):
        result = compile_play(play)
        issue_list = [{"code": issue.code, "message": issue.message, "path": issue.path} for issue in result.issues]
        if play.get("id") in seen:
            issue_list.append({"code": "ORG-PLAY-DUPLICATE", "message": "Duplicate play id", "path": f"plays[{index}].id"})
        seen.add(play.get("id"))
        if play.get("team_context") != team_context:
            issue_list.append({"code": "ORG-PLAY-TEAM", "message": "Play team_context must match corpus team_context", "path": f"plays[{index}].team_context"})
        source = play.get("source", {})
        if source.get("ref") not in source_refs:
            issue_list.append({"code": "ORG-PLAY-SOURCE-LINK", "message": "Play source ref must be listed in corpus source_refs", "path": f"plays[{index}].source.ref"})
        compiled.append({"play_id": play.get("id"), "status": "validated" if not issue_list else "rejected", "normalized_play": result.normalized_play, "issues": issue_list})
        errors.extend({**issue, "path": f"plays[{index}].{issue['path']}"} for issue in issue_list)
    return {"id": corpus_id, "organization_id": organization_id, "team_context": team_context, "season": season, "source_refs": list(source_refs), "plays": compiled, "compiler": compiler, "status": "under_review" if not errors else "rejected", "human_review_required": True, "owner_decision_ref": owner_decision_ref, "approved_by": None, "created_at": datetime.now(timezone.utc).isoformat(), "issues": errors}


def approve_organization_play_corpus(*, corpus: dict[str, Any], approver: str, approver_role: str, decision_ref: str) -> dict[str, Any]:
    result = deepcopy(corpus)
    issues: list[dict[str, str]] = []
    if corpus.get("status") != "under_review":
        issues.append({"code": "ORG-PLAY-STATE", "message": "Only an under_review corpus can be validated", "path": "status"})
    if approver_role != "program_owner":
        issues.append({"code": "ORG-PLAY-ROLE", "message": "Only a program_owner may validate an organization play corpus", "path": "approver_role"})
    if not decision_ref.startswith(("DEC-", "APPROVAL-")):
        issues.append({"code": "ORG-PLAY-DECISION", "message": "A DEC-* or APPROVAL-* reference is required", "path": "decision_ref"})
    if issues:
        result["issues"] = list(result.get("issues", [])) + issues
        return result
    result.update({"status": "validated", "human_review_required": False, "approved_by": approver, "owner_decision_ref": decision_ref, "approved_at": datetime.now(timezone.utc).isoformat(), "production_implementation_allowed": False, "stage_advance_authorized": False, "issues": []})
    return result
