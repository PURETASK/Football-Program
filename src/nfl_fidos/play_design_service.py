"""Persistent play-design registry, templates, versions, and role views."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .play_creation import validate_legality, validate_play_design
from .play_assignment_graph import build_assignment_graph
from .play_design_exports import build_export, build_export_preflight
from .play_timeline import normalize_timeline_design
from .play_design_versioning import RENDERER_VERSION, build_snapshot, bump_version, design_checksum, design_diff, renderer_checksum, snapshot_id, three_way_merge, verify_design_integrity, verify_release_integrity, verify_snapshot_integrity
from .play_legality import profile_metadata
from .tenant_repository import TenantRepository
from .security_controls import sign_payload


def _clean_required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _parse_expiry(value: Any) -> datetime:
    text = _clean_required_text(value, "expires_at")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("expires_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


ASSET_REGISTRY: tuple[dict[str, Any], ...] = (
    {"id": "ASSET-ROUTE-POST", "kind": "route", "term": "post", "unit": "offense", "arrow_style": "route", "description": "Vertical stem with an inside break."},
    {"id": "ASSET-ROUTE-DIG", "kind": "route", "term": "dig", "unit": "offense", "arrow_style": "route", "description": "In-breaking route at a defined depth."},
    {"id": "ASSET-ROUTE-FLAT", "kind": "route", "term": "flat", "unit": "offense", "arrow_style": "route", "description": "Fast outlet to the flat."},
    {"id": "ASSET-MOTION-JET", "kind": "motion", "term": "jet", "unit": "offense", "arrow_style": "motion", "description": "Fast pre-snap motion across the formation."},
    {"id": "ASSET-RUN-IZ", "kind": "run", "term": "inside_zone", "unit": "offense", "arrow_style": "run", "description": "Zone run with an interior aiming point."},
    {"id": "ASSET-BLOCK-COMB0", "kind": "block", "term": "combo", "unit": "offense", "arrow_style": "block", "description": "Two-player combination block."},
    {"id": "ASSET-FRONT-425", "kind": "front", "term": "4-2-5_over", "unit": "defense", "arrow_style": "fit", "description": "Four-down nickel front."},
    {"id": "ASSET-COVER-3", "kind": "coverage", "term": "cover_3", "unit": "defense", "arrow_style": "coverage", "description": "Three-deep zone coverage shell."},
    {"id": "ASSET-RUSH-EDGE", "kind": "rush", "term": "edge", "unit": "defense", "arrow_style": "rush", "description": "Edge pressure path."},
    {"id": "ASSET-STUNT-TEX", "kind": "stunt", "term": "tex", "unit": "defense", "arrow_style": "stunt", "description": "Tackle-end exchange."},
)

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "playbook" / "asset-registry.json"
ALIGNMENT_PRESETS_PATH = Path(__file__).resolve().parents[2] / "playbook" / "alignment-presets.json"
CONCEPT_TEMPLATES_PATH = Path(__file__).resolve().parents[2] / "playbook" / "concept-templates.json"


def load_alignment_presets() -> dict[tuple[str, str, str], dict[str, Any]]:
    if not ALIGNMENT_PRESETS_PATH.exists():
        return {}
    with ALIGNMENT_PRESETS_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    presets = payload.get("presets", [])
    if not isinstance(presets, list):
        raise ValueError("Alignment preset registry must contain a presets array")
    output: dict[tuple[str, str, str], dict[str, Any]] = {}
    for preset in presets:
        if not isinstance(preset, dict) or not preset.get("unit") or not preset.get("category") or not preset.get("term"):
            raise ValueError("Every alignment preset requires unit, category, and term")
        slots = preset.get("slots")
        if not isinstance(slots, list) or len(slots) != 11:
            raise ValueError(f"Alignment preset {preset.get('term')} must contain exactly 11 slots")
        keys = [slot.get("key") for slot in slots if isinstance(slot, dict)]
        if len(keys) != 11 or len(set(keys)) != 11:
            raise ValueError(f"Alignment preset {preset.get('term')} must contain 11 unique slot keys")
        for slot in slots:
            x, y = slot.get("x"), slot.get("y")
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not 0 <= x <= 100 or not 0 <= y <= 53:
                raise ValueError(f"Alignment preset {preset.get('term')} contains an out-of-bounds slot")
        key = (str(preset["unit"]), str(preset["category"]), str(preset["term"]))
        if key in output:
            raise ValueError(f"Duplicate alignment preset: {key}")
        output[key] = deepcopy(preset)
    return output


def load_asset_registry() -> list[dict[str, Any]]:
    """Load the versioned catalog, retaining the small fallback for packaging."""
    alignments = load_alignment_presets()
    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        assets = payload.get("assets", [])
        if isinstance(assets, list) and assets:
            enriched = deepcopy(assets)
            for asset in enriched:
                key = (str(asset.get("unit")), str(asset.get("category")), str(asset.get("term")))
                if key in alignments:
                    asset["alignment"] = deepcopy(alignments[key])
            return enriched
    return [deepcopy(asset) for asset in ASSET_REGISTRY]


def validate_asset_registry(assets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Validate the professional catalog contract before it reaches the editor palette."""
    catalog = deepcopy(assets if assets is not None else load_asset_registry())
    errors: list[dict[str, Any]] = []
    required_categories = {"formation", "route", "protection", "run", "front", "coverage", "pressure", "stunt", "rotation", "check", "teaching"}
    seen_ids: set[str] = set()
    seen_terms: set[tuple[str, str, str]] = set()
    categories = {str(item.get("category")) for item in catalog if isinstance(item, dict)}
    missing_categories = sorted(required_categories - categories)
    if missing_categories:
        errors.append({"code": "ASSET-CATEGORIES-MISSING", "categories": missing_categories})
    for index, asset in enumerate(catalog):
        if not isinstance(asset, dict):
            errors.append({"code": "ASSET-NOT-OBJECT", "index": index})
            continue
        asset_id = str(asset.get("id", "")).strip()
        key = (str(asset.get("unit", "")), str(asset.get("category", "")), str(asset.get("term", "")))
        required = [field for field in ("id", "category", "kind", "term", "unit", "description", "accessibility", "version", "status") if not str(asset.get(field, "")).strip()]
        if required:
            errors.append({"code": "ASSET-METADATA-MISSING", "index": index, "fields": required})
        if asset_id and asset_id in seen_ids:
            errors.append({"code": "ASSET-ID-DUPLICATE", "id": asset_id})
        if asset_id:
            seen_ids.add(asset_id)
        if all(key):
            if key in seen_terms:
                errors.append({"code": "ASSET-TERM-DUPLICATE", "key": key})
            seen_terms.add(key)
        aliases = asset.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases):
            errors.append({"code": "ASSET-ALIASES-INVALID", "id": asset_id})
        if asset.get("status") in {"deprecated", "retired"} and asset.get("replacement_id") == asset_id:
            errors.append({"code": "ASSET-REPLACEMENT-SELF", "id": asset_id})
    return {"status": "valid" if not errors else "invalid", "asset_count": len(catalog), "category_count": len(categories), "categories": sorted(categories), "errors": errors}


