"""Checksums, snapshots, diffs, three-way merges, and release metadata."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


RENDERER_VERSION = "nfl-fidos-play-renderer-1.0.0"
LIFECYCLE_FIELDS = {"status", "approval", "validation", "latest_snapshot_id", "release_id", "release_bundle", "_revision", "_saved_at", "_saved_by", "parent_design_id", "parent_snapshot_id", "merged_branch_id", "merge_base_snapshot_id", "rolled_back_from_snapshot_id"}
MERGE_METADATA_FIELDS = {"parent_design_id", "parent_snapshot_id", "merged_branch_id", "merge_base_snapshot_id", "rolled_back_from_snapshot_id"}


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in sorted(value.items()) if key not in LIFECYCLE_FIELDS}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def design_checksum(design: dict[str, Any]) -> str:
    payload = json.dumps(_canonical(design), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def renderer_checksum() -> str:
    return hashlib.sha256(RENDERER_VERSION.encode("utf-8")).hexdigest()


def bump_version(version: Any) -> str:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", str(version or "0.1.0"))
    if not match:
        return "0.1.1"
    major, minor, patch = (int(value) for value in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def snapshot_id(design_id: str, version: str, checksum: str, source: str = "save") -> str:
    safe_version = re.sub(r"[^A-Za-z0-9._-]+", "-", version)
    safe_source = re.sub(r"[^A-Za-z0-9._-]+", "-", source or "save")
    return f"SNAPSHOT-{design_id}-{safe_version}-{safe_source}-{checksum[:12]}"


def build_snapshot(design: dict[str, Any], *, actor: str, source: str = "save") -> dict[str, Any]:
    checksum = design.get("checksum") or design_checksum(design)
    version = str(design.get("version", "0.1.0"))
    return {
        "id": snapshot_id(str(design["id"]), version, checksum, source),
        "organization_id": design.get("organization_id"),
        "design_id": design["id"],
        "version": version,
        "checksum": checksum,
        "renderer_version": design.get("renderer_version", RENDERER_VERSION),
        "renderer_checksum": design.get("renderer_checksum", renderer_checksum()),
        "source": source,
        "design": deepcopy(design),
        "immutable": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": actor,
    }


def _item_key(item: dict[str, Any], index: int) -> str:
    return str(item.get("id") or f"index:{index}")


def _collection_diff(base: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> dict[str, Any]:
    def keyed(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        output = {}
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            output[_item_key(item, index)] = item
        return output

    before = keyed(base)
    after = keyed(candidate)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = []
    for item_id in sorted(set(before) & set(after)):
        fields = sorted({key for key in set(before[item_id]) | set(after[item_id]) if before[item_id].get(key) != after[item_id].get(key) and not key.startswith("_")})
        if fields:
            changed.append({"id": item_id, "fields": fields, "before": deepcopy(before[item_id]), "after": deepcopy(after[item_id])})
    return {"added": added, "removed": removed, "changed": changed}


def design_diff(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    fields = sorted({key for key in set(base) | set(candidate) if key not in {"elements", "players", "validation", "_revision", "_saved_at", "_saved_by"} | MERGE_METADATA_FIELDS and base.get(key) != candidate.get(key)})
    return {"changed_fields": fields, "players": _collection_diff(base.get("players", []), candidate.get("players", [])), "elements": _collection_diff(base.get("elements", []), candidate.get("elements", [])), "timeline_changed": base.get("timeline") != candidate.get("timeline"), "base_checksum": design_checksum(base), "candidate_checksum": design_checksum(candidate)}


def _merge_collection(base: list[dict[str, Any]], target: list[dict[str, Any]], branch: list[dict[str, Any]], path: str) -> tuple[list[dict[str, Any]], list[str]]:
    base_map = {_item_key(item, index): item for index, item in enumerate(base) if isinstance(item, dict)}
    target_map = {_item_key(item, index): item for index, item in enumerate(target) if isinstance(item, dict)}
    branch_map = {_item_key(item, index): item for index, item in enumerate(branch) if isinstance(item, dict)}
    merged: dict[str, dict[str, Any]] = {}
    conflicts: list[str] = []
    for item_id in sorted(set(base_map) | set(target_map) | set(branch_map)):
        original, ours, theirs = base_map.get(item_id), target_map.get(item_id), branch_map.get(item_id)
        if ours == original:
            selected = theirs
        elif theirs == original or ours == theirs:
            selected = ours
        elif ours is None and theirs is not None and original is not None:
            conflicts.append(f"{path}.{item_id}: deleted on target, changed on branch")
            selected = ours
        elif theirs is None and ours is not None and original is not None:
            conflicts.append(f"{path}.{item_id}: changed on target, deleted on branch")
            selected = ours
        else:
            conflicts.append(f"{path}.{item_id}")
            selected = ours or theirs
        if selected is not None:
            merged[item_id] = deepcopy(selected)
    ordered_ids = [_item_key(item, index) for index, item in enumerate(target) if isinstance(item, dict)]
    ordered_ids.extend(item_id for item_id in merged if item_id not in ordered_ids)
    return [merged[item_id] for item_id in ordered_ids if item_id in merged], conflicts


def three_way_merge(base: dict[str, Any], target: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(target)
    conflicts: list[str] = []
    for key in sorted(set(base) | set(target) | set(branch)):
        if key in {"elements", "players", "id", "organization_id", "version", "status", "approval", "latest_snapshot_id", "release_id", "release_bundle", "_revision", "_saved_at", "_saved_by"} | MERGE_METADATA_FIELDS:
            continue
        original, ours, theirs = base.get(key), target.get(key), branch.get(key)
        if ours == original:
            merged[key] = deepcopy(theirs)
        elif theirs == original or ours == theirs:
            merged[key] = deepcopy(ours)
        else:
            conflicts.append(key)
    for key in ("players", "elements"):
        merged[key], collection_conflicts = _merge_collection(base.get(key, []), target.get(key, []), branch.get(key, []), key)
        conflicts.extend(collection_conflicts)
    return {"merged": merged, "conflicts": sorted(conflicts)}
