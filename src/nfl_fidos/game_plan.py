"""Evidence-aware game-plan recommendation assembly."""

from __future__ import annotations

from typing import Any

from .evidence import qualify_claim


def build_game_plan_options(
    *,
    problem: str,
    evidence: list[dict[str, Any]],
    options: list[dict[str, Any]],
    human_decision_required: bool = True,
) -> dict[str, Any]:
    """Return alternatives and countermeasures; never silently select a locked plan."""
    qualified = [qualify_claim(item) for item in evidence]
    usable = [item for item in qualified if item["valid"]]
    return {
        "id": "GAMEPLAN-DRAFT-001",
        "capability_id": "CAP-018",
        "workflow_id": "WF-007",
        "problem": problem,
        "evidence": usable,
        "options": options,
        "countermeasures_required": True,
        "human_decision_required": human_decision_required,
        "status": "draft",
        "uncertainty": "Evidence is contextual; options require staff review before lock.",
    }
