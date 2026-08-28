"""Dependency-free validation for the NFL FIDOS Stage 0 control plane."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    manifest = load("control/manifest.json")
    registry = load("control/stage-0a-registry.json")
    gate = load("control/stage-0-exit-gate.json")
    stage_manifest = load("control/stage-manifest.json")

    if manifest["scope"] != "NFL only":
        fail(errors, "scope must remain NFL only")
    if manifest["current_stage"] != "STAGE-0" or manifest["current_work_package"] != "STAGE-0A":
        fail(errors, "program must remain in Stage 0A until the exit gate is closed")
    if manifest["production_implementation_allowed"] is not False:
        fail(errors, "production implementation must remain disabled during Stage 0A")
    stages = stage_manifest.get("stages", [])
    if len(stages) != 26:
        fail(errors, f"stage manifest must contain 26 stages, found {len(stages)}")
    expected_stage_ids = {f"STAGE-{index}" for index in range(26)}
    actual_stage_ids = {stage.get("id") for stage in stages}
    if actual_stage_ids != expected_stage_ids:
        fail(errors, "stage manifest must contain exactly STAGE-0 through STAGE-25")
    stage_zero = next((stage for stage in stages if stage.get("id") == "STAGE-0"), None)
    if not stage_zero or stage_zero.get("status") != "in_progress":
        fail(errors, "STAGE-0 must remain in_progress until its exit gate closes")

    collections = {
        "capabilities": ("CAP-", ["id", "name", "domain", "users", "contexts", "owner_stage", "dependencies", "priority", "risks", "acceptance_criteria"]),
        "agents": ("AGT-", ["id", "name", "family", "permissions", "dependencies", "owner_stage"]),
        "objects": ("OBJ-", ["id", "name", "domain", "versioned"]),
        "workflows": ("WF-", ["id", "name", "stages", "dependencies"]),
        "nuance_classes": ("NUANCE-", ["id", "name", "description"]),
        "risks": ("RISK-", ["id", "name", "severity", "mitigation"]),
        "questions": ("Q-", ["id", "question", "status", "owner", "impact"]),
    }

    ids: dict[str, str] = {}
    for group, (prefix, fields) in collections.items():
        records = registry.get(group)
        if not isinstance(records, list) or not records:
            fail(errors, f"{group} must be a non-empty list")
            continue
        for record in records:
            for field in fields:
                if field not in record:
                    fail(errors, f"{group} record {record.get('id', '<missing>')} lacks {field}")
            identifier = record.get("id", "")
            if not re.match(rf"^{re.escape(prefix)}[0-9]+$", identifier) and prefix not in {"NUANCE-", "RISK-"}:
                fail(errors, f"invalid {group} identifier: {identifier}")
            if identifier in ids:
                fail(errors, f"duplicate identifier: {identifier}")
            ids[identifier] = group

    for capability in registry.get("capabilities", []):
        for dependency in capability.get("dependencies", []) + capability.get("risks", []):
            if dependency not in ids:
                fail(errors, f"{capability['id']} references missing {dependency}")
        if not re.match(r"^STAGE-[0-9]+$", capability.get("owner_stage", "")):
            fail(errors, f"{capability['id']} has invalid owner_stage")

    for agent in registry.get("agents", []):
        for dependency in agent.get("dependencies", []):
            if dependency not in ids:
                fail(errors, f"{agent['id']} references missing {dependency}")

    for workflow in registry.get("workflows", []):
        for dependency in workflow.get("dependencies", []):
            if dependency not in ids:
                fail(errors, f"{workflow['id']} references missing {dependency}")

    if gate.get("status") == "complete":
        fail(errors, "Stage 0 gate cannot be complete while the manifest is in Stage 0A discovery")
    if any(check.get("status") == "complete" for check in gate.get("checks", [])) and gate.get("status") != "complete":
        # This is allowed during incremental discovery; it is intentionally not an error.
        pass

    if errors:
        print("CONTROL PLANE INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print("CONTROL PLANE VALID")
    print(f"capabilities={len(registry['capabilities'])} agents={len(registry['agents'])} objects={len(registry['objects'])} workflows={len(registry['workflows'])}")
    print(f"nuance_classes={len(registry['nuance_classes'])} risks={len(registry['risks'])} questions={len(registry['questions'])}")
    print(f"stage_gate={gate['status']} current_stage={manifest['current_stage']} work_package={manifest['current_work_package']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