def load_concept_templates() -> list[dict[str, Any]]:
    """Load reusable, slot-relative concept packages and verify their graph."""
    if not CONCEPT_TEMPLATES_PATH.exists():
        return [deepcopy(template) for template in TEMPLATES]
    with CONCEPT_TEMPLATES_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    templates = payload.get("templates", [])
    if not isinstance(templates, list) or not templates:
        raise ValueError("Concept template registry must contain a templates array")
    alignments = load_alignment_presets()
    seen_templates: set[str] = set()
    output: list[dict[str, Any]] = []
    for source in templates:
        if not isinstance(source, dict):
            raise ValueError("Every concept template must be an object")
        template = deepcopy(source)
        template_id = str(template.get("id", ""))
        unit = str(template.get("unit", ""))
        if not template_id or not template.get("name") or unit not in {"offense", "defense", "special_teams"}:
            raise ValueError("Every concept template requires id, name, and a supported unit")
        if template_id in seen_templates:
            raise ValueError(f"Duplicate concept template id: {template_id}")
        seen_templates.add(template_id)
        assignments = template.get("assignments")
        if not isinstance(assignments, list) or not assignments:
            raise ValueError(f"Concept template {template_id} requires assignments")
        assignment_keys = [str(item.get("key", "")) for item in assignments if isinstance(item, dict)]
        if len(assignment_keys) != len(assignments) or any(not key for key in assignment_keys) or len(set(assignment_keys)) != len(assignment_keys):
            raise ValueError(f"Concept template {template_id} requires unique assignment keys")
        known_keys = set(assignment_keys)
        for assignment in assignments:
            for reference in [*(assignment.get("depends_on") or []), assignment.get("exchange_with"), assignment.get("target_element_key")]:
                if reference and reference not in known_keys:
                    raise ValueError(f"Concept template {template_id} references unknown assignment key: {reference}")
        alignment_term = template.get("front") if unit == "defense" else template.get("formation")
        alignment_category = "front" if unit == "defense" else "formation"
        alignment = alignments.get((unit, alignment_category, str(alignment_term)))
        if alignment:
            valid_slots = {str(slot.get("key")) for slot in alignment.get("slots", [])}
            invalid_slots = sorted({str(item.get("slot")) for item in assignments if item.get("slot") not in valid_slots})
            if invalid_slots:
                raise ValueError(f"Concept template {template_id} uses unknown alignment slots: {', '.join(invalid_slots)}")
            template["alignment"] = deepcopy(alignment)
        template.setdefault("scope", "system")
        template.setdefault("status", "approved")
        output.append(template)
    return output


def asset_compatibility(asset: dict[str, Any], *, unit: str | None = None, formation: str | None = None, personnel: str | None = None, rule_profile: str | None = None) -> dict[str, Any]:
    reasons: list[str] = []
    warnings: list[str] = []
    basis: list[str] = []
    asset_unit = str(asset.get("unit", "shared"))
    if unit:
        basis.append(f"unit:{unit}")
        if asset_unit not in {unit, "shared"}:
            reasons.append(f"Designed for {asset_unit}, not {unit}.")
    formations = asset.get("compatible_formations", [])
    if formation and isinstance(formations, list) and formations:
        basis.append(f"formation:{formation}")
        if formation not in formations:
            reasons.append(f"Not cataloged for formation {formation.replace('_', ' ')}.")
    personnel_groups = asset.get("compatible_personnel", [])
    if personnel and isinstance(personnel_groups, list) and personnel_groups:
        basis.append(f"personnel:{personnel}")
        if personnel not in personnel_groups:
            reasons.append(f"Not cataloged for {personnel} personnel.")
    rule_profiles = asset.get("compatible_rule_profiles", [])
    if rule_profile and isinstance(rule_profiles, list) and rule_profiles:
        basis.append(f"rule_profile:{rule_profile}")
        if rule_profile not in rule_profiles:
            reasons.append(f"Not approved for the {rule_profile.replace('_', ' ')} rule profile.")
    status = str(asset.get("status", "active"))
    selectable = status in {"active", "approved"}
    if not selectable:
        reasons.append(f"Asset lifecycle state is {status}.")
    replacement_id = asset.get("replacement_id")
    if replacement_id:
        warnings.append(f"Use replacement {replacement_id} for new authoring.")
    compatible = not reasons
    return {
        "compatible": compatible,
        "selectable": selectable,
        "score": max(0, 100 - len(reasons) * 30 - len(warnings) * 10),
        "reasons": reasons,
        "warnings": warnings,
        "basis": basis,
        "replacement_id": replacement_id,
    }


TEMPLATES: tuple[dict[str, Any], ...] = (
    {"id": "TEMPLATE-OFF-2X2", "name": "Shotgun 2x2", "unit": "offense", "formation": "shotgun_2x2", "concept": "Dagger"},
    {"id": "TEMPLATE-OFF-TRIPS", "name": "Shotgun Trips", "unit": "offense", "formation": "shotgun_trips", "concept": "Flood"},
    {"id": "TEMPLATE-DEF-425", "name": "4-2-5 Cover 3", "unit": "defense", "formation": "4-2-5_over", "front": "4-2-5_over", "coverage": "cover_3", "concept": "Cover 3"},
    {"id": "TEMPLATE-DEF-3RD", "name": "Third-Down Pressure", "unit": "defense", "formation": "nickel_mug", "front": "4-2-5_over", "coverage": "cover_1", "concept": "Pressure"},
)


