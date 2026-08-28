"""Opponent scouting and competitive-intelligence workspace."""

from __future__ import annotations

from typing import Any

from .scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report
from .tenant_repository import TenantRepository

TENDENCY_DIMENSIONS = ("down", "distance", "field_zone", "personnel", "formation", "motion", "front", "coverage", "pressure")


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_strings(item))
        return values
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        for key in ("id", "ref", "reference", "uri", "title", "statement"):
            if value.get(key):
                return [str(value[key])]
    return []


def _first(*values: Any) -> Any:
    return next((value for value in values if value not in (None, "")), None)


def _text(value: Any, fallback: str = "") -> str:
    values = _strings(value)
    return values[0] if values else fallback


def _number(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _stance(value: Any) -> str | None:
    result = _text(value).lower().replace("-", "_").replace(" ", "_")
    return result or None


def _review_gate(*, sample_size: int, confidence: str, evidence_refs: list[str], contradictions: list[str]) -> str:
    if contradictions:
        return "contradiction"
    if sample_size < 10:
        return "low_sample"
    if not evidence_refs:
        return "missing_evidence"
    if confidence.lower() in {"low", "unrated", "unknown", "not_set"}:
        return "low_confidence"
    return "ready_for_staff_review"


def build_tendency_explorer(*, reports: list[dict[str, Any]], opponent: str | None = None, filters: dict[str, str] | None = None) -> dict[str, Any]:
    """Build a source-preserving, server-authoritative tendency query result."""
    filters = filters or {}
    draft: list[dict[str, Any]] = []
    for report in reports:
        if opponent and report.get("opponent") != opponent:
            continue
        situation = _object(report.get("situation"))
        tags = _object(report.get("tags"))
        evolution = _object(_first(report.get("evolution"), report.get("adaptation"), report.get("trend_context")))
        claims = report.get("claims") if isinstance(report.get("claims"), list) else [{"statement": _first(report.get("claims"), report.get("title"), report.get("id")), "confidence": report.get("confidence"), "evidence_refs": report.get("evidence_refs")}]
        for index, raw_claim in enumerate(claims):
            claim = _object(raw_claim)
            dimensions = {key: _text(_first(claim.get(key), situation.get(key), tags.get(key), report.get(key)), "all") for key in TENDENCY_DIMENSIONS}
            evidence_refs = list(dict.fromkeys(_strings(_first(claim.get("evidence_refs"), report.get("evidence_refs"), claim.get("source_refs"), report.get("source_refs")))))
            source_clips = list(dict.fromkeys(_strings(_first(claim.get("source_clips"), claim.get("clip_ids"), claim.get("film_clip_ids"), report.get("source_clips"), report.get("clip_ids")))))
            explicit_contradictions = list(dict.fromkeys(_strings(_first(claim.get("contradictions"), claim.get("contradicts"), claim.get("conflicts"), claim.get("contradiction_refs")))))
            confidence = _text(_first(claim.get("confidence"), report.get("confidence")), "unrated")
            sample_size = _number(_first(claim.get("sample_size"), report.get("sample_size")))
            draft.append({
                "id": f"{report.get('id')}-CLAIM-{index + 1}",
                "report_id": report.get("id"),
                "organization_id": report.get("organization_id"),
                "opponent": report.get("opponent"),
                "statement": _text(_first(claim.get("statement"), claim.get("claim"), claim.get("description")), "Unlabeled tendency"),
                "confidence": confidence,
                "evidence_refs": evidence_refs,
                "source_clips": source_clips,
                "contradictions": explicit_contradictions,
                "sample_size": sample_size,
                "trend": _text(_first(claim.get("trend"), claim.get("trend_direction"), claim.get("evolution"), claim.get("current_vs_historical"), report.get("trend"), report.get("trend_direction"), evolution.get("trend"), evolution.get("direction")), "") or None,
                "stance": _stance(_first(claim.get("stance"), claim.get("direction"), claim.get("polarity"), report.get("stance"))),
                **dimensions,
            })
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for record in draft:
        key = tuple(str(record.get(field, "unknown")).lower() for field in ("opponent", *TENDENCY_DIMENSIONS))
        groups.setdefault(key, []).append(record)
    for record in draft:
        key = tuple(str(record.get(field, "unknown")).lower() for field in ("opponent", *TENDENCY_DIMENSIONS))
        group = groups.get(key, [])
        opposing = [candidate["id"] for candidate in group if candidate["id"] != record["id"] and candidate.get("stance") and record.get("stance") and candidate["stance"] != record["stance"]]
        record["contradictions"] = list(dict.fromkeys([*record.get("contradictions", []), *opposing]))
        evidence = list(dict.fromkeys([*record.get("evidence_refs", []), *record.get("source_clips", [])]))
        record["evidence_refs"] = evidence
        record["review_gate"] = _review_gate(sample_size=int(record.get("sample_size") or 0), confidence=str(record.get("confidence") or "unrated"), evidence_refs=evidence, contradictions=record["contradictions"])
    filtered = [record for record in draft if all(not filters.get(key) or filters[key] == "all" or record.get(key) == filters[key] for key in TENDENCY_DIMENSIONS)]
    gate_counts: dict[str, int] = {}
    for record in filtered:
        gate = str(record.get("review_gate"))
        gate_counts[gate] = gate_counts.get(gate, 0) + 1
    return {
        "opponent": opponent,
        "filters": {key: value for key, value in filters.items() if value and value != "all"},
        "records": filtered,
        "total": len(filtered),
        "sample_size_total": sum(int(record.get("sample_size") or 0) for record in filtered),
        "review_gate_counts": gate_counts,
        "human_review_required": bool(filtered),
        "production_implementation_allowed": False,
    }


class ScoutingWorkspaceService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def save_profile(self, *, profile: dict[str, Any], actor: str) -> dict[str, Any]:
        record = dict(profile)
        record["organization_id"] = self.repository.organization_id
        if record.get("status") == "valid":
            return self.repository.put("opponent_profiles", record["id"], record, actor=actor, reason="opponent_profile_saved")
        return record

    def create_report(self, *, report: dict[str, Any], actor: str) -> dict[str, Any]:
        record = dict(report)
        record["organization_id"] = self.repository.organization_id
        if record.get("status") == "under_review":
            return self.repository.put("scouting_reports", record["id"], record, actor=actor, reason="situational_scouting_report_created")
        return record

    def save_matchup(self, *, model: dict[str, Any], actor: str) -> dict[str, Any]:
        record = dict(model)
        record["organization_id"] = self.repository.organization_id
        return self.repository.put("matchup_models", record["id"], record, actor=actor, reason="matchup_model_saved") if record.get("status") == "under_review" else record

    def workspace(self, *, opponent: str | None = None) -> dict[str, Any]:
        collections = {name:self.repository.list(name) for name in ("opponent_profiles", "scouting_reports", "matchup_models", "opponent_evolutions")}
        if opponent:
            for name, records in collections.items():
                collections[name] = [record for record in records if record.get("opponent") == opponent]
        reports = collections["scouting_reports"]
        tendency = build_tendency_explorer(reports=reports, opponent=opponent)
        return {"organization_id":self.repository.organization_id, "opponent":opponent, "status":"ready" if any(collections.values()) else "empty", **collections, "tendency_explorer": tendency, "low_sample_count":sum(1 for report in reports if report.get("sample_size", 0) < 10), "review_count":sum(1 for record in [*reports, *collections["matchup_models"]] if record.get("status") in {"under_review", "needs_review"}), "adaptation_warning_count":sum(1 for record in collections["opponent_evolutions"] if record.get("status") in {"warning", "under_review"}), "human_review_required":bool(reports or collections["matchup_models"])}

    def tendency_explorer(self, *, opponent: str | None = None, filters: dict[str, str] | None = None) -> dict[str, Any]:
        reports = self.repository.list("scouting_reports")
        result = build_tendency_explorer(reports=reports, opponent=opponent, filters=filters)
        return {"organization_id": self.repository.organization_id, **result}
