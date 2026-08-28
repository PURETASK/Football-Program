"""Contextual opponent-scouting helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .evidence import qualify_claim


def build_tendency_record(
    *,
    record_id: str,
    team: str,
    opponent: str,
    observations: list[dict[str, Any]],
    situation: str,
    source_ref: str,
    captured_at: str,
) -> dict[str, Any]:
    """Summarize only observations matching the requested context."""
    matching = [observation for observation in observations if situation in observation.get("situations", [])]
    counts = Counter(observation.get("response", "unknown") for observation in matching)
    dominant = counts.most_common(1)[0] if counts else ("unknown", 0)
    sample_size = len(matching)
    confidence = "low" if sample_size < 5 else "moderate" if sample_size < 10 else "high"
    claim = f"In {situation}, {opponent} most often recorded response '{dominant[0]}' in the available sample."
    return qualify_claim({
        "id": record_id,
        "claim": claim,
        "classification": "observed_tendency",
        "source": {"kind": "film_observation_set", "ref": source_ref, "captured_at": captured_at},
        "context": {"team": team, "opponent": opponent, "situations": [situation]},
        "sample_size": sample_size,
        "confidence": confidence,
        "limitations": ["Observed film is not a guarantee of future behavior."],
        "distribution": dict(counts),
    })
