"""Validation and lookup for seasonal and role-specific drill variants."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .drill_library import validate_drill
from .position_drill_library import load_position_drill_library, validate_position_drill_library


SEASONS = {"offseason", "preseason", "regular_season", "postseason"}


def validate_seasonal_role_variants(*, variants_library: dict[str, Any], base_library: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    base = base_library or load_position_drill_library()
    base_validation = validate_position_drill_library(base)
    if base_validation["status"] != "valid":
        errors.append({"code": "VARIANT-BASE-LIBRARY", "message": "Base position drill library must validate before variants can be accepted", "path": "base_library"})
    base_drills = {drill.get("id"): drill for entry in base.get("positions", []) for drill in entry.get("drills", [])}
    variants = variants_library.get("variants", [])
    seen: set[str] = set()
    for index, variant in enumerate(variants):
        path = f"variants[{index}]"
        variant_id = variant.get("variant_id")
        if not isinstance(variant_id, str) or not variant_id.startswith("VARIANT-DRILL-") or variant_id in seen:
            errors.append({"code": "VARIANT-ID", "message": "Variant IDs must be unique and use VARIANT-DRILL- prefix", "path": f"{path}.variant_id"})
        seen.add(variant_id)
        base_drill = base_drills.get(variant.get("base_drill_id"))
        if base_drill is None:
            errors.append({"code": "VARIANT-BASE", "message": "Variant must reference an existing base drill", "path": f"{path}.base_drill_id"})
            continue
        if variant.get("position") != base_drill.get("position"):
            errors.append({"code": "VARIANT-POSITION", "message": "Variant position must match the base drill", "path": f"{path}.position"})
        if variant.get("season") not in SEASONS:
            errors.append({"code": "VARIANT-SEASON", "message": "Variant season is not controlled", "path": f"{path}.season"})
        adaptation = variant.get("adaptation", {})
        for field in ("objective", "load_change", "safety_controls", "evaluation_focus"):
            if not adaptation.get(field):
                errors.append({"code": "VARIANT-ADAPTATION", "message": f"Variant adaptation requires {field}", "path": f"{path}.adaptation.{field}"})
        effective = copy.deepcopy(base_drill)
        effective.update(copy.deepcopy(variant.get("overrides", {})))
        effective["id"] = f"DRILL-{variant_id.removeprefix('VARIANT-DRILL-')}"
        effective["position"] = variant.get("position")
        errors.extend({"code": "VARIANT-DRILL", "message": issue["message"], "path": f"{path}.{issue['path']}"} for issue in validate_drill(effective))
    return {"library_id": variants_library.get("variant_library_id"), "status": "valid" if not errors else "invalid", "errors": errors, "variant_count": len(variants), "base_drill_count": len(base_drills), "seasons": sorted({variant.get("season") for variant in variants if variant.get("season")})}


def load_seasonal_role_variants(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path else Path(__file__).resolve().parents[2] / "development" / "seasonal-role-drill-variants.json"
    return json.loads(source.read_text(encoding="utf-8"))