class PlayDesignService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository

    def _store_immutable_snapshot(self, snapshot: dict[str, Any], *, actor: str, reason: str) -> dict[str, Any]:
        """Persist a snapshot once; a matching retry never mutates history."""
        existing = self.repository.get("play_design_versions", snapshot["id"])
        if existing is not None:
            stable_fields = ("organization_id", "design_id", "version", "checksum", "renderer_version", "renderer_checksum", "source", "design", "immutable")
            if any(existing.get(field) != snapshot.get(field) for field in stable_fields):
                raise ValueError("Immutable play-design snapshot id already exists with different content")
            return existing
        return self.repository.put("play_design_versions", snapshot["id"], snapshot, actor=actor, reason=reason)

    def assets(self, *, unit: str | None = None, kind: str | None = None, category: str | None = None, query: str | None = None, status: str | None = None, formation: str | None = None, context_formation: str | None = None, personnel: str | None = None, rule_profile: str | None = None) -> list[dict[str, Any]]:
        query_key = (query or "").strip().lower()
        overrides = {item.get("asset_id"): item for item in self.repository.list("playbook_asset_overrides")}
        output: list[dict[str, Any]] = []
        for source in load_asset_registry():
            asset = deepcopy(source)
            override = overrides.get(asset.get("id"))
            if override:
                asset.update({key: value for key, value in override.items() if key not in {"id", "asset_id", "organization_id"}})
            haystack = " ".join([str(asset.get("term", "")), str(asset.get("display_name", "")), " ".join(asset.get("aliases", []))]).lower()
            formations = asset.get("compatible_formations", [])
            if unit and asset.get("unit") not in {unit, "shared"}:
                continue
            if kind and asset.get("kind") != kind:
                continue
            if category and asset.get("category") != category:
                continue
            if status and asset.get("status") != status:
                continue
            if formation and formation not in formations:
                continue
            if query_key and query_key not in haystack:
                continue
            asset["compatibility"] = asset_compatibility(asset, unit=unit, formation=context_formation, personnel=personnel, rule_profile=rule_profile)
            output.append(asset)
        return output

    def templates(self, *, unit: str | None = None) -> list[dict[str, Any]]:
        system_templates = load_concept_templates()
        organization_templates = self.repository.list("play_design_templates")
        templates = [*system_templates, *organization_templates]
        return [deepcopy(template) for template in templates if not unit or template.get("unit") == unit]

    def template_lineage_impact(self, template_id: str) -> dict[str, Any]:
        """Report descendants and inherited fields affected by a parent change.

        This is intentionally read-only. Parent edits or propagation require a
        separate governed workflow and are never performed as a side effect of
        requesting the report.
        """
        templates = self.templates()
        by_id = {str(item.get("id")): item for item in templates if item.get("id")}
        target = by_id.get(str(template_id))
        if target is None:
            raise KeyError(f"Unknown template: {template_id}")

        def resolved(template: dict[str, Any], seen: set[str] | None = None) -> dict[str, dict[str, Any]]:
            seen = set(seen or ())
            current_id = str(template.get("id", ""))
            if current_id in seen:
                return {}
            seen.add(current_id)
            parent = by_id.get(str(template.get("parent_template_id"))) if template.get("parent_template_id") else None
            output = resolved(parent, seen) if parent else {}
            for assignment in template.get("assignments", []):
                if isinstance(assignment, dict) and assignment.get("key"):
                    output[str(assignment["key"])] = deepcopy(assignment)
            return output

        def changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
            return sorted({*before.keys(), *after.keys()} - {"key"}, key=str)

        impacted: list[dict[str, Any]] = []
        queue: list[tuple[str, int]] = [(str(target["id"]), 0)]
        visited = {str(target["id"])}
        while queue:
            parent_id, depth = queue.pop(0)
            parent = by_id[parent_id]
            parent_effective = resolved(parent)
            for child in templates:
                child_id = str(child.get("id", ""))
                if str(child.get("parent_template_id", "")) != parent_id or child_id in visited:
                    continue
                visited.add(child_id)
                child_effective = resolved(child)
                local_by_key = {str(item.get("key")): item for item in child.get("assignments", []) if isinstance(item, dict) and item.get("key")}
                inherited_keys = sorted(set(parent_effective) & set(child_effective))
                overridden = []
                for key in inherited_keys:
                    if key in local_by_key:
                        fields = [field for field in changed_fields(parent_effective[key], local_by_key[key]) if parent_effective[key].get(field) != local_by_key[key].get(field)]
                        if fields:
                            overridden.append({"key": key, "fields": fields})
                impacted.append({
                    "template_id": child_id,
                    "name": child.get("name"),
                    "depth": depth + 1,
                    "status": child.get("status", "active"),
                    "inherited_assignment_count": len(inherited_keys),
                    "local_override_count": len(overridden),
                    "overrides": overridden,
                    "propagation_required": True,
                })
                queue.append((child_id, depth + 1))
        return {
            "template_id": str(target["id"]),
            "template_name": target.get("name"),
            "organization_id": self.repository.organization_id,
            "dependent_count": len(impacted),
            "dependents": impacted,
            "propagation_required": bool(impacted),
            "mutated": False,
        }

    def create_template(self, design_id: str, *, name: str, actor: str, description: str = "", tags: list[str] | None = None, template_kind: str = "custom", layer: str = "complete_call", element_ids: list[str] | None = None, parent_template_id: str | None = None) -> dict[str, Any]:
        """Capture a saved play or selected assignment stencil as a reusable template."""
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        clean_name = _clean_required_text(name, "name")
        if template_kind not in {"complete_call", "concept_layer", "protection_layer", "coverage_layer", "pressure_layer", "custom"}:
            raise ValueError("Unknown template_kind")
        parent = next((item for item in self.templates() if item.get("id") == parent_template_id), None) if parent_template_id else None
        if parent_template_id and parent is None:
            raise ValueError("Unknown parent template")
        if parent and parent.get("unit") != design.get("unit"):
            raise ValueError("Parent template unit must match the saved design")
        players = {player.get("id"): player for player in design.get("players", []) if isinstance(player, dict) and player.get("id")}
        requested_ids = {str(item) for item in (element_ids or []) if str(item).strip()}
        source_elements = [element for element in design.get("elements", []) if isinstance(element, dict) and (not requested_ids or str(element.get("id")) in requested_ids)]
        if not source_elements:
            raise ValueError("A reusable template requires at least one assignment")
        key_by_id = {str(element.get("id")): f"A-{index + 1:02d}" for index, element in enumerate(source_elements) if element.get("id")}
        assignments: list[dict[str, Any]] = []
        for index, element in enumerate(source_elements):
            assignment = deepcopy(element)
            element_id = str(assignment.pop("id", ""))
            player_id = assignment.pop("player_id", None)
            player = players.get(player_id, {})
            slot = str(player.get("alignment_key") or player.get("role") or player.get("position") or "TEAM")
            origin = player.get("start") if isinstance(player.get("start"), dict) else {"x": 0, "y": 0}
            raw_points = assignment.pop("points", assignment.pop("path", []))
            points = [{"dx": round(float(point["x"]) - float(origin.get("x", 0)), 3), "dy": round(float(point["y"]) - float(origin.get("y", 0)), 3)} for point in raw_points if isinstance(point, dict) and isinstance(point.get("x"), (int, float)) and isinstance(point.get("y"), (int, float))]
            assignment.update({"key": key_by_id.get(element_id, f"A-{index + 1:02d}"), "slot": slot})
            if points:
                assignment["points"] = points
            assignment["depends_on"] = [key_by_id[item] for item in assignment.get("depends_on", []) if item in key_by_id]
            if assignment.get("exchange_with") in key_by_id:
                assignment["exchange_with"] = key_by_id[assignment["exchange_with"]]
            else:
                assignment.pop("exchange_with", None)
            if assignment.get("target_element_id") in key_by_id:
                assignment["target_element_key"] = key_by_id[assignment.pop("target_element_id")]
            else:
                assignment.pop("target_element_id", None)
            assignment.pop("target_player_id", None)
            assignments.append(assignment)
        slug = re.sub(r"[^A-Z0-9]+", "-", clean_name.upper()).strip("-")[:36] or "CUSTOM"
        custom_count = len(self.repository.list("play_design_templates")) + 1
        template_id = f"TPL-ORG-{slug}-{custom_count:03d}"
        alignment_presets = load_alignment_presets()
        unit = str(design.get("unit", "offense"))
        alignment_term = design.get("front") if unit == "defense" else design.get("formation")
        alignment_category = "front" if unit == "defense" else "formation"
        template = {
            "id": template_id,
            "organization_id": self.repository.organization_id,
            "name": clean_name,
            "unit": unit,
            "template_kind": template_kind,
            "layer": layer or "complete_call",
            "formation": design.get("formation"),
            "front": design.get("front"),
            "coverage": design.get("coverage"),
            "personnel": design.get("personnel"),
            "concept": design.get("concept"),
            "version": "1.0.0",
            "status": "active",
            "scope": "organization",
            "description": str(description or f"Reusable {'stencil' if requested_ids else 'template'} captured from {design.get('name') or design_id}."),
            "tags": sorted({str(tag).strip() for tag in (tags or []) if str(tag).strip()}),
            "situations": [],
            "expected_companion_layers": [],
            "coaching_points": deepcopy(design.get("coaching_notes", [])),
            "timeline": deepcopy(design.get("timeline", {})),
            "assignments": assignments,
            "source_design_id": design_id,
            "source_snapshot_id": design.get("latest_snapshot_id"),
            "source_checksum": design.get("checksum"),
            "source_element_ids": sorted(requested_ids) if requested_ids else None,
            "capture_scope": "selection" if requested_ids else "full_play",
            "parent_template_id": parent_template_id,
            "inherited_assignments": deepcopy(parent.get("inherited_assignments", [])) + deepcopy(parent.get("assignments", [])) if parent else [],
            "alignment": deepcopy(alignment_presets.get((unit, alignment_category, str(alignment_term)))),
        }
        return self.repository.put("play_design_templates", template_id, template, actor=actor, reason="play_design_template_created")

    def update_asset_lifecycle(self, asset_id: str, *, status: str, actor: str, replacement_id: str | None = None, reason: str = "") -> dict[str, Any]:
        allowed = {"proposed", "reviewed", "approved", "active", "deprecated", "retired"}
        if status not in allowed:
            raise ValueError(f"Unknown asset lifecycle state: {status}")
        asset = next((item for item in load_asset_registry() if item.get("id") == asset_id), None)
        if asset is None:
            raise KeyError(f"Unknown asset: {asset_id}")
        override = {"id": f"OVERRIDE-{asset_id}", "asset_id": asset_id, "organization_id": self.repository.organization_id, "status": status, "replacement_id": replacement_id, "reason": reason}
        return self.repository.put("playbook_asset_overrides", override["id"], override, actor=actor, reason="asset_lifecycle_updated")

    def migrate_asset(self, old_asset_id: str, new_asset_id: str, *, actor: str) -> dict[str, Any]:
        if not any(item.get("id") == old_asset_id for item in load_asset_registry()) or not any(item.get("id") == new_asset_id for item in load_asset_registry()):
            raise KeyError("Both source and replacement assets must exist")
        designs = self.repository.list("play_designs")
        changed = 0
        for design in designs:
            dirty = False
            for element in design.get("elements", []):
                if element.get("asset_id") == old_asset_id:
                    element["asset_id"] = new_asset_id
                    dirty = True
            if dirty:
                self.repository.put("play_designs", design["id"], design, actor=actor, reason="asset_migration_applied")
                changed += 1
        return {"old_asset_id": old_asset_id, "new_asset_id": new_asset_id, "designs_migrated": changed, "status": "migrated"}

    def save(self, design: dict[str, Any], *, actor: str, expected_revision: int | None = None) -> dict[str, Any]:
        candidate = normalize_timeline_design(deepcopy(design))
        candidate["organization_id"] = self.repository.organization_id
        candidate.setdefault("status", "draft")
        existing = self.repository.get("play_designs", candidate.get("id", ""))
        if existing and expected_revision is not None and existing.get("_revision") != expected_revision:
            raise ValueError({"code": "DESIGN-CONFLICT", "message": "Design changed since it was loaded", "expected_revision": expected_revision, "actual_revision": existing.get("_revision")})
        if existing:
            candidate["version"] = bump_version(existing.get("version", candidate.get("version", "0.1.0")))
            if existing.get("status") == "published":
                candidate["status"] = "draft"
                candidate["approval"] = {"state": "draft", "supersedes_release_id": existing.get("release_id")}
                candidate.pop("release_id", None)
                candidate.pop("release_bundle", None)
        else:
            candidate["version"] = str(candidate.get("version", "0.1.0"))
        candidate["renderer_version"] = RENDERER_VERSION
        candidate["renderer_checksum"] = renderer_checksum()
        candidate["checksum"] = design_checksum(candidate)
        candidate["latest_snapshot_id"] = snapshot_id(str(candidate["id"]), candidate["version"], candidate["checksum"], "save")
        issues = self._apply_approved_legality_overrides(candidate, validate_play_design(candidate) + validate_legality(candidate))
        has_errors = any(issue.get("severity", "error") == "error" for issue in issues)
        candidate["validation"] = {"status": "invalid" if has_errors else "valid", "issues": issues}
        saved = self.repository.put("play_designs", candidate["id"], candidate, actor=actor, reason="play_design_saved")
        snapshot = build_snapshot(saved, actor=actor, source="save")
        self._store_immutable_snapshot(snapshot, actor=actor, reason="play_design_snapshot_created")
        return saved

    def create_batch_variants(self, design_id: str, *, variants: list[dict[str, Any]], actor: str, batch_id: str | None = None) -> dict[str, Any]:
        """Create bounded, draft child designs for explicit defensive/situational looks."""
        source = self.repository.get("play_designs", design_id)
        if source is None:
            raise KeyError(f"Unknown play design: {design_id}")
        if not isinstance(variants, list) or not variants or len(variants) > 32:
            raise ValueError("variants must contain between 1 and 32 looks")
        clean_batch = str(batch_id or f"VARIANT-BATCH-{design_id}-{len(self.repository.list('play_design_variant_batches')) + 1:04d}")
        if not clean_batch.startswith("VARIANT-BATCH-"):
            raise ValueError("batch_id must start with VARIANT-BATCH-")
        allowed_patch = {"formation", "front", "coverage", "personnel", "concept", "rule_profile"}
        allowed_assignment_patch = {
            "type", "points", "path", "note", "assignment", "responsibility", "objective", "technique",
            "landmark", "depth_yards", "leverage", "gap", "fit_gap", "gap_owner", "gap_owner_label",
            "fit_rule", "coverage", "rush_lane", "blitz_path", "stunt", "rotation", "rotation_trigger",
            "rotation_from_zone", "rotation_to_zone", "rotation_replacement_player_id", "rotation_vacated_zone",
            "rotation_sequence", "rotation_communication", "blocking_primitive", "protection_mode",
            "release_after_ms", "route_family", "stem_depth_yards", "break_type", "break_depth_yards",
            "finish_direction", "option_rule", "option_condition", "arrow_style", "arrow_ends", "path_mode",
            "line_style", "stroke_width", "line_cap", "start_ms", "end_ms", "timing", "phase", "zone",
        }
        created: list[dict[str, Any]] = []
        for index, item in enumerate(variants, start=1):
            if not isinstance(item, dict):
                raise ValueError("each variant must be an object")
            label = _clean_required_text(item.get("label") or item.get("name") or f"Look {index}", "variant label")
            patch = item.get("patch") or item.get("look") or {}
            if not isinstance(patch, dict) or any(key not in allowed_patch for key in patch):
                raise ValueError("variant patch contains an unsupported field")
            if not patch:
                raise ValueError("each variant requires at least one look field")
            assignment_patches = item.get("assignment_patches") or []
            if not isinstance(assignment_patches, list) or len(assignment_patches) > 64:
                raise ValueError("assignment_patches must contain at most 64 entries")
            slug = re.sub(r"[^A-Z0-9]+", "-", label.upper()).strip("-")[:28] or f"LOOK-{index:02d}"
            child_id = f"{design_id}-VAR-{slug}-{index:02d}"
            child = deepcopy(source)
            child.update({key: value for key, value in patch.items()})
            child["id"] = child_id
            child["name"] = f"{source.get('name') or design_id} · {label}"
            child["status"] = "draft"
            child["version"] = "0.1.0"
            child.pop("_revision", None)
            child.pop("latest_snapshot_id", None)
            child.pop("checksum", None)
            child.pop("release_id", None)
            child.pop("release_bundle", None)
            child.pop("approval", None)
            child["parent_design_id"] = design_id
            child["variant_batch_id"] = clean_batch
            normalized_assignment_patches: list[dict[str, Any]] = []
            elements_by_id = {str(element.get("id")): element for element in child.get("elements", []) if isinstance(element, dict) and element.get("id")}
            for assignment_patch in assignment_patches:
                if not isinstance(assignment_patch, dict):
                    raise ValueError("each assignment patch must be an object")
                element_id = _clean_required_text(assignment_patch.get("element_id"), "assignment patch element_id")
                element_patch = assignment_patch.get("patch")
                if element_id not in elements_by_id:
                    raise ValueError(f"assignment patch targets unknown element: {element_id}")
                if not isinstance(element_patch, dict) or not element_patch:
                    raise ValueError("each assignment patch requires a non-empty patch object")
                if "id" in element_patch or any(key not in allowed_assignment_patch for key in element_patch):
                    raise ValueError("assignment patch contains an unsupported field")
                elements_by_id[element_id].update(deepcopy(element_patch))
                normalized_assignment_patches.append({"element_id": element_id, "patch": deepcopy(element_patch)})
            child["variant_look"] = {"label": label, "patch": deepcopy(patch), "assignment_patches": normalized_assignment_patches, "source_design_id": design_id, "source_revision": source.get("_revision")}
            created.append(self.save(child, actor=actor))
        report = {"id": clean_batch, "organization_id": self.repository.organization_id, "source_design_id": design_id, "variant_ids": [item["id"] for item in created], "variants": created, "count": len(created), "status": "created", "immutable_source_revision": source.get("_revision"), "human_review_required": True}
        return self.repository.put("play_design_variant_batches", clean_batch, report, actor=actor, reason="play_design_variant_batch_created")

    def validate_draft(self, design: dict[str, Any]) -> dict[str, Any]:
        """Validate the current unsaved design without creating canonical state."""
        candidate = normalize_timeline_design(deepcopy(design))
        candidate["organization_id"] = self.repository.organization_id
        candidate.setdefault("status", "draft")
        candidate["renderer_version"] = RENDERER_VERSION
        candidate["renderer_checksum"] = renderer_checksum()
        candidate["draft_checksum"] = design_checksum(candidate)
        rule_profile = str(candidate.get("rule_profile") or "nfl")
        try:
            profile = profile_metadata(rule_profile)
        except KeyError:
            profile = {"id": rule_profile, "label": "Unknown controlled rule profile", "source": {"title": "Unknown profile", "uri": None, "rule_refs": []}}
        issues = self._apply_approved_legality_overrides(candidate, validate_play_design(candidate) + validate_legality(candidate))
        status = "invalid" if any(item.get("severity", "error") == "error" for item in issues) else "valid"
        return {
            "design_id": str(candidate.get("id") or "UNSAVED-DESIGN"),
            "rule_profile": rule_profile,
            "profile": profile,
            "issues": issues,
            "overrides": [item for item in self.repository.list("play_design_legality_overrides") if item.get("design_id") == candidate.get("id")],
            "status": status,
            "draft": True,
            "persisted": False,
            "draft_checksum": candidate["draft_checksum"],
            "normalized_design": candidate,
            "assignment_graph": build_assignment_graph(candidate),
        }

    def _apply_approved_legality_overrides(self, design: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        approved = [item for item in self.repository.list("play_design_legality_overrides") if item.get("design_id") == design.get("id") and item.get("status") == "approved"]
        by_code = {item.get("issue_code"): item for item in approved}
        output = []
        for issue in issues:
            override = by_code.get(issue.get("code"))
            active_override = False
            if override:
                try:
                    active_override = _parse_expiry(override.get("expires_at")) > datetime.now(timezone.utc)
                except ValueError:
                    active_override = False
            if override and active_override and issue.get("overrideable") is True:
                adjusted = deepcopy(issue)
                adjusted["original_severity"] = adjusted.get("severity", "error")
                adjusted["severity"] = "warning"
                adjusted["status"] = "overridden"
                adjusted["override"] = {"id": override.get("id"), "rationale": override.get("rationale"), "decision_ref": override.get("approval_decision_ref") or override.get("decision_ref"), "evidence_refs": override.get("evidence_refs", []), "expires_at": override.get("expires_at")}
                adjusted["message"] = f"{adjusted.get('message', 'Legality finding')} (approved override recorded; confirm before release)"
                output.append(adjusted)
            elif override:
                adjusted = deepcopy(issue)
                adjusted["override_expired"] = True
                adjusted["override"] = {"id": override.get("id"), "expires_at": override.get("expires_at"), "status": "expired"}
                output.append(adjusted)
            else:
                output.append(issue)
        return output

    def legality_report(self, design_id: str) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        rule_profile = design.get("rule_profile", "nfl")
        try:
            profile = profile_metadata(rule_profile)
        except KeyError:
            profile = {"id": rule_profile, "label": "Unknown controlled rule profile", "source": {"title": "Unknown profile", "uri": None, "rule_refs": []}}
        issues = self._apply_approved_legality_overrides(design, validate_play_design(design) + validate_legality(design))
        return {"design_id": design_id, "rule_profile": rule_profile, "profile": profile, "issues": issues, "overrides": [item for item in self.repository.list("play_design_legality_overrides") if item.get("design_id") == design_id], "status": "invalid" if any(item.get("severity", "error") == "error" for item in issues) else "valid"}

    def request_legality_override(self, design_id: str, *, issue_code: str, rationale: str, decision_ref: str, evidence_refs: list[str], expires_at: str, actor: str) -> dict[str, Any]:
        report = self.legality_report(design_id)
        issue = next((item for item in report["issues"] if item.get("code") == issue_code), None)
        if issue is None:
            raise KeyError(f"Legality issue is not present on the current design: {issue_code}")
        if issue.get("overrideable") is not True:
            raise ValueError("This legality finding is not overrideable")
        rationale_value = _clean_required_text(rationale, "rationale")
        decision_value = _clean_required_text(decision_ref, "decision_ref")
        if not isinstance(evidence_refs, list) or not evidence_refs or any(not isinstance(item, str) or not item.strip() for item in evidence_refs):
            raise ValueError("evidence_refs must be a non-empty list of non-empty strings")
        expiry = _parse_expiry(expires_at)
        if expiry <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        override_id = f"OVERRIDE-LEGALITY-{design_id}-{issue_code}"
        existing = self.repository.get("play_design_legality_overrides", override_id)
        if existing and existing.get("status") == "approved":
            raise ValueError("An approved override already exists for this finding")
        override = {"id": override_id, "organization_id": self.repository.organization_id, "design_id": design_id, "issue_code": issue_code, "rule_profile": report["rule_profile"], "rationale": rationale_value, "decision_ref": decision_value, "evidence_refs": [item.strip() for item in evidence_refs], "expires_at": expiry.isoformat(), "requested_by": actor, "status": "pending_owner_approval", "requested_at": datetime.now(timezone.utc).isoformat(), "original_issue": deepcopy(issue)}
        return self.repository.put("play_design_legality_overrides", override["id"], override, actor=actor, reason="legality_override_requested")

    def approve_legality_override(self, design_id: str, *, override_id: str, decision_ref: str, actor: str) -> dict[str, Any]:
        override = self.repository.get("play_design_legality_overrides", override_id)
        if override is None or override.get("design_id") != design_id:
            raise KeyError("Unknown legality override for this design")
        decision_value = _clean_required_text(decision_ref, "decision_ref")
        if override.get("status") != "pending_owner_approval":
            raise ValueError("Only a pending owner-approval override can be approved")
        override["status"] = "approved"
        override["approval_decision_ref"] = decision_value
        override["approved_by"] = actor
        override["approved_at"] = datetime.now(timezone.utc).isoformat()
        return self.repository.put("play_design_legality_overrides", override_id, override, actor=actor, reason="legality_override_approved")

    def workspace(self, *, include_invalid: bool = True) -> dict[str, Any]:
        designs = self.repository.list("play_designs")
        if not include_invalid:
            designs = [design for design in designs if design.get("validation", {}).get("status") == "valid"]
        return {"organization_id": self.repository.organization_id, "designs": designs, "templates": self.templates(), "asset_count": len(load_asset_registry())}

    def role_view(self, design_id: str, *, role: str, mode: str = "player", step: int | None = None, user_id: str | None = None) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        # Older persisted records may predate phase/event normalization. Read
        # through the canonical timeline contract so teaching views do not
        # silently lose timing or legacy event semantics.
        design = normalize_timeline_design(design)
        if mode not in {"player", "coach", "position_group"}:
            raise ValueError("mode must be player, position_group, or coach")
        players = [item for item in design.get("players", []) if isinstance(item, dict)]
        exact = [item for item in players if item.get("id") == role]
        group = exact or [item for item in players if item.get("position") == role or item.get("role") == role]
        coach_role = role.lower() in {"coach", "coach_staff", "analyst", "staff", "all"}
        if not group and not coach_role:
            raise KeyError(f"Role is not present in design: {role}")
        effective_mode = "coach" if mode == "coach" or coach_role else mode
        target_ids = {item.get("id") for item in group if item.get("id")}
        elements = [item for item in design.get("elements", []) if isinstance(item, dict)]
        if effective_mode == "coach":
            visible = deepcopy(elements)
        else:
            visible = [item for item in elements if item.get("player_id") in target_ids or item.get("visibility") in {"shared", "all"} or item.get("role") in {role, "shared", "all"} or (not item.get("player_id") and item.get("kind") == "annotation")]
        visible_ids = {item.get("id") for item in visible if item.get("id")}
        position_by_player = {item.get("id"): item.get("position", item.get("role", "player")) for item in players}
        steps: list[dict[str, Any]] = []
        for index, element in enumerate(visible):
            element_id = str(element.get("id") or f"ELEMENT-{index + 1}")
            timing = element.get("timing", {}) if isinstance(element.get("timing"), dict) else {}
            phases = timing.get("phases") if isinstance(timing.get("phases"), list) else []
            if not phases:
                phases = [{"id": "assignment", "label": "Assignment", "start_ms": element.get("start_ms", 0), "end_ms": element.get("end_ms", design.get("timeline", {}).get("duration_ms", 3000))}]
            for phase_index, phase in enumerate(phases):
                instruction = element.get("note") or element.get("assignment") or element.get("responsibility") or "Execute the assigned path and coaching cue."
                responsibility_context = []
                if element.get("gap_owner"):
                    responsibility_context.append(f"Own {element['gap_owner']}.")
                if element.get("exchange_with"):
                    role_label = str(element.get("exchange_role") or "exchange").replace("_", " ")
                    responsibility_context.append(f"{role_label} with {element['exchange_with']}.")
                if element.get("rotation_to_zone") or element.get("zone"):
                    responsibility_context.append(f"Replace {element.get('rotation_to_zone') or element.get('zone')}.")
                if element.get("rotation_trigger"):
                    responsibility_context.append(f"Trigger: {str(element['rotation_trigger']).replace('_', ' ')}.")
                if element.get("rotation_communication"):
                    responsibility_context.append(f"Communication: {element['rotation_communication']}.")
                if responsibility_context:
                    instruction = f"{instruction} {' '.join(responsibility_context)}"
                steps.append({"id": f"STEP-{element_id}-{phase.get('id', phase_index + 1)}", "element_id": element_id, "player_id": element.get("player_id"), "position": position_by_player.get(element.get("player_id"), "shared"), "label": f"{position_by_player.get(element.get('player_id'), 'Shared')} · {element.get('type') or element.get('kind', 'assignment')} · {phase.get('label', 'Phase')}", "instruction": instruction, "gap_owner": element.get("gap_owner"), "exchange_with": element.get("exchange_with"), "exchange_role": element.get("exchange_role"), "replacement_zone": element.get("rotation_to_zone") or element.get("zone"), "rotation_trigger": element.get("rotation_trigger"), "rotation_sequence": element.get("rotation_sequence"), "start_ms": int(phase.get("start_ms", 0) or 0), "end_ms": int(phase.get("end_ms", 0) or 0), "revealed": False})
        steps.sort(key=lambda item: (item["start_ms"], item["end_ms"], item["id"]))
        for index, item in enumerate(steps):
            item["step_index"] = index
        reveal_step = None if step is None else max(0, min(int(step), max(0, len(steps) - 1)))
        for item in steps:
            item["revealed"] = reveal_step is None or item["step_index"] <= reveal_step
        mastery = self.mastery(design_id, role=role, user_id=user_id)
        mastered_step_ids = set(mastery.get("summary", {}).get("mastered_steps", []))
        for item in steps:
            item["mastered"] = item["id"] in mastered_step_ids
        reads = [{"id": str(element.get("id") or f"ELEMENT-{index + 1}"), "player_id": element.get("player_id"), "key": element.get("read_key") or element.get("key") or element.get("responsibility"), "prompt": element.get("read_prompt") or element.get("note") or "Identify the key and confirm the assignment."} for index, element in enumerate(visible) if element.get("kind") == "read" or element.get("read_key") or element.get("read_prompt")]
        timeline = deepcopy(design.get("timeline", {}))
        narration = timeline.get("narration", []) if isinstance(timeline.get("narration"), list) else []
        timeline["narration"] = [cue for cue in narration if effective_mode == "coach" or cue.get("role") in {None, role, "shared", "all"}]
        quiz_source = design.get("teaching", {}).get("quizzes", []) if isinstance(design.get("teaching"), dict) else design.get("quizzes", [])
        if not isinstance(quiz_source, list):
            quiz_source = []
        quizzes = []
        for index, quiz in enumerate(quiz_source):
            if not isinstance(quiz, dict):
                continue
            item = {"id": quiz.get("id", f"QUIZ-{design_id}-{index + 1}"), "question": quiz.get("question") or quiz.get("prompt") or "What is your assignment?", "options": quiz.get("options", []), "step_id": quiz.get("step_id")}
            if effective_mode == "coach" and "answer" in quiz:
                item["answer"] = quiz.get("answer")
            else:
                item["answer_required"] = True
            quizzes.append(item)
        practice_linkage = deepcopy(design.get("practice_linkage")) if "practice_linkage" in design else {"practice_refs": deepcopy(design.get("practice_refs", [])), "drill_ids": deepcopy(design.get("drill_ids", []))}
        accessible_lines = [f"{design.get('concept') or design_id}; {design.get('formation') or 'formation'}; {role} view."]
        accessible_lines.extend(f"Step {item['step_index'] + 1}: {item['label']}. {item['instruction']} ({item['start_ms']} to {item['end_ms']} milliseconds)." for item in steps if item["revealed"])
        return {"id": f"VIEW-{design_id}-{role}-{effective_mode}", "play_id": design_id, "role": role, "mode": effective_mode, "position_group": [item.get("position") for item in group], "source_play_version": design.get("version"), "source_snapshot_id": design.get("latest_snapshot_id"), "source_checksum": design.get("checksum"), "renderer_version": design.get("renderer_version"), "renderer_checksum": design.get("renderer_checksum"), "player": group[0] if group else None, "players": deepcopy(group if effective_mode != "coach" else players), "context_players": deepcopy([item for item in players if item not in group]) if effective_mode != "coach" else [], "elements": visible, "filtered_diagram": {"players": deepcopy(group if effective_mode != "coach" else players), "context_players": deepcopy([item for item in players if item not in group]) if effective_mode != "coach" else [], "elements": visible, "hidden_element_count": max(0, len(elements) - len(visible))}, "timeline": timeline, "steps": steps, "current_step": reveal_step, "read_reveal": reads, "quizzes": quizzes, "mastery": mastery, "practice_linkage": practice_linkage, "coaching_notes": deepcopy(design.get("coaching_notes", [])), "accessible_text": "\n".join(accessible_lines), "status": "renderable", "visible_element_ids": sorted(visible_ids)}

    def mastery(self, design_id: str, *, role: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        if self.repository.get("play_designs", design_id) is None:
            raise KeyError(f"Unknown play design: {design_id}")
        records = [item for item in self.repository.list("play_design_mastery") if item.get("design_id") == design_id and (role is None or item.get("role") == role) and (user_id is None or item.get("user_id") == user_id)]
        records.sort(key=lambda item: item.get("recorded_at", item.get("_saved_at", "")))
        scores = [float(item.get("score")) for item in records if isinstance(item.get("score"), (int, float))]
        mastered_steps = sorted({item.get("step_id") for item in records if item.get("status") == "mastered" and item.get("step_id")})
        return {"design_id": design_id, "role": role, "user_id": user_id, "attempts": records, "summary": {"attempt_count": len(records), "average_score": round(sum(scores) / len(scores), 3) if scores else None, "mastered_step_count": len(mastered_steps), "mastered_steps": mastered_steps, "status": "mastered" if mastered_steps and records and all(item.get("status") == "mastered" for item in records[-min(len(records), len(mastered_steps)):]) else ("in_progress" if records else "not_started")}}

    def record_mastery(self, design_id: str, *, role: str, user_id: str, step_id: str, score: float, result: str = "attempted", actor: str, practice_ref: str | None = None, notes: str = "", attempt_id: str | None = None) -> dict[str, Any]:
        if self.repository.get("play_designs", design_id) is None:
            raise KeyError(f"Unknown play design: {design_id}")
        if not role or not user_id or not step_id:
            raise ValueError("role, user_id, and step_id are required")
        try:
            normalized_score = float(score)
        except (TypeError, ValueError) as exc:
            raise ValueError("score must be numeric") from exc
        if not 0 <= normalized_score <= 1:
            raise ValueError("score must be between 0 and 1")
        if result not in {"attempted", "passed", "mastered", "needs_review"}:
            raise ValueError("Unknown mastery result")
        status = "mastered" if result == "mastered" or normalized_score >= 0.8 else result
        safe_role = str(role).replace("/", "-").replace(" ", "-")
        record = {"id": attempt_id or f"MASTERY-{design_id}-{user_id}-{safe_role}-{len(self.repository.list('play_design_mastery')) + 1:04d}", "organization_id": self.repository.organization_id, "design_id": design_id, "role": role, "user_id": user_id, "step_id": step_id, "score": round(normalized_score, 3), "result": result, "status": status, "practice_ref": practice_ref, "notes": notes.strip() if isinstance(notes, str) else "", "recorded_at": datetime.now(timezone.utc).isoformat(), "recorded_by": actor}
        return self.repository.put("play_design_mastery", record["id"], record, actor=actor, reason="play_design_mastery_recorded")

    def export_artifact(self, design_ids: list[str], *, kind: str, format: str, actor: str, role: str | None = None, black_white: bool = False, branding: dict[str, Any] | None = None, layout: str | None = None, signing_secret: str | None = None) -> dict[str, Any]:
        if not isinstance(design_ids, list) or not design_ids:
            raise ValueError("At least one design id is required")
        designs = []
        for design_id in design_ids:
            design = self.repository.get("play_designs", design_id)
            if design is None:
                raise KeyError(f"Unknown play design: {design_id}")
            designs.append(design)
        artifact = build_export(designs=designs, kind=kind, format=format, role=role, black_white=black_white, branding=branding, layout=layout)
        artifact["organization_id"] = self.repository.organization_id
        artifact["requested_by"] = actor
        if signing_secret:
            signed_fields = {"artifact_id": artifact.get("artifact_id"), "organization_id": artifact["organization_id"], "sha256": artifact.get("sha256"), "source_manifest_hash": artifact.get("source_manifest_hash")}
            artifact["signature"] = sign_payload(signed_fields, secret=signing_secret)
            artifact["signature_algorithm"] = "HMAC-SHA256"
            artifact["signed_fields"] = sorted(signed_fields)
        return artifact

    def export_preflight(self, design_ids: list[str], *, kind: str, format: str, role: str | None = None, layout: str | None = None) -> dict[str, Any]:
        """Run export validation against organization-scoped source records."""
        if not isinstance(design_ids, list) or not design_ids:
            raise ValueError("At least one design id is required")
        designs = []
        for design_id in design_ids:
            design = self.repository.get("play_designs", design_id)
            if design is None:
                raise KeyError(f"Unknown play design: {design_id}")
            designs.append(design)
        return build_export_preflight(designs=designs, kind=kind, format=format, role=role, layout=layout)

    def submit_quiz(self, design_id: str, *, role: str, user_id: str, quiz_id: str, answer: Any, actor: str, practice_ref: str | None = None) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        teaching = design.get("teaching", {}) if isinstance(design.get("teaching"), dict) else {}
        quizzes = teaching.get("quizzes", design.get("quizzes", []))
        quiz = next((item for item in quizzes if isinstance(item, dict) and item.get("id") == quiz_id), None)
        if quiz is None:
            raise KeyError(f"Unknown quiz: {quiz_id}")
        expected = quiz.get("answer")
        correct = answer == expected or (isinstance(expected, list) and answer in expected)
        step_id = quiz.get("step_id") or f"STEP-QUIZ-{quiz_id}"
        mastery = self.record_mastery(design_id, role=role, user_id=user_id, step_id=step_id, score=1.0 if correct else 0.0, result="mastered" if correct else "needs_review", actor=actor, practice_ref=practice_ref, attempt_id=f"QUIZ-ATTEMPT-{design_id}-{user_id}-{quiz_id}-{len(self.repository.list('play_design_mastery')) + 1:04d}")
        return {"quiz_id": quiz_id, "correct": correct, "score": mastery["score"], "mastery": mastery}

    def request_review(self, design_id: str, *, actor: str, decision_ref: str) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        design["status"] = "under_review"
        design["approval"] = {"state": "pending_approval", "requester": actor, "decision_ref": decision_ref}
        return self.repository.put("play_designs", design_id, design, actor=actor, reason="play_design_review_requested")

    def publish(self, design_id: str, *, actor: str, decision_ref: str, game_plan_snapshot_id: str | None = None) -> dict[str, Any]:
        design = self.repository.get("play_designs", design_id)
        if design is None:
            raise KeyError(f"Unknown play design: {design_id}")
        if design.get("validation", {}).get("status") != "valid":
            raise ValueError("Only a valid play design can be published")
        if design.get("approval", {}).get("state") != "pending_approval":
            raise ValueError("Play design must be under review before publishing")
        integrity = verify_design_integrity(design)
        if not integrity["valid"]:
            raise ValueError({"code": "DESIGN-INTEGRITY-INVALID", "issues": integrity["issues"]})
        if game_plan_snapshot_id is not None:
            if not isinstance(game_plan_snapshot_id, str) or not game_plan_snapshot_id.strip():
                raise ValueError("game_plan_snapshot_id must be a non-empty string when supplied")
            design["game_plan_snapshot_id"] = game_plan_snapshot_id.strip()
            design["checksum"] = design_checksum(design)
        design["status"] = "published"
        design["approval"] = {"state": "approved", "approver": actor, "decision_ref": decision_ref}
        release_id = f"RELEASE-{design_id}-{design.get('version', '0.1.0')}"
        existing_release = self.repository.get("play_design_releases", release_id)
        if existing_release is not None:
            raise ValueError("Immutable release already exists; create a new draft version before publishing")
        release_snapshot_id = snapshot_id(str(design_id), str(design.get("version", "0.1.0")), str(design["checksum"]), "publish")
        design["release_id"] = release_id
        design["latest_snapshot_id"] = release_snapshot_id
        design["release_bundle"] = {"id": release_id, "immutable": True, "snapshot_id": release_snapshot_id, "content_checksum": design.get("checksum"), "renderer_version": design.get("renderer_version"), "renderer_checksum": design.get("renderer_checksum"), "game_plan_snapshot_id": design.get("game_plan_snapshot_id"), "game_plan_snapshot_locked": bool(design.get("game_plan_snapshot_id"))}
        saved = self.repository.put("play_designs", design_id, design, actor=actor, reason="play_design_published")
        snapshot = build_snapshot(saved, actor=actor, source="publish")
        self._store_immutable_snapshot(snapshot, actor=actor, reason="play_design_release_snapshot_created")
        release = {"id": release_id, "organization_id": self.repository.organization_id, "design_id": design_id, "version": saved.get("version"), "snapshot_id": snapshot["id"], "checksum": saved.get("checksum"), "renderer_version": saved.get("renderer_version"), "renderer_checksum": saved.get("renderer_checksum"), "game_plan_snapshot_id": saved.get("game_plan_snapshot_id"), "game_plan_snapshot_locked": bool(saved.get("game_plan_snapshot_id")), "immutable": True, "status": "published", "approval": saved.get("approval"), "bundle_manifest": deepcopy(saved.get("release_bundle", {})), "published_at": datetime.now(timezone.utc).isoformat()}
        release_integrity = verify_release_integrity(release)
        if not release_integrity["valid"]:
            raise ValueError({"code": "RELEASE-INTEGRITY-INVALID", "issues": release_integrity["issues"]})
        self.repository.put("play_design_releases", release_id, release, actor=actor, reason="play_design_release_created")
        return saved

    def branch(self, design_id: str, *, branch_id: str, actor: str) -> dict[str, Any]:
        source = self.repository.get("play_designs", design_id)
        if source is None:
            raise KeyError(f"Unknown play design: {design_id}")
        if not branch_id or branch_id == design_id:
            raise ValueError("branch_id must be a distinct non-empty design id")
        if self.repository.get("play_designs", branch_id) is not None:
            raise ValueError("A design with this branch_id already exists")
        if not source.get("latest_snapshot_id"):
            raise ValueError("Source design is missing an immutable base snapshot")
        branch = deepcopy(source)
        branch["id"] = branch_id
        branch["version"] = str(source.get("version", "0.1.0")) + ".branch"
        branch["status"] = "draft"
        branch["parent_design_id"] = design_id
        branch["parent_snapshot_id"] = source.get("latest_snapshot_id")
        branch["approval"] = {"state": "draft"}
        branch.pop("release_id", None)
        branch.pop("release_bundle", None)
        branch.pop("_revision", None)
        branch.pop("_saved_at", None)
        branch.pop("_saved_by", None)
        branch["renderer_version"] = RENDERER_VERSION
        branch["renderer_checksum"] = renderer_checksum()
        branch["checksum"] = design_checksum(branch)
        branch["latest_snapshot_id"] = snapshot_id(str(branch_id), branch["version"], branch["checksum"], "branch")
        saved = self.repository.put("play_designs", branch_id, branch, actor=actor, reason="play_design_branch_created")
        snapshot = build_snapshot(saved, actor=actor, source="branch")
        self._store_immutable_snapshot(snapshot, actor=actor, reason="play_design_branch_snapshot_created")
        return saved

    def versions(self, design_id: str) -> dict[str, Any]:
        if self.repository.get("play_designs", design_id) is None:
            raise KeyError(f"Unknown play design: {design_id}")
        snapshots = sorted([item for item in self.repository.list("play_design_versions") if item.get("design_id") == design_id], key=lambda item: item.get("created_at", ""))
        releases = sorted([item for item in self.repository.list("play_design_releases") if item.get("design_id") == design_id], key=lambda item: item.get("published_at", ""))
        for snapshot in snapshots:
            snapshot["integrity"] = verify_snapshot_integrity(snapshot)
        for release in releases:
            release["integrity"] = verify_release_integrity(release)
        return {"design_id": design_id, "snapshots": snapshots, "releases": releases}

    def diff(self, design_id: str, *, base_snapshot_id: str, compare_snapshot_id: str) -> dict[str, Any]:
        versions = self.versions(design_id)["snapshots"]
        base = next((item for item in versions if item.get("id") == base_snapshot_id), None)
        compare = next((item for item in versions if item.get("id") == compare_snapshot_id), None)
        if base is None or compare is None:
            raise KeyError("Both snapshot ids must belong to the design")
        return {
            "design_id": design_id,
            "base_snapshot_id": base_snapshot_id,
            "compare_snapshot_id": compare_snapshot_id,
            "base_version": base.get("version"),
            "compare_version": compare.get("version"),
            "base_design": deepcopy(base.get("design", {})),
            "compare_design": deepcopy(compare.get("design", {})),
            "diff": design_diff(base.get("design", {}), compare.get("design", {})),
        }

    def merge(self, design_id: str, *, branch_id: str, actor: str, expected_revision: int | None = None) -> dict[str, Any]:
        target = self.repository.get("play_designs", design_id)
        branch = self.repository.get("play_designs", branch_id)
        if target is None or branch is None or branch.get("parent_design_id") != design_id:
            raise KeyError("Target design and a child branch are required for merge")
        base_snapshot = self.repository.get("play_design_versions", branch.get("parent_snapshot_id", ""))
        if base_snapshot is None:
            raise ValueError("Branch is missing its immutable parent snapshot")
        merged = three_way_merge(base_snapshot.get("design", {}), target, branch)
        if merged["conflicts"]:
            return {"status": "conflict", "design_id": design_id, "branch_id": branch_id, "conflicts": merged["conflicts"], "diff": design_diff(target, branch)}
        merged_design = merged["merged"]
        merged_design.pop("release_id", None)
        merged_design.pop("release_bundle", None)
        merged_design.update({"id": design_id, "organization_id": self.repository.organization_id, "status": "draft", "approval": {"state": "draft"}, "merged_branch_id": branch_id, "merge_base_snapshot_id": base_snapshot["id"]})
        saved = self.save(merged_design, actor=actor, expected_revision=expected_revision if expected_revision is not None else target.get("_revision"))
        return {"status": "merged", "design": saved, "branch_id": branch_id, "merge_base_snapshot_id": base_snapshot["id"]}

    def rollback(self, design_id: str, *, snapshot_id: str, actor: str, decision_ref: str, expected_revision: int | None = None) -> dict[str, Any]:
        current = self.repository.get("play_designs", design_id)
        snapshot = self.repository.get("play_design_versions", snapshot_id)
        if current is None or snapshot is None or snapshot.get("design_id") != design_id:
            raise KeyError("Rollback snapshot must belong to the design")
        restored = deepcopy(snapshot.get("design", {}))
        restored.pop("release_id", None)
        restored.pop("release_bundle", None)
        restored.update({"id": design_id, "organization_id": self.repository.organization_id, "status": "draft", "approval": {"state": "draft", "rollback_decision_ref": decision_ref}, "rolled_back_from_snapshot_id": snapshot_id})
        saved = self.save(restored, actor=actor, expected_revision=expected_revision if expected_revision is not None else current.get("_revision"))
        return {"status": "draft_rollback", "design": saved, "rolled_back_from_snapshot_id": snapshot_id, "decision_ref": decision_ref}

    def add_comment(self, design_id: str, *, actor: str, text: str, element_id: str | None = None, parent_comment_id: str | None = None) -> dict[str, Any]:
        if self.repository.get("play_designs", design_id) is None:
            raise KeyError(f"Unknown play design: {design_id}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Comment text is required")
        parent = self.repository.get("play_design_comments", parent_comment_id) if parent_comment_id else None
        if parent_comment_id and (parent is None or parent.get("design_id") != design_id):
            raise KeyError(f"Unknown parent comment: {parent_comment_id}")
        comment_id = f"COMMENT-{design_id}-{len(self.repository.list('play_design_comments')) + 1:04d}"
        thread_id = parent.get("thread_id") if parent else comment_id
        comment = {"id": comment_id, "organization_id": self.repository.organization_id, "design_id": design_id, "thread_id": thread_id, "parent_comment_id": parent_comment_id, "element_id": element_id or (parent.get("element_id") if parent else None), "author": actor, "text": text.strip(), "status": "open", "replies": 0}
        if parent:
            parent["replies"] = int(parent.get("replies", 0)) + 1
            self.repository.put("play_design_comments", parent["id"], parent, actor=actor, reason="play_design_comment_reply_counted")
        return self.repository.put("play_design_comments", comment["id"], comment, actor=actor, reason="play_design_comment_added")

    def reply_comment(self, design_id: str, *, comment_id: str, actor: str, text: str) -> dict[str, Any]:
        return self.add_comment(design_id, actor=actor, text=text, parent_comment_id=comment_id)

    def resolve_comment(self, design_id: str, *, comment_id: str, actor: str, resolved: bool = True) -> dict[str, Any]:
        if self.repository.get("play_designs", design_id) is None:
            raise KeyError(f"Unknown play design: {design_id}")
        comment = self.repository.get("play_design_comments", comment_id)
        if comment is None or comment.get("design_id") != design_id:
            raise KeyError(f"Unknown comment: {comment_id}")
        comment["status"] = "resolved" if resolved else "open"
        comment["resolved_by"] = actor if resolved else None
        comment["resolved_at"] = datetime.now(timezone.utc).isoformat() if resolved else None
        return self.repository.put("play_design_comments", comment_id, comment, actor=actor, reason="play_design_comment_resolved" if resolved else "play_design_comment_reopened")

    def comments(self, design_id: str) -> list[dict[str, Any]]:
        comments = [item for item in self.repository.list("play_design_comments") if item.get("design_id") == design_id]
        return sorted(comments, key=lambda item: item.get("_saved_at", ""))
