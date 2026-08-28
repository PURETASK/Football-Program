"""First player-learning vertical slice built on the canonical play compiler."""

from __future__ import annotations

from typing import Any

from .play_compiler import compile_play


ROLE_LABELS = {
    "QB": "quarterback",
    "C": "center",
    "WR1": "wide receiver",
    "RB": "running back",
}


def build_player_lesson(play: dict[str, Any], learner_role: str) -> dict[str, Any]:
    """Create a small, role-specific lesson only from a validated play record."""

    result = compile_play(play)
    if not result.valid:
        raise ValueError({"code": "LESSON-INVALID-PLAY", "issues": [issue.__dict__ for issue in result.issues]})

    assignment = next(
        (item["assignment"] for item in play["assignments"] if item.get("role") == learner_role),
        None,
    )
    if assignment is None:
        raise ValueError({"code": "LESSON-ROLE-NOT-IN-PLAY", "role": learner_role})

    role_label = ROLE_LABELS.get(learner_role, learner_role)
    situation = play["situation"]
    return {
        "id": f"LESSON-{play['id'].removeprefix('PLAY-')}-{learner_role}",
        "capability_id": "CAP-001",
        "workflow_id": "WF-001",
        "status": "draft",
        "learner_role": learner_role,
        "learner_role_label": role_label,
        "source_play_id": play["id"],
        "objective": f"As the {role_label}, explain and execute your assignment in {play['formation']} {play['personnel']} personnel on {situation['down']}rd-and-{situation['distance']}.",
        "assignment": assignment,
        "context": {
            "team_context": play["team_context"],
            "field_zone": situation["field_zone"],
            "down": situation["down"],
            "distance": situation["distance"],
        },
        "checks": [
            {"type": "recall", "prompt": "State your assignment before the snap."},
            {"type": "application", "prompt": "Describe the first observable cue that changes your execution."},
            {"type": "reflection", "prompt": "Identify one uncertainty or team-specific term that requires coach confirmation."},
        ],
        "provenance": {"kind": play["source"]["kind"], "ref": play["source"]["ref"]},
        "confidence": "grounded_in_validated_play_record",
    }
