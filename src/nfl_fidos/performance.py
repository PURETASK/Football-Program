"""Professional performance support with explicit non-diagnostic boundaries."""

from __future__ import annotations

from typing import Any


BOUNDARIES = [
    "This is performance support, not medical diagnosis or treatment.",
    "Recommendations require qualified staff review when pain, injury, illness, or protected health information is involved.",
    "Do not infer a medical condition from performance observations.",
]


def build_performance_note(
    *,
    note_id: str,
    athlete_context: str,
    observations: list[str],
    recommendations: list[str],
    health_signal_present: bool = False,
) -> dict[str, Any]:
    if not note_id.startswith("PERF-"):
        raise ValueError({"code": "PERF-ID", "message": "Performance note id must start with PERF-"})
    if not observations or not recommendations:
        raise ValueError({"code": "PERF-CONTENT", "message": "Observations and recommendations are required"})
    return {
        "id": note_id,
        "capability_id": "CAP-014",
        "athlete_context": athlete_context,
        "observations": observations,
        "recommendations": recommendations,
        "boundaries": BOUNDARIES,
        "escalation_required": health_signal_present,
        "status": "requires_staff_review" if health_signal_present else "draft",
    }
