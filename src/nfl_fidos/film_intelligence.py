"""Stage 14 film observation, grading, correction, playlist, and QA contracts."""

from __future__ import annotations

from typing import Any


TAG_DOMAINS = {"personnel", "formation", "motion", "front", "coverage", "pressure", "concept", "result", "technique", "situation"}
CONFIDENCE = {"low", "moderate", "high"}
CORRECTION_STATES = {"uncorrected", "under_review", "corrected", "rejected"}
FILM_LINK_TYPES = {"playbook", "scouting", "player_development", "game_plan", "analytics"}


def normalize_film_links(linked_record_refs: Any) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Normalize cross-workspace evidence links without inventing target records."""
    if linked_record_refs in (None, ""):
        return [], []
    if not isinstance(linked_record_refs, list):
        return [], [{"code": "FILM-LINKS-TYPE", "message": "linked_record_refs must be a list", "path": "linked_record_refs"}]
    normalized: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    for index, raw in enumerate(linked_record_refs):
        if not isinstance(raw, dict):
            issues.append({"code": "FILM-LINK-ITEM", "message": "each film link must be an object", "path": f"linked_record_refs[{index}]"})
            continue
        record_type = str(raw.get("record_type") or raw.get("type") or "").strip().lower()
        record_id = str(raw.get("record_id") or raw.get("id") or "").strip()
        label = str(raw.get("label") or "").strip()
        if record_type not in FILM_LINK_TYPES:
            issues.append({"code": "FILM-LINK-TARGET", "message": f"film links must target one of {sorted(FILM_LINK_TYPES)}", "path": f"linked_record_refs[{index}].record_type"})
        if not record_id:
            issues.append({"code": "FILM-LINK-ID", "message": "film link record_id is required", "path": f"linked_record_refs[{index}].record_id"})
        if record_type in FILM_LINK_TYPES and record_id:
            normalized.append({"record_type": record_type, "record_id": record_id, "label": label or record_id})
    return normalized, issues


def build_film_observation(*, observation_id: str, clip_id: str, asset_id: str, domain: str, label: str, team: str, opponent: str, situation: dict[str, Any], source_frame: str, confidence: str, observed_or_inferred: str, annotator: str, evidence: str, linked_record_refs: Any = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not observation_id.startswith("FILM-OBS-"):
        issues.append({"code":"FILM-OBS-ID", "message":"Observation id must start with FILM-OBS-", "path":"observation_id"})
    if not clip_id.startswith("CLIP-") or not asset_id.startswith("FILM-"):
        issues.append({"code":"FILM-OBS-SOURCE", "message":"Clip and film asset references are required", "path":"source"})
    if domain not in TAG_DOMAINS:
        issues.append({"code":"FILM-OBS-DOMAIN", "message":"Unknown film tag domain", "path":"domain"})
    if not label or not team or not opponent or not situation or not source_frame or not annotator or not evidence:
        issues.append({"code":"FILM-OBS-CONTEXT", "message":"Observation label, context, source frame, annotator, and evidence are required", "path":"context"})
    if confidence not in CONFIDENCE:
        issues.append({"code":"FILM-OBS-CONFIDENCE", "message":"Unknown confidence", "path":"confidence"})
    if observed_or_inferred not in {"observed", "measured", "reported", "inferred", "hypothesized"}:
        issues.append({"code":"FILM-OBS-CLASSIFICATION", "message":"Observation classification is invalid", "path":"observed_or_inferred"})
    normalized_links, link_issues = normalize_film_links(linked_record_refs)
    issues.extend(link_issues)
    return {"id":observation_id, "clip_id":clip_id, "asset_id":asset_id, "domain":domain, "label":label, "context":{"team":team,"opponent":opponent,"situation":situation}, "source_frame":source_frame, "confidence":confidence, "classification":observed_or_inferred, "annotator":annotator, "evidence":evidence, "linked_record_refs":normalized_links, "correction":{"state":"uncorrected","corrected_by":None,"reason":None}, "status":"invalid" if issues else "ready_for_review", "issues":issues}


def build_assignment_grade(*, grade_id: str, observation: dict[str, Any], player_id: str, assignment: str, grade: str, assignment_basis: str, confidence: str, evidence_refs: list[str], grader: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not grade_id.startswith("GRADE-") or not player_id or not assignment or not grader or not evidence_refs:
        issues.append({"code":"FILM-GRADE-CONTEXT", "message":"Grade identity, assignment, grader, and evidence are required", "path":"context"})
    if grade not in {"plus", "neutral", "minus", "not_available"}:
        issues.append({"code":"FILM-GRADE-VALUE", "message":"Unknown grade", "path":"grade"})
    if confidence not in CONFIDENCE:
        issues.append({"code":"FILM-GRADE-CONFIDENCE", "message":"Unknown confidence", "path":"confidence"})
    if assignment_basis not in {"observed", "team_playbook", "coach_annotation", "inferred"}:
        issues.append({"code":"FILM-GRADE-BASIS", "message":"Unknown assignment basis", "path":"assignment_basis"})
    if assignment_basis == "inferred" and confidence == "low":
        issues.append({"code":"FILM-GRADE-INFERENCE", "message":"Low-confidence inferred assignments cannot receive a definitive grade", "path":"grade"})
    return {"id":grade_id, "observation_id":observation.get("id"), "player_id":player_id, "assignment":assignment, "grade":grade, "assignment_basis":assignment_basis, "confidence":confidence, "evidence_refs":evidence_refs, "grader":grader, "status":"needs_review" if issues else "under_review", "issues":issues, "human_review_required":True}


def correct_film_observation(*, observation: dict[str, Any], corrected_label: str, corrected_by: str, reason: str, correction_state: str = "corrected") -> dict[str, Any]:
    if correction_state not in CORRECTION_STATES or not corrected_label or not corrected_by or not reason:
        raise ValueError({"code":"FILM-CORRECTION-INCOMPLETE", "message":"Correction label, reviewer, reason, and valid state are required"})
    output = dict(observation)
    output["label"] = corrected_label
    output["correction"] = {"state":correction_state, "corrected_by":corrected_by, "reason":reason}
    output["status"] = "corrected" if correction_state == "corrected" else "under_review" if correction_state == "under_review" else correction_state
    return output


def build_film_playlist(*, playlist_id: str, name: str, purpose: str, clip_ids: list[str], filters: dict[str, Any], owner: str, access_roles: list[str]) -> dict[str, Any]:
    issues: list[str] = []
    if not playlist_id.startswith("PLAYLIST-") or not name or not purpose or not clip_ids or not owner or not access_roles:
        issues.append("playlist identity, purpose, clips, owner, and access roles are required")
    if any(not clip_id.startswith("CLIP-") for clip_id in clip_ids):
        issues.append("all playlist references must be CLIP-* ids")
    return {"id":playlist_id, "name":name, "purpose":purpose, "clip_ids":clip_ids, "filters":filters, "owner":owner, "access_roles":access_roles, "status":"invalid" if issues else "draft", "issues":issues}


def validate_film_qa(*, qa_id: str, clips: list[dict[str, Any]], observations: list[dict[str, Any]], reviewer: str) -> dict[str, Any]:
    issues: list[str] = []
    valid_clip_ids = {clip.get("id") for clip in clips if clip.get("status") in {"ready", "registered"}}
    for observation in observations:
        if observation.get("clip_id") not in valid_clip_ids:
            issues.append(f"observation {observation.get('id')} references unavailable clip")
        if observation.get("confidence") == "low" and observation.get("classification") == "inferred":
            issues.append(f"observation {observation.get('id')} is low-confidence inferred evidence")
    return {"id":qa_id, "reviewer":reviewer, "clip_count":len(clips), "observation_count":len(observations), "status":"passed" if reviewer and not issues else "needs_correction", "issues":issues, "manual_correction_workflow":True}
