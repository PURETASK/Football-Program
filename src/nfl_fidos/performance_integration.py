"""Provider-neutral, read-only performance data integration boundary."""

from __future__ import annotations

from typing import Any

from .performance_ingestion import ingest_performance_batch


ALLOWED_PROVIDER_KINDS = {"wearable_platform", "practice_system", "performance_platform", "approved_export"}
MAX_RECORDS = 1000


def ingest_provider_batch(
    *,
    organization_id: str,
    provider: dict[str, Any],
    batch_id: str,
    records: list[dict[str, Any]],
    source_manifest: dict[str, Any],
    actor: str,
) -> dict[str, Any]:
    """Validate provider metadata, then ingest an already-authorized batch.

    No provider is contacted here. A separately deployed adapter may fetch and
    normalize data, but this boundary only accepts its evidence and delegates
    non-diagnostic validation to the canonical batch ingester.
    """
    issues: list[str] = []
    if provider.get("kind") not in ALLOWED_PROVIDER_KINDS:
        issues.append("provider.kind is not an approved performance provider")
    if provider.get("mode") != "read_only":
        issues.append("provider.mode must be read_only")
    provider_ref = str(provider.get("source_ref", ""))
    if not provider_ref or not (provider_ref.startswith("SOURCE-") or provider_ref.startswith("PROVIDER-")):
        issues.append("provider.source_ref must reference an approved SOURCE-* or PROVIDER-* record")
    if len(records) > MAX_RECORDS:
        issues.append(f"records cannot exceed {MAX_RECORDS}")
    if issues:
        return {
            "id": batch_id,
            "organization_id": organization_id,
            "status": "rejected",
            "integration_issues": issues,
            "accepted": [],
            "rejected": [],
            "accepted_count": 0,
            "rejected_count": 0,
            "external_provider_called": False,
            "external_state_changed": False,
            "medical_decision_performed": False,
            "human_review_required": True,
        }
    result = ingest_performance_batch(batch_id=batch_id, organization_id=organization_id, records=records, source_manifest=source_manifest, actor=actor)
    result.update({
        "provider": {"kind": provider.get("kind"), "mode": provider.get("mode"), "source_ref": provider_ref},
        "integration_issues": [],
        "external_provider_called": False,
        "external_state_changed": False,
        "medical_decision_performed": False,
    })
    return result
