"""Executable Stage 0/0A discovery and exit-gate evaluation."""

from __future__ import annotations

from typing import Any


COLLECTIONS = ("capabilities", "agents", "objects", "workflows", "nuance_classes", "risks", "questions")
PREFIXES = {
    "capabilities": "CAP-",
    "agents": "AGT-",
    "objects": "OBJ-",
    "workflows": "WF-",
    "nuance_classes": "NUANCE-",
    "risks": "RISK-",
    "questions": "Q-",
}


def _check(check_id: str, criterion: str, passed: bool, evidence: list[str], blockers: list[str]) -> dict[str, Any]:
    result = {"id": check_id, "criterion": criterion, "status": "passed" if passed else "blocked", "evidence": evidence}
    if not passed:
        blockers.extend(evidence)
    return result


def evaluate_stage0_exit(
    registry: dict[str, Any], *, gap_audit_complete: bool = False, owner_approved: bool = False
) -> dict[str, Any]:
    """Evaluate whether the Stage 0A registry is eligible to advance to Stage 1.

    This function deliberately treats gap auditing and owner approval as external
    evidence. A structurally complete registry is not silently treated as approved.
    """
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    all_ids: set[str] = set()
    duplicate_ids: list[str] = []
    collections_present = all(isinstance(registry.get(name), list) and registry[name] for name in COLLECTIONS)
    checks.append(_check("STAGE0-COLLECTIONS", "Required discovery collections are present and non-empty", collections_present,
                         ["Missing or empty registry collection"] if not collections_present else [", ".join(COLLECTIONS)], blockers))

    for collection in COLLECTIONS:
        records = registry.get(collection, [])
        prefix = PREFIXES[collection]
        for record in records:
            record_id = record.get("id") if isinstance(record, dict) else None
            if not isinstance(record_id, str) or not record_id.startswith(prefix):
                blockers.append(f"{collection}: invalid stable ID {record_id!r}")
            elif record_id in all_ids:
                duplicate_ids.append(record_id)
            else:
                all_ids.add(record_id)
    checks.append(_check("STAGE0-STABLE-IDS", "Every registry record has a unique stable identifier", not duplicate_ids and not any("invalid stable ID" in b for b in blockers),
                         [f"Duplicate IDs: {duplicate_ids}"] if duplicate_ids else [f"Validated {len(all_ids)} IDs"], blockers))

    required_by_collection = {
        "capabilities": ("name", "domain", "users", "contexts", "owner_stage", "dependencies", "priority", "risks", "acceptance_criteria"),
        "agents": ("name", "family", "permissions", "dependencies", "owner_stage"),
        "objects": ("name", "domain", "versioned"),
        "workflows": ("name", "stages", "dependencies"),
        "nuance_classes": ("name", "description"),
        "risks": ("name", "severity", "mitigation"),
        "questions": ("question", "status", "owner", "impact"),
    }
    missing: list[str] = []
    for collection, fields in required_by_collection.items():
        for record in registry.get(collection, []):
            missing_fields = [field for field in fields if field not in record]
            if missing_fields:
                missing.append(f"{record.get('id', '<unknown>')}: {', '.join(missing_fields)}")
    checks.append(_check("STAGE0-METADATA", "Every record has required discovery metadata", not missing,
                         missing or ["Required metadata present for all registry records"], blockers))

    invalid_refs: list[str] = []
    for collection in ("capabilities", "agents", "workflows"):
        for record in registry.get(collection, []):
            for ref in record.get("dependencies", []):
                if ref not in all_ids:
                    invalid_refs.append(f"{record.get('id')}: unresolved dependency {ref}")
            for ref in record.get("risks", []):
                if ref not in all_ids:
                    invalid_refs.append(f"{record.get('id')}: unresolved risk {ref}")
    checks.append(_check("STAGE0-REFERENCES", "Capability, agent, and workflow references resolve", not invalid_refs,
                         invalid_refs or ["All dependency and risk references resolve"], blockers))

    invalid_owners = [f"{r.get('id')}: {r.get('owner_stage')}" for r in registry.get("capabilities", [])
                      if not isinstance(r.get("owner_stage"), str) or not r["owner_stage"].startswith("STAGE-")]
    checks.append(_check("STAGE0-OWNERS", "Every capability has an owning stage", not invalid_owners,
                         invalid_owners or ["All capabilities have owning stages"], blockers))

    gap_ok = bool(gap_audit_complete)
    checks.append(_check("STAGE0-GAP-AUDIT", "Gap and redundancy audit is complete", gap_ok,
                         ["Gap/redundancy audit evidence is required"] if not gap_ok else ["Gap/redundancy audit marked complete"], blockers))
    approval_ok = bool(owner_approved)
    checks.append(_check("STAGE0-OWNER-APPROVAL", "Final registry manifest is owner-approved", approval_ok,
                         ["Program owner approval evidence is required"] if not approval_ok else ["Owner approval recorded"], blockers))

    structural_ok = all(check["status"] == "passed" for check in checks[:5])
    ready = structural_ok and gap_ok
    approved = ready and approval_ok
    status = "approved" if approved else "ready_for_approval" if ready else "blocked"
    return {
        "gate_id": "STAGE0-EXIT-001",
        "stage": "STAGE-0",
        "work_package": "STAGE-0A",
        "next_stage": "STAGE-1",
        "status": status,
        "eligible_to_advance": approved,
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "registry_id": registry.get("registry_id"),
        "counts": {collection: len(registry.get(collection, [])) for collection in COLLECTIONS},
    }
