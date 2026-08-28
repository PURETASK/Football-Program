"""Role-specific view model derived from canonical play records."""

from __future__ import annotations

from typing import Any

from .play_compiler import compile_play


def build_playbook_view(*, view_id: str, play: dict[str, Any], role: str) -> dict[str, Any]:
    result = compile_play(play)
    if not result.valid:
        raise ValueError({"code": "VIEW-INVALID-PLAY", "issues": [issue.__dict__ for issue in result.issues]})
    assignment = next((item for item in play["assignments"] if item.get("role") == role), None)
    if assignment is None:
        raise ValueError({"code": "VIEW-ROLE-NOT-IN-PLAY", "role": role})
    return {
        "id": view_id,
        "capability_id": "CAP-011",
        "play_id": play["id"],
        "role": role,
        "source_play_version": play["version"],
        "elements": [
            {"type": "formation", "value": play["formation"]},
            {"type": "personnel", "value": play["personnel"]},
            {"type": "assignment", "value": assignment["assignment"], "emphasis": "primary"},
            {"type": "situation", "value": play["situation"]},
        ],
        "status": "renderable",
    }
