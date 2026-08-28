"""Stage 11 drill taxonomy, competency links, and evaluation rules."""

from __future__ import annotations

from typing import Any


DRILL_TYPES = {"individual", "unit", "group", "team"}
CONTACT_LEVELS = {"non_contact", "thud", "contact"}


def validate_drill(drill: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ("id", "name", "drill_type", "target_skill", "competencies", "classification", "setup", "dose", "coaching_cues", "common_errors", "corrections", "kpis", "regressions", "progressions", "film_angles", "safety")
    for field in required:
        if not drill.get(field):
            issues.append({"code":"DRILL-REQUIRED", "message":f"Missing drill field: {field}", "path":field})
    if drill.get("id") and not str(drill["id"]).startswith("DRILL-"):
        issues.append({"code":"DRILL-ID", "message":"Drill id must start with DRILL-", "path":"id"})
    if drill.get("drill_type") not in DRILL_TYPES:
        issues.append({"code":"DRILL-TYPE", "message":"Unknown drill type", "path":"drill_type"})
    classification = drill.get("classification", {})
    if classification.get("contact_level") not in CONTACT_LEVELS:
        issues.append({"code":"DRILL-CONTACT", "message":"Contact level must be explicit", "path":"classification.contact_level"})
    dose = drill.get("dose", {})
    for field in ("minutes", "reps", "intensity"):
        if not dose.get(field):
            issues.append({"code":"DRILL-DOSE", "message":f"Dose requires {field}", "path":f"dose.{field}"})
    for field in ("competencies", "coaching_cues", "common_errors", "corrections", "kpis", "regressions", "progressions", "film_angles"):
        if field in drill and (not isinstance(drill[field], list) or not drill[field]):
            issues.append({"code":"DRILL-LIST", "message":f"{field} must be non-empty", "path":field})
    if not isinstance(drill.get("safety"), dict) or not drill["safety"].get("controls"):
        issues.append({"code":"DRILL-SAFETY", "message":"Safety controls are required", "path":"safety"})
    return issues


def build_drill(*, drill_id: str, name: str, drill_type: str, target_skill: str, competencies: list[str], classification: dict[str, Any], setup: dict[str, Any], dose: dict[str, Any], coaching_cues: list[str], common_errors: list[str], corrections: list[str], kpis: list[dict[str, Any]], regressions: list[str], progressions: list[str], film_angles: list[str], safety: dict[str, Any], position: str | None = None) -> dict[str, Any]:
    drill = {"id":drill_id, "name":name, "drill_type":drill_type, "position":position, "target_skill":target_skill, "competencies":competencies, "classification":classification, "setup":setup, "dose":dose, "coaching_cues":coaching_cues, "common_errors":common_errors, "corrections":corrections, "kpis":kpis, "regressions":regressions, "progressions":progressions, "film_angles":film_angles, "safety":safety}
    issues = validate_drill(drill)
    drill["status"] = "invalid" if issues else "draft"
    drill["issues"] = issues
    return drill


def evaluate_drill(*, evaluation_id: str, drill: dict[str, Any], athlete_id: str, observations: list[dict[str, Any]], evaluator: str) -> dict[str, Any]:
    issues = validate_drill(drill)
    if not athlete_id or not observations or not evaluator:
        issues.append({"code":"DRILL-EVAL-CONTEXT", "message":"Athlete, observations, and evaluator are required", "path":"evaluation"})
    return {"id":evaluation_id, "drill_id":drill.get("id"), "athlete_id":athlete_id, "observations":observations, "evaluator":evaluator, "status":"invalid" if issues else "under_review", "issues":issues, "human_review_required":True}
