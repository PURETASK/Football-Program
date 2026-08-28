"""Cross-domain scheme/play compatibility and red-team validation."""

from __future__ import annotations

from typing import Any

from .play_compiler import compile_play
from .scheme import validate_scheme


def _component_label(scheme: dict[str, Any], kind: str) -> str | None:
    for component in scheme.get("components", []):
        if component.get("kind") == kind:
            return component.get("label")
    return None


def _equivalent_label(left: Any, right: Any) -> bool:
    """Compare canonical labels while preserving explicit team terminology."""
    normalize = lambda value: " ".join(str(value).lower().replace("_", " ").split())
    left_value = normalize(left)
    right_value = normalize(right)
    if left_value == right_value:
        return True
    if left_value.endswith(" personnel") and left_value.removesuffix(" personnel") == right_value:
        return True
    if right_value.endswith(" personnel") and right_value.removesuffix(" personnel") == left_value:
        return True
    return False


def check_play_scheme_compatibility(*, play: dict[str, Any], scheme: dict[str, Any], result_id: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    play_result = compile_play(play)
    if not play_result.valid:
        issues.append({"code": "COMPAT-PLAY-INVALID", "message": "Play must compile before compatibility is checked", "path": "play"})
    scheme_issues = validate_scheme(scheme)
    if scheme_issues:
        issues.append({"code": "COMPAT-SCHEME-INVALID", "message": "Scheme must validate before compatibility is checked", "path": "scheme"})

    expected_personnel = _component_label(scheme, "personnel")
    expected_formation = _component_label(scheme, "formation")
    if expected_personnel and not _equivalent_label(expected_personnel, play.get("personnel", "")):
        issues.append({"code": "COMPAT-PERSONNEL", "message": "Play personnel does not match scheme component", "path": "play.personnel"})
    if expected_formation and not _equivalent_label(expected_formation, play.get("formation", "")):
        issues.append({"code": "COMPAT-FORMATION", "message": "Play formation does not match scheme component", "path": "play.formation"})
    return {
        "id": result_id,
        "play_id": play.get("id"),
        "scheme_id": scheme.get("id"),
        "compatible": not issues,
        "issues": issues,
        "review_required": True,
        "status": "compatible" if not issues else "incompatible",
    }


def build_red_team_matrix(*, matrix_id: str, scheme_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not matrix_id.startswith("REDTEAM-") or not scheme_id.startswith("SCHEME-") or not rows:
        raise ValueError({"code": "REDTEAM-INCOMPLETE", "message": "Matrix id, scheme id, and at least one row are required"})
    issues: list[dict[str, str]] = []
    normalized_rows = []
    for index, row in enumerate(rows):
        if not row.get("threat") or not row.get("response") or not row.get("counter"):
            issues.append({"code": "REDTEAM-ROW", "message": "Each row requires threat, response, and counter", "path": f"rows[{index}"})
        normalized_rows.append({
            "threat": row.get("threat"), "response": row.get("response"), "counter": row.get("counter"),
            "evidence_refs": row.get("evidence_refs", []), "owner_review": row.get("owner_review", "pending"),
        })
    return {
        "id": matrix_id,
        "scheme_id": scheme_id,
        "rows": normalized_rows,
        "status": "draft",
        "review_required": True,
        "issues": issues,
    }
