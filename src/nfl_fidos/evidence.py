"""Evidence and nuance primitives for football intelligence outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CLASSIFICATIONS = {
    "fact", "rule", "team_rule", "observed_tendency", "coaching_preference",
    "contextual_principle", "hypothesis",
}
CONFIDENCES = {"low", "moderate", "high"}


@dataclass(frozen=True)
class EvidenceIssue:
    code: str
    message: str
    path: str


def validate_evidence(item: dict[str, Any]) -> tuple[EvidenceIssue, ...]:
    issues: list[EvidenceIssue] = []
    required = ["id", "claim", "classification", "source", "context", "sample_size", "confidence"]
    for field in required:
        if field not in item or item[field] in (None, "", []):
            issues.append(EvidenceIssue("EVIDENCE-REQUIRED", f"Missing required field: {field}", field))
    if item.get("id") and (not isinstance(item["id"], str) or not item["id"].startswith("EVD-")):
        issues.append(EvidenceIssue("EVIDENCE-ID", "Evidence id must start with EVD-", "id"))
    if item.get("classification") not in CLASSIFICATIONS:
        issues.append(EvidenceIssue("EVIDENCE-CLASSIFICATION", "Unknown claim classification", "classification"))
    if item.get("confidence") not in CONFIDENCES:
        issues.append(EvidenceIssue("EVIDENCE-CONFIDENCE", "Confidence must be low, moderate, or high", "confidence"))
    if not isinstance(item.get("sample_size"), int) or isinstance(item.get("sample_size"), bool) or item["sample_size"] < 1:
        issues.append(EvidenceIssue("EVIDENCE-SAMPLE", "Sample size must be a positive integer", "sample_size"))
    context = item.get("context")
    if not isinstance(context, dict) or not context.get("team") or not context.get("opponent") or not context.get("situations"):
        issues.append(EvidenceIssue("EVIDENCE-CONTEXT", "Team, opponent, and at least one situation are required", "context"))
    source = item.get("source")
    if not isinstance(source, dict) or not source.get("kind") or not source.get("ref") or not source.get("captured_at"):
        issues.append(EvidenceIssue("EVIDENCE-PROVENANCE", "Source kind, reference, and capture timestamp are required", "source"))
    if item.get("confidence") == "high" and isinstance(item.get("sample_size"), int) and item["sample_size"] < 10:
        issues.append(EvidenceIssue("EVIDENCE-CALIBRATION", "High confidence requires a larger sample or an explicit reviewed exception", "confidence"))
    return tuple(issues)


def qualify_claim(item: dict[str, Any]) -> dict[str, Any]:
    """Return a safe presentation envelope; never erase source limitations."""
    issues = validate_evidence(item)
    output = dict(item)
    output["valid"] = not issues
    output["issues"] = [issue.__dict__ for issue in issues]
    if item.get("classification") == "observed_tendency" and item.get("sample_size", 0) < 10:
        output.setdefault("limitations", []).append("Small sample; do not generalize beyond the recorded situations.")
        output["generalization_allowed"] = False
    else:
        output["generalization_allowed"] = True
    return output
