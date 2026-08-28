"""Stage 21 canonical data, ERD, version/history, migration, and tenancy validation."""

from __future__ import annotations

from typing import Any


def validate_data_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    entities = architecture.get("entities", [])
    entity_ids = {entity.get("id") for entity in entities}
    if not entities or len(entity_ids) != len(entities):
        issues.append("entities must be non-empty and uniquely identified")
    for entity in entities:
        for field in ("id", "name", "collection", "authoritative_for", "versioned", "audit_required", "tenant_key"):
            if field not in entity or entity[field] in (None, "", []):
                issues.append(f"{entity.get('id')}: missing {field}")
        if entity.get("versioned") is not True or entity.get("audit_required") is not True:
            issues.append(f"{entity.get('id')}: canonical entities must be versioned and audited")
    relationship_ids = set()
    for relationship in architecture.get("relationships", []):
        relationship_ids.add(relationship.get("name"))
        if relationship.get("from") not in entity_ids or relationship.get("to") not in entity_ids:
            issues.append(f"relationship {relationship.get('name')}: unknown endpoint")
        if relationship.get("cardinality") not in {"1_to_many", "many_to_many", "one_to_one"}:
            issues.append(f"relationship {relationship.get('name')}: invalid cardinality")
    for field in ("history_model", "migration_strategy", "security_and_tenancy", "audit_event_fields"):
        if not architecture.get(field):
            issues.append(f"missing data architecture section: {field}")
    required_audit_fields = {"event_id", "event_type", "collection", "record_id", "revision", "actor", "reason", "occurred_at"}
    if not required_audit_fields.issubset(set(architecture.get("audit_event_fields", []))):
        issues.append("audit event model is incomplete")
    return {"architecture_id":architecture.get("architecture_id"), "status":"valid" if not issues else "invalid", "errors":issues, "entity_count":len(entities), "relationship_count":len(architecture.get("relationships", []))}


def validate_record_tenancy(*, record: dict[str, Any], requester_organization: str, cross_organization_scope: bool = False) -> dict[str, Any]:
    organization_id = record.get("organization_id") or record.get("team_context")
    allowed = bool(organization_id and requester_organization and (organization_id == requester_organization or cross_organization_scope))
    return {"status":"allowed" if allowed else "denied", "allowed":allowed, "record_organization":organization_id, "requester_organization":requester_organization, "cross_organization_scope":cross_organization_scope, "audit_required":cross_organization_scope}
