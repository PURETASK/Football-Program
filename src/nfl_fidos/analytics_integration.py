"""Provider-neutral, bounded analytics observation ingestion."""

from __future__ import annotations

from typing import Any

from .analytics_dictionary import calculate_metric


ALLOWED_PROVIDER_KINDS = {"play_charting", "tracking_export", "analytics_platform", "approved_export"}
MAX_RECORDS = 1000


def calculate_provider_batch(*, organization_id: str, provider: dict[str, Any], batch_id: str, records: list[dict[str, Any]], source_manifest: dict[str, Any], actor: str) -> dict[str, Any]:
    issues: list[str] = []
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    if not organization_id.startswith("ORG-") or not actor:
        issues.append("organization_id and actor are required")
    if not batch_id.startswith("ANALYTICS-BATCH-"):
        issues.append("batch_id must start with ANALYTICS-BATCH-")
    if provider.get("kind") not in ALLOWED_PROVIDER_KINDS:
        issues.append("provider.kind is not an approved analytics provider")
    if provider.get("mode") != "read_only":
        issues.append("provider.mode must be read_only")
    provider_ref = str(provider.get("source_ref", ""))
    if not provider_ref or not (provider_ref.startswith("SOURCE-") or provider_ref.startswith("PROVIDER-")):
        issues.append("provider.source_ref must reference an approved SOURCE-* or PROVIDER-* record")
    if source_manifest.get("ref") != provider_ref:
        issues.append("source_manifest.ref must match provider.source_ref")
    if len(records) > MAX_RECORDS:
        issues.append(f"records cannot exceed {MAX_RECORDS}")
    if issues:
        return {"id":batch_id, "organization_id":organization_id, "accepted":[], "rejected":[], "batch_issues":issues, "accepted_count":0, "rejected_count":0, "status":"rejected", "external_provider_called":False, "external_state_changed":False, "human_review_required":True}
    for index, record in enumerate(records[:MAX_RECORDS]):
        if record.get("organization_id") not in {None, organization_id}:
            rejected.append({"index":index, "issues":["organization scope mismatch"]})
            continue
        try:
            observation = calculate_metric(definition=record["definition"], numerator=record["numerator"], denominator=record["denominator"], context=record["context"], source={"kind":source_manifest.get("kind", ""), "ref":provider_ref}, observation_ids=record["observation_ids"])
        except (KeyError, TypeError, ValueError) as exc:
            rejected.append({"index":index, "issues":[str(exc)]})
            continue
        observation["organization_id"] = organization_id
        observation["batch_id"] = batch_id
        observation["ingested_by"] = actor
        observation["provider"] = {"kind":provider.get("kind"), "mode":provider.get("mode"), "source_ref":provider_ref}
        if observation["status"] == "valid":
            accepted.append(observation)
        else:
            rejected.append({"index":index, "observation_id":observation.get("id"), "issues":observation["issues"]})
    status = "rejected" if not accepted and (issues or rejected) else "partial" if issues or rejected else "accepted"
    return {"id":batch_id, "organization_id":organization_id, "accepted":accepted, "rejected":rejected, "batch_issues":issues, "accepted_count":len(accepted), "rejected_count":len(rejected), "status":status, "external_provider_called":False, "external_state_changed":False, "human_review_required":True}
