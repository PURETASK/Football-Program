"""Production-oriented play-card, call-sheet, wristband, and install exports."""

from __future__ import annotations

import base64
import csv
import hashlib
import html
import io
import json
import math
import re
import struct
import zlib
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .play_creation import validate_legality, validate_play_design
from .play_legality import RULE_PROFILE_CATALOG
from .play_timeline import normalize_timeline_design

try:  # Optional in the local foundation; the export contract remains testable without it.
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover - exercised only in minimal packaging.
    colors = None
    letter = None
    canvas = None

try:  # Optional PNG support for local packaging.
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - exercised only in minimal packaging.
    Image = None
    ImageDraw = None
    ImageFont = None


EXPORT_FORMATS = {"pdf", "svg", "png", "json", "csv", "html"}
EXPORT_KINDS = {"play_card", "call_sheet", "wristband", "install_sheet"}
EXPORT_LAYOUTS = {"single", "grid_2x2", "grid_3x2", "table", "wristband_2col", "wristband_3col", "wristband_4col"}
WRISTBAND_LAYOUTS = {
    "wristband_2col": {"columns": 2, "rows": 16, "title": "Two-column wristband", "call_chars": 28, "detail_chars": 34, "call_size": 8, "detail_size": 6.5},
    "wristband_3col": {"columns": 3, "rows": 18, "title": "Three-column compact wristband", "call_chars": 19, "detail_chars": 22, "call_size": 7, "detail_size": 5.8},
    "wristband_4col": {"columns": 4, "rows": 18, "title": "Four-column sideline strip", "call_chars": 14, "detail_chars": 16, "call_size": 6.2, "detail_size": 5.1},
}
PRINT_PROFILES = {
    "letter_portrait": {"page_size": "letter", "orientation": "portrait", "safe_area_in": 0.35},
    "letter_portrait_wristband": {"page_size": "letter", "orientation": "portrait", "safe_area_in": 0.2},
    "data_export": {"page_size": None, "orientation": None, "safe_area_in": None},
}
DEFAULT_BRAND = {"organization_name": "NFL FIDOS", "team_name": "Team Playbook", "accent_color": "#10213d", "footer": "Human-reviewed play artifact"}
COLOR_BY_KIND = {"route": "#2563eb", "motion": "#7c3aed", "run": "#087443", "block": "#8a5500", "read": "#0891b2", "coverage": "#334155", "rush": "#a51d2d", "fit": "#a51d2d", "stunt": "#a51d2d", "rotation": "#0f766e", "annotation": "#475569"}


def _safe(value: Any, fallback: str = "play") -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or fallback)).strip("-")
    return text or fallback


def _brand(branding: dict[str, Any] | None) -> dict[str, str]:
    output = dict(DEFAULT_BRAND)
    if isinstance(branding, dict):
        for key in output:
            if branding.get(key) not in (None, ""):
                output[key] = str(branding[key])
    if not re.match(r"^#[0-9A-Fa-f]{6}$", output["accent_color"]):
        output["accent_color"] = DEFAULT_BRAND["accent_color"]
    return output


def _element_id(element: dict[str, Any], index: int) -> str:
    return str(element.get("id") or f"ELEMENT-{index + 1}")


def _defensive_alignment_label(player: dict[str, Any]) -> str | None:
    technique = player.get("defensive_technique")
    alignment = player.get("defensive_alignment")
    if not technique and not alignment:
        return None
    return " · ".join(filter(None, [f"{technique}-tech" if technique else None, str(alignment).replace("_", " ") if alignment else None]))


def _svg_path(points: list[dict[str, Any]]) -> str:
    return " ".join(("M" if point_index == 0 else "L") + f" {float(point.get('x', 0)):.2f} {float(point.get('y', 0)) + 4:.2f}" for point_index, point in enumerate(points))


def _stroke_style(element: dict[str, Any]) -> tuple[str, str, str]:
    """Normalize authoring semantics into deterministic SVG stroke attributes."""
    line_style = str(element.get("line_style") or element.get("stroke_style") or "solid").lower()
    dash = "6 3" if line_style in {"dashed", "dash"} else "2 2" if line_style in {"dotted", "dot"} else "none"
    try:
        weight = max(0.25, min(3.5, float(element.get("line_weight") or element.get("stroke_width") or 0.55)))
    except (TypeError, ValueError):
        weight = 0.55
    cap = str(element.get("line_cap") or "round").lower()
    if cap not in {"round", "square", "butt"}:
        cap = "round"
    return f"{weight:.2f}", dash, cap


def _marker_attributes(element: dict[str, Any], marker_id: str = "arrow") -> str:
    """Match canvas arrow semantics in exported SVG paths.

    `arrow_style=none` is a deliberate coach choice (for example, a blocking
    landmark or a coverage shell connector), so the export must not add an
    arrow that is absent from the authored diagram.  Arrow ends default to
    the historical finish-arrow behavior for legacy designs.
    """
    if str(element.get("arrow_style") or "").lower() == "none":
        return ""
    ends = str(element.get("arrow_ends") or "end").lower()
    attributes: list[str] = []
    if ends in {"start", "both"}:
        attributes.append(f' marker-start="url(#{marker_id})"')
    if ends in {"end", "both"}:
        attributes.append(f' marker-end="url(#{marker_id})"')
    return "".join(attributes)


def _visible(design: dict[str, Any], role: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    players = [item for item in design.get("players", []) if isinstance(item, dict)]
    elements = [item for item in design.get("elements", []) if isinstance(item, dict)]
    if not role or role.lower() in {"coach", "coach_staff", "staff", "all"}:
        return players, elements
    player_ids = {item.get("id") for item in players if item.get("id") == role or item.get("position") == role or item.get("role") == role}
    if not player_ids:
        raise KeyError(f"Role is not present in design: {role}")
    return [item for item in players if item.get("id") in player_ids], [item for item in elements if item.get("player_id") in player_ids or item.get("visibility") in {"shared", "all"} or item.get("role") in {role, "shared", "all"} or (not item.get("player_id") and item.get("kind") == "annotation")]


def validate_export_design(design: dict[str, Any], *, kind: str, format: str, role: str | None = None, layout: str | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if kind not in EXPORT_KINDS:
        issues.append({"code": "EXPORT-KIND", "message": "Unknown export kind", "path": "kind", "severity": "error"})
    if format not in EXPORT_FORMATS:
        issues.append({"code": "EXPORT-FORMAT", "message": "Unknown export format", "path": "format", "severity": "error"})
    if layout is not None and layout not in EXPORT_LAYOUTS:
        issues.append({"code": "EXPORT-LAYOUT", "message": "Unknown export layout", "path": "layout", "severity": "error"})
    if layout and layout.startswith("wristband_") and kind != "wristband":
        issues.append({"code": "EXPORT-LAYOUT-KIND", "message": "Wristband layouts can only be used for wristband artifacts", "path": "layout", "severity": "error"})
    if layout in {"grid_2x2", "grid_3x2", "table", "wristband_2col", "wristband_3col", "wristband_4col"} and format in {"svg", "png"}:
        issues.append({"code": "EXPORT-LAYOUT-FORMAT", "message": "This layout requires a multi-item PDF or HTML packet format", "path": "layout", "severity": "error"})
    if not isinstance(design, dict) or not design.get("id"):
        issues.append({"code": "EXPORT-DESIGN", "message": "A design id is required", "path": "design.id", "severity": "error"})
        return issues
    validation = design.get("validation", {})
    if validation.get("status") == "invalid":
        issues.append({"code": "EXPORT-DESIGN-INVALID", "message": "Invalid play designs cannot be exported as production artifacts", "path": "validation", "severity": "error"})
    rule_profile = str(design.get("rule_profile") or "nfl")
    profile = RULE_PROFILE_CATALOG.get(rule_profile)
    if profile is None:
        issues.append({"code": "EXPORT-RULE-PROFILE", "message": "Export requires a controlled rule profile", "path": "rule_profile", "severity": "error"})
    elif profile.get("players_on_field") is None:
        issues.append({"code": "EXPORT-RULE-PROFILE-UNRESOLVED", "message": "The selected rule profile requires local player-count rules before export", "path": "rule_profile", "severity": "error"})
    elif not isinstance(design.get("players"), list) or len(design.get("players", [])) != profile["players_on_field"]:
        issues.append({"code": "EXPORT-PLAYER-COUNT", "message": f"The selected {rule_profile} profile requires {profile['players_on_field']} players", "path": "players", "severity": "error", "expected": profile["players_on_field"], "observed": len(design.get("players", [])) if isinstance(design.get("players"), list) else None})
    if profile and profile.get("requires_local_rules") and not design.get("local_rule_source_ref"):
        issues.append({"code": "EXPORT-LOCAL-RULE-SOURCE", "message": "The selected profile requires an approved local rule source before export", "path": "local_rule_source_ref", "severity": "error"})
    if not isinstance(design.get("elements"), list):
        issues.append({"code": "EXPORT-ELEMENTS", "message": "Design elements must be a list", "path": "elements", "severity": "error"})
    else:
        for index, element in enumerate(design["elements"]):
            if not isinstance(element, dict):
                issues.append({"code": "EXPORT-ELEMENT-SHAPE", "message": "Every export element must be an object", "path": f"elements[{index}]", "severity": "error"})
                continue
            if not element.get("id"):
                issues.append({"code": "EXPORT-ELEMENT-ID", "message": "Every production export element should have a stable id", "path": f"elements[{index}].id", "severity": "warning"})
            for path_name in ("points", "path"):
                points = element.get(path_name)
                if not isinstance(points, list):
                    continue
                for point_index, point in enumerate(points):
                    if not isinstance(point, dict):
                        issues.append({"code": "EXPORT-GEOMETRY-POINT", "message": "Every export path point must be an object", "path": f"elements[{index}].{path_name}[{point_index}]", "severity": "error"})
                        continue
                    x, y = point.get("x"), point.get("y")
                    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not (0 <= float(x) <= 100 and 0 <= float(y) <= 53.33):
                        issues.append({"code": "EXPORT-GEOMETRY-BOUNDS", "message": "Path geometry must remain inside the canonical 100 x 53.33 field bounds", "path": f"elements[{index}].{path_name}[{point_index}]", "severity": "error"})
            branches = element.get("branches")
            if isinstance(branches, list):
                for branch_index, branch in enumerate(branches):
                    if not isinstance(branch, dict) or not isinstance(branch.get("points"), list):
                        continue
                    for point_index, point in enumerate(branch["points"]):
                        if not isinstance(point, dict) or not isinstance(point.get("x"), (int, float)) or not isinstance(point.get("y"), (int, float)) or not (0 <= float(point["x"]) <= 100 and 0 <= float(point["y"]) <= 53.33):
                            issues.append({"code": "EXPORT-GEOMETRY-BOUNDS", "message": "Branch geometry must remain inside the canonical 100 x 53.33 field bounds", "path": f"elements[{index}].branches[{branch_index}].points[{point_index}]", "severity": "error"})
    if isinstance(design.get("players"), list):
        for index, player in enumerate(design["players"]):
            point = player.get("start") if isinstance(player, dict) else None
            if not isinstance(point, dict):
                continue
            x, y = point.get("x"), point.get("y")
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not (0 <= float(x) <= 100 and 0 <= float(y) <= 53.33):
                issues.append({"code": "EXPORT-GEOMETRY-BOUNDS", "message": "Player alignment must remain inside the canonical 100 x 53.33 field bounds", "path": f"players[{index}].start", "severity": "error"})
    if kind == "wristband" and not (design.get("call") or design.get("concept") or design.get("name")):
        issues.append({"code": "EXPORT-WRISTBAND-CALL", "message": "Wristband entries need a call or concept label", "path": "concept", "severity": "error"})
    if role:
        try:
            _visible(design, role)
        except KeyError as exc:
            issues.append({"code": "EXPORT-ROLE", "message": str(exc), "path": "role", "severity": "error"})
    return issues


def _svg(design: dict[str, Any], *, role: str | None = None, black_white: bool = False, branding: dict[str, Any] | None = None) -> str:
    brand = _brand(branding)
    players, elements = _visible(design, role)
    colors_by_kind = {key: ("#111827" if black_white else value) for key, value in COLOR_BY_KIND.items()}
    field = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 62" role="img" aria-labelledby="title desc">', f'<title id="title">{html.escape(str(design.get("concept") or design.get("id")))}</title>', f'<desc id="desc">{html.escape(_accessible_text(design, role=role))}</desc>', '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>', '<rect width="100" height="62" fill="#f8fafc"/>', '<rect x="1" y="1" width="98" height="60" rx="1.5" fill="#5a9d52" stroke="#fff" stroke-width=".5"/>']
    for yard in range(0, 101, 10):
        field.append(f'<line x1="{yard}" x2="{yard}" y1="1" y2="61" stroke="#d7f0d0" stroke-width=".25"/>')
    field.append('<line x1="50" x2="50" y1="1" y2="61" stroke="#fff" stroke-width=".35"/>')
    for index, element in enumerate(elements):
        points = element.get("points", [])
        if len(points) < 2:
            continue
        path = " ".join(("M" if point_index == 0 else "L") + f" {float(point.get('x', 0)):.2f} {float(point.get('y', 0)) + 4:.2f}" for point_index, point in enumerate(points))
        kind = element.get("kind", "annotation")
        color = colors_by_kind.get(kind, "#111827")
        stroke_width, dash, cap = _stroke_style(element)
        dash_attr = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        element_id = html.escape(_element_id(element, index))
        label = element.get("type") or element.get("assignment") or element.get("responsibility")
        label_text = str(label or kind)
        field.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="{cap}" stroke-linejoin="round"{dash_attr}{_marker_attributes(element)} style="color:{color}" data-element-id="{element_id}" aria-label="{html.escape(label_text)}"/>')
        for branch in element.get("branches", []) if isinstance(element.get("branches"), list) else []:
            if not isinstance(branch, dict) or len(branch.get("points", [])) < 2:
                continue
            branch_label = f"{branch.get('label') or 'Alternate path'}: {branch.get('condition') or 'conditional'}"
            branch_marker_source = {**element, **branch}
            field.append(f'<path d="{_svg_path(branch["points"])}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="{cap}" stroke-linejoin="round" stroke-dasharray="{dash if dash != "none" else "4 2"}"{_marker_attributes(branch_marker_source)} opacity=".78" style="color:{color}" data-element-id="{element_id}" data-branch-id="{html.escape(str(branch.get("id") or "branch"))}" aria-label="{html.escape(branch_label)}"/>')
        if label:
            last = points[-1]
            field.append(f'<text x="{float(last.get("x", 0)) + 1:.2f}" y="{float(last.get("y", 0)) + 3:.2f}" font-family="Arial,sans-serif" font-size="1.65" fill="{color}">{html.escape(str(label))}</text>')
    visible_player_ids = {item.get("id") for item in players}
    all_players = [item for item in design.get("players", []) if isinstance(item, dict)]
    for index, player in enumerate(all_players):
        if role and player.get("id") not in visible_player_ids:
            continue
        point = player.get("start", {})
        color = "#111827" if black_white else ("#fff" if player.get("unit") != "defense" else "#fee2e2")
        x, y = float(point.get("x", 50)), float(point.get("y", 26.66)) + 4
        field.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.45" fill="{color}" stroke="#111827" stroke-width=".35"/>')
        field.append(f'<text x="{x:.2f}" y="{y + .55:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="1.05" font-weight="700" fill="#111827">{html.escape(str(player.get("position") or index + 1))}</text>')
        alignment_label = _defensive_alignment_label(player) if player.get("unit") == "defense" or design.get("unit") == "defense" else None
        if alignment_label:
            field.append(f'<text x="{x + 2:.2f}" y="{y - 1.25:.2f}" font-family="Arial,sans-serif" font-size=".9" font-weight="700" fill="#111827">{html.escape(alignment_label)}</text>')
    field.append(f'<rect x="1" y="1" width="98" height="3" fill="{html.escape(brand["accent_color"])}" opacity=".94"/><text x="3" y="3.25" font-family="Arial,sans-serif" font-size="1.45" font-weight="700" fill="#fff">{html.escape(brand["team_name"])} - {html.escape(str(design.get("concept") or design.get("id")))}</text>')
    field.append('</svg>')
    return "".join(field)


def _accessible_text(design: dict[str, Any], *, role: str | None = None) -> str:
    players, elements = _visible(design, role)
    lines = [f"{design.get('concept') or design.get('id')} - {design.get('unit', 'unit')} - {design.get('formation', 'formation')}", f"Role: {role or 'coach'}", "Players: " + ", ".join(str(item.get("position") or item.get("id")) for item in players)]
    for index, element in enumerate(elements):
        label = element.get("type") or element.get("assignment") or element.get("responsibility") or element.get("kind", "assignment")
        timing = element.get("timing", {}) if isinstance(element.get("timing"), dict) else {}
        lines.append(f"{index + 1}. {label}; player {element.get('player_id', 'shared')}; timing {timing.get('start_ms', element.get('start_ms', 0))}-{timing.get('end_ms', element.get('end_ms', 'end'))} ms.")
        branches = element.get("branches") if isinstance(element.get("branches"), list) else []
        for branch in branches:
            if isinstance(branch, dict):
                lines.append(f"   Alternate path {branch.get('label') or branch.get('id') or 'branch'}; condition {branch.get('condition') or 'unspecified'}; timing {branch.get('start_ms', timing.get('start_ms', element.get('start_ms', 0)))}-{branch.get('end_ms', timing.get('end_ms', element.get('end_ms', 'end')))} ms.")
    timeline = design.get("timeline") if isinstance(design.get("timeline"), dict) else {}
    events = timeline.get("events") if isinstance(timeline.get("events"), list) else []
    elements_by_id = {item.get("id"): item for item in design.get("elements", []) if isinstance(item, dict) and item.get("id")}
    for event in sorted((item for item in events if isinstance(item, dict)), key=lambda item: (item.get("start_ms", item.get("at_ms", item.get("ms", 0))), str(item.get("id", "")))):
        kind = event.get("kind") or event.get("type") or "cue"
        start = event.get("start_ms", event.get("at_ms", event.get("ms", 0)))
        end = event.get("end_ms")
        clock = f"{start}-{end} ms" if end is not None else f"at {start} ms"
        detail = event.get("label") or event.get("note") or event.get("description") or event.get("element_id") or "shared"
        branch_detail = ""
        branch_id = event.get("branch_id")
        if branch_id:
            element = elements_by_id.get(event.get("element_id"))
            branches = element.get("branches", []) if isinstance(element, dict) and isinstance(element.get("branches"), list) else []
            branch = next((candidate for candidate in branches if isinstance(candidate, dict) and candidate.get("id") == branch_id), None)
            if branch:
                branch_detail = f"; path {branch.get('label') or branch_id} (condition: {branch.get('condition') or 'unspecified'})"
            else:
                branch_detail = f"; path {branch_id}"
        lines.append(f"Timeline {kind}: {detail}{branch_detail}; {clock}.")
    narration = timeline.get("narration") if isinstance(timeline.get("narration"), list) else []
    for cue in sorted((item for item in narration if isinstance(item, dict)), key=lambda item: (item.get("start_ms", 0), str(item.get("id", "")))):
        lines.append(f"Narration ({cue.get('role') or 'coach'}) {cue.get('start_ms', 0)}-{cue.get('end_ms', 'end')} ms: {cue.get('text') or 'Teaching cue.'}")
    return "\n".join(lines)


def _call_rows(designs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, design in enumerate(designs):
        situation = design.get("situation", {}) if isinstance(design.get("situation"), dict) else {}
        rows.append({"slot": index + 1, "code": design.get("wristband_code") or f"{index + 1:02d}", "call": design.get("call") or design.get("concept") or design.get("id"), "unit": design.get("unit", ""), "formation": design.get("formation", ""), "personnel": design.get("personnel", ""), "situation": situation.get("label") or situation.get("down_distance") or situation.get("down") or "", "design_id": design.get("id"), "version": design.get("version", "")})
    return rows


def _csv_payload(rows: list[dict[str, Any]], columns: list[str]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _source_manifest(designs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Return the reproducible source lock that travels with every artifact."""
    manifest = [{
        "design_id": design.get("id"),
        "name": design.get("name") or design.get("concept") or design.get("id"),
        "version": design.get("version"),
        "snapshot_id": design.get("latest_snapshot_id"),
        "content_checksum": design.get("checksum"),
        "renderer_version": design.get("renderer_version"),
        "renderer_checksum": design.get("renderer_checksum"),
        "status": design.get("status"),
        "release_id": design.get("release_id"),
        "approval_state": (design.get("approval") or {}).get("state") if isinstance(design.get("approval"), dict) else None,
    } for design in designs]
    canonical = json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return manifest, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _html_payload(designs: list[dict[str, Any]], *, kind: str, role: str | None, black_white: bool, branding: dict[str, Any] | None, layout: str) -> bytes:
    brand = _brand(branding)
    cards = []
    for design in designs:
        svg = _svg(design, role=role, black_white=black_white, branding=brand)
        cards.append(f'<article class="play-card"><h2>{html.escape(str(design.get("concept") or design.get("id")))}</h2><p>{html.escape(str(design.get("unit", "")).title())} - {html.escape(str(design.get("formation", "")))} - {html.escape(str(design.get("personnel", "")))}</p>{svg}<h3>Assignments</h3><pre>{html.escape(_accessible_text(design, role=role))}</pre></article>')
    layout_class = "packet-grid-2x2" if layout == "grid_2x2" else "packet-grid-3x2" if layout == "grid_3x2" else "packet-list"
    payload = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(brand["team_name"])} {html.escape(kind)}</title><style>@page{{size:letter;margin:.45in}}:root{{font-family:Arial,sans-serif;color:#172033}}body{{margin:0}}header{{border-bottom:5px solid {brand["accent_color"]};padding:0 0 8px;margin-bottom:14px}}h1{{font-size:20px;margin:0}}h2{{font-size:16px;margin:4px 0}}h3{{font-size:12px;margin:7px 0 3px}}p{{font-size:10px;color:#475569}}.packet-grid-2x2,.packet-grid-3x2{{display:grid;gap:10px;align-items:start}}.packet-grid-2x2{{grid-template-columns:1fr 1fr}}.packet-grid-3x2{{grid-template-columns:1fr 1fr 1fr}}.packet-list{{display:block}}.play-card{{break-inside:avoid;border:1px solid #cbd5e1;border-radius:8px;padding:10px;margin:0 0 12px}}.packet-grid-2x2 .play-card,.packet-grid-3x2 .play-card{{margin:0;padding:6px}}.play-card svg{{width:100%;height:auto;max-height:4.1in}}pre{{white-space:pre-wrap;font-size:9px;line-height:1.35;margin:0}}footer{{position:fixed;bottom:0;left:0;right:0;text-align:center;font-size:8px;color:#64748b}}@media print{{.play-card{{page-break-inside:avoid}}}}</style></head><body><header><h1>{html.escape(brand["team_name"])} - {html.escape(brand["organization_name"])}</h1><p>{html.escape(brand["footer"])} - {datetime.now(timezone.utc).date().isoformat()}</p></header><main class="{layout_class}">{"".join(cards)}</main><footer>Page <span class="pageNumber"></span></footer></body></html>'
    return payload.encode("utf-8")


def _draw_field(pdf: Any, design: dict[str, Any], *, x: float, y: float, width: float, height: float, role: str | None, black_white: bool) -> None:
    players, elements = _visible(design, role)
    pdf.saveState()
    pdf.setFillColor(colors.HexColor("#5a9d52") if not black_white else colors.white)
    pdf.setStrokeColor(colors.HexColor("#111827"))
    pdf.rect(x, y, width, height, fill=1, stroke=1)
    pdf.setStrokeColor(colors.HexColor("#d7f0d0") if not black_white else colors.HexColor("#9ca3af"))
    for yard in range(0, 101, 10):
        px = x + (yard / 100) * width
        pdf.line(px, y, px, y + height)
    for index, element in enumerate(elements):
        points = element.get("points", [])
        if len(points) < 2:
            continue
        color = colors.HexColor("#111827" if black_white else COLOR_BY_KIND.get(element.get("kind"), "#111827"))
        pdf.setStrokeColor(color)
        pdf.setFillColor(color)
        stroke_width, dash, _ = _stroke_style(element)
        pdf.setLineWidth(max(0.8, float(stroke_width) * 2.2))

        def draw_path(path_points: list[dict[str, Any]], *, alternate: bool = False, style_source: dict[str, Any] | None = None) -> None:
            if len(path_points) < 2:
                return
            if alternate or dash != "none":
                pdf.setDash(4, 3)
            for point_index in range(1, len(path_points)):
                p1, p2 = path_points[point_index - 1], path_points[point_index]
                x1, y1 = x + float(p1.get("x", 0)) / 100 * width, y + height - float(p1.get("y", 0)) / 53.33 * height
                x2, y2 = x + float(p2.get("x", 0)) / 100 * width, y + height - float(p2.get("y", 0)) / 53.33 * height
                pdf.line(x1, y1, x2, y2)
            def field_point(point: dict[str, Any]) -> tuple[float, float]:
                return (x + float(point.get("x", 0)) / 100 * width, y + height - float(point.get("y", 0)) / 53.33 * height)

            def draw_arrow(endpoint: dict[str, Any], previous: dict[str, Any]) -> None:
                ex, ey = field_point(endpoint)
                px, py = field_point(previous)
                angle = math.atan2(ey - py, ex - px)
                arrow_size = 6
                pdf.circle(ex, ey, 2.2, fill=1, stroke=0)
                arrow = pdf.beginPath(); arrow.moveTo(ex, ey)
                arrow.lineTo(ex - arrow_size * math.cos(angle - 0.48), ey - arrow_size * math.sin(angle - 0.48))
                arrow.lineTo(ex - arrow_size * math.cos(angle + 0.48), ey - arrow_size * math.sin(angle + 0.48)); arrow.close()
                pdf.drawPath(arrow, fill=1, stroke=0)

            source = style_source or element
            arrow_style = str(source.get("arrow_style") or "").lower()
            arrow_ends = str(source.get("arrow_ends") or "end").lower()
            if arrow_style != "none":
                if arrow_ends in {"start", "both"}:
                    draw_arrow(path_points[0], path_points[1])
                if arrow_ends in {"end", "both"}:
                    draw_arrow(path_points[-1], path_points[-2])
            pdf.setDash()

        draw_path(points)
        for branch in element.get("branches", []) if isinstance(element.get("branches"), list) else []:
            if isinstance(branch, dict):
                draw_path(branch.get("points", []), alternate=True, style_source={**element, **branch})
        label = str(element.get("type") or element.get("assignment") or element.get("kind", ""))[:18]
        pdf.setFont("Helvetica", 6.5)
        pdf.drawString(lx + 3, ly + 2, label)
    for player in players:
        point = player.get("start", {})
        px, py = x + float(point.get("x", 50)) / 100 * width, y + height - float(point.get("y", 26.66)) / 53.33 * height
        pdf.setFillColor(colors.white if not black_white else colors.white)
        pdf.setStrokeColor(colors.black)
        pdf.circle(px, py, 6, fill=1, stroke=1)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 5.5)
        pdf.drawCentredString(px, py - 2, str(player.get("position") or "P")[:5])
        alignment_label = _defensive_alignment_label(player) if design.get("unit") == "defense" else None
        if alignment_label:
            pdf.setFont("Helvetica", 5.2)
            pdf.drawString(px + 7, py + 4, alignment_label[:22])
    pdf.restoreState()


def _minimal_pdf_payload(designs: list[dict[str, Any]], *, kind: str, role: str | None, branding: dict[str, Any] | None) -> bytes:
    """Keep the contract usable in a minimal Python image; full deployments use ReportLab."""
    brand = _brand(branding)
    lines = [f"{brand['team_name']} - {brand['organization_name']}", kind.replace("_", " ").title()]
    for design in designs:
        lines.append(str(design.get("concept") or design.get("id")))
        lines.extend(_accessible_text(design, role=role).splitlines())
    stream = ["BT", "/F1 10 Tf", "40 760 Td"]
    for line in lines[:55]:
        safe_line = str(line).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:120]
        stream.append(f"({safe_line}) Tj")
        stream.append("0 -14 Td")
    stream.append("ET")
    content = "\n".join(stream).encode("latin-1", "replace")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output));output.extend(f"{index} 0 obj\n".encode("ascii"));output.extend(obj);output.extend(b"\nendobj\n")
    xref = len(output);output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    output.extend("".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:]).encode("ascii"));output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"));return bytes(output)


def _pdf_header(pdf: Any, *, brand: dict[str, str], kind: str, page_index: int, total_pages: int, page_width: float, page_height: float) -> None:
    pdf.setFillColor(colors.HexColor(brand["accent_color"]))
    pdf.rect(0, page_height - 42, page_width, 42, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(30, page_height - 25, f"{brand['team_name']} - {brand['organization_name']}")
    pdf.setFont("Helvetica", 7.5)
    pdf.drawRightString(page_width - 30, page_height - 25, f"{kind.replace('_', ' ').title()} | {page_index}/{total_pages}")


def _packet_pdf_payload(designs: list[dict[str, Any]], *, kind: str, role: str | None, black_white: bool, branding: dict[str, Any] | None, layout: str) -> bytes:
    if canvas is None or colors is None or letter is None:
        return _minimal_pdf_payload(designs, kind=kind, role=role, branding=branding)
    brand = _brand(branding)
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=letter, pageCompression=1)
    page_width, page_height = letter
    rows = _call_rows(designs)
    if kind == "call_sheet":
        per_page = 27
        total_pages = max(1, math.ceil(len(rows) / per_page))
        for page_index in range(total_pages):
            _pdf_header(pdf, brand=brand, kind=kind, page_index=page_index + 1, total_pages=total_pages, page_width=page_width, page_height=page_height)
            top = page_height - 70
            pdf.setFillColor(colors.HexColor("#172033"));pdf.setFont("Helvetica-Bold", 8)
            headers = ["Slot", "Code", "Call", "Unit", "Formation", "Situation"]
            widths = [32, 38, 142, 58, 105, 130]
            cursor = 30
            for header, width in zip(headers, widths):
                pdf.drawString(cursor, top, header);cursor += width
            pdf.setFont("Helvetica", 7.5)
            for row_index, row in enumerate(rows[page_index * per_page:(page_index + 1) * per_page]):
                top -= 22
                pdf.setFillColor(colors.HexColor("#f8fafc") if row_index % 2 == 0 else colors.white)
                pdf.roundRect(26, top - 8, page_width - 52, 18, 3, fill=1, stroke=0)
                pdf.setFillColor(colors.black);cursor = 30
                for value, width in zip([row["slot"], row["code"], row["call"], row["unit"], row["formation"], row["situation"]], widths):
                    pdf.drawString(cursor, top - 2, str(value)[:24]);cursor += width
            pdf.setFillColor(colors.HexColor("#64748b"));pdf.setFont("Helvetica", 7)
            pdf.drawCentredString(page_width / 2, 24, f"{brand['footer']} - Page {page_index + 1} of {total_pages}")
            pdf.showPage()
    else:
        wristband = WRISTBAND_LAYOUTS.get(layout, WRISTBAND_LAYOUTS["wristband_2col"])
        columns = int(wristband["columns"])
        rows_per_page = int(wristband["rows"])
        per_page = columns * rows_per_page
        gap = 10
        card_width = (page_width - 60 - gap * (columns - 1)) / columns
        row_step = 32
        total_pages = max(1, math.ceil(len(rows) / per_page))
        for page_index in range(total_pages):
            _pdf_header(pdf, brand=brand, kind=kind, page_index=page_index + 1, total_pages=total_pages, page_width=page_width, page_height=page_height)
            pdf.setFont("Helvetica-Bold", 9);pdf.setFillColor(colors.black);pdf.drawString(30, page_height - 70, str(wristband["title"]))
            page_rows = rows[page_index * per_page:(page_index + 1) * per_page]
            for row_index, row in enumerate(page_rows):
                column = row_index % columns; row_number = row_index // columns
                x = 30 + column * (card_width + gap); slot_y = page_height - 98 - row_number * row_step
                pdf.setFillColor(colors.HexColor("#f8fafc") if not black_white else colors.white)
                pdf.roundRect(x, slot_y - 14, card_width, 24, 4, fill=1, stroke=1)
                pdf.setFillColor(colors.black);pdf.setFont("Helvetica-Bold", float(wristband["call_size"]));pdf.drawString(x + 6, slot_y, f"{row['code']}  {str(row['call'])[:int(wristband['call_chars'])]}")
                pdf.setFont("Helvetica", float(wristband["detail_size"]));pdf.drawString(x + 6, slot_y - 8, f"{row['unit']} | {row['formation']} | {row['situation']}"[:int(wristband["detail_chars"])])
            pdf.setFillColor(colors.HexColor("#64748b"));pdf.setFont("Helvetica", 7)
            pdf.drawCentredString(page_width / 2, 24, f"{brand['footer']} - Page {page_index + 1} of {total_pages}")
            pdf.showPage()
    pdf.save()
    return stream.getvalue()


def _grid_pdf_payload(designs: list[dict[str, Any]], *, kind: str, role: str | None, black_white: bool, branding: dict[str, Any] | None, layout: str) -> bytes:
    if canvas is None or colors is None or letter is None:
        return _minimal_pdf_payload(designs, kind=kind, role=role, branding=branding)
    brand = _brand(branding)
    columns, rows_per_page = (2, 2) if layout == "grid_2x2" else (3, 2)
    per_page = columns * rows_per_page
    total_pages = max(1, math.ceil(len(designs) / per_page))
    stream = io.BytesIO();pdf = canvas.Canvas(stream, pagesize=letter, pageCompression=1)
    page_width, page_height = letter; gap = 10; card_width = (page_width - 60 - gap * (columns - 1)) / columns; card_height = (page_height - 112 - gap * (rows_per_page - 1)) / rows_per_page
    for page_index in range(total_pages):
        _pdf_header(pdf, brand=brand, kind=kind, page_index=page_index + 1, total_pages=total_pages, page_width=page_width, page_height=page_height)
        for card_index, design in enumerate(designs[page_index * per_page:(page_index + 1) * per_page]):
            column = card_index % columns; row_number = card_index // columns
            x = 30 + column * (card_width + gap); y = page_height - 60 - (row_number + 1) * card_height - row_number * gap
            pdf.setFillColor(colors.white);pdf.setStrokeColor(colors.HexColor("#cbd5e1"));pdf.roundRect(x, y, card_width, card_height, 6, fill=1, stroke=1)
            pdf.setFillColor(colors.HexColor("#172033"));pdf.setFont("Helvetica-Bold", 9);pdf.drawString(x + 8, y + card_height - 15, str(design.get("concept") or design.get("id"))[:28])
            pdf.setFont("Helvetica", 6.5);pdf.drawString(x + 8, y + card_height - 26, f"{design.get('unit', '')} | {design.get('formation', '')} | v{design.get('version', '')}")
            field_height = max(90, card_height - 82)
            _draw_field(pdf, design, x=x + 8, y=y + 38, width=card_width - 16, height=field_height, role=role, black_white=black_white)
            pdf.setFillColor(colors.HexColor("#475569"));pdf.setFont("Helvetica", 5.5);pdf.drawString(x + 8, y + 18, f"{len(design.get('elements', []))} assignments | {design.get('checksum', '')[:10]}")
        pdf.setFillColor(colors.HexColor("#64748b"));pdf.setFont("Helvetica", 7);pdf.drawCentredString(page_width / 2, 24, f"{brand['footer']} - Page {page_index + 1} of {total_pages}")
        pdf.showPage()
    pdf.save();return stream.getvalue()


def _install_sheet_pdf_payload(designs: list[dict[str, Any]], *, role: str | None, black_white: bool, branding: dict[str, Any] | None) -> bytes:
    """Render a coach-facing install handout with a field and assignment ledger."""
    if canvas is None or colors is None or letter is None:
        return _minimal_pdf_payload(designs, kind="install_sheet", role=role, branding=branding)
    brand = _brand(branding)
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=letter, pageCompression=1)
    page_width, page_height = letter
    for page_index, design in enumerate(designs):
        _pdf_header(pdf, brand=brand, kind="install_sheet", page_index=page_index + 1, total_pages=len(designs), page_width=page_width, page_height=page_height)
        title = str(design.get("concept") or design.get("name") or design.get("id"))
        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(30, page_height - 70, title[:60])
        pdf.setFont("Helvetica", 8)
        pdf.drawString(30, page_height - 84, f"{str(design.get('unit', '')).title()} - {design.get('formation', '')} - {design.get('personnel', '')} - v{design.get('version', '')}")
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawString(30, page_height - 98, "Install focus: teach alignment, first movement, assignment, and the coaching cue before adding tempo.")

        _draw_field(pdf, design, x=30, y=page_height - 410, width=300, height=285, role=role, black_white=black_white)
        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(350, page_height - 125, "Assignment ledger")
        pdf.setFont("Helvetica", 6.5)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.drawString(350, page_height - 137, "Position / player | assignment | landmark / timing")

        players, elements = _visible(design, role)
        by_player: dict[str, list[dict[str, Any]]] = {}
        for element in elements:
            by_player.setdefault(str(element.get("player_id") or "shared"), []).append(element)
        player_labels = {str(player.get("id")): str(player.get("position") or player.get("id") or "Player") for player in players}
        ledger: list[tuple[str, dict[str, Any] | None]] = []
        for player in players:
            player_id = str(player.get("id"))
            assignments = by_player.pop(player_id, [])
            ledger.extend((player_labels[player_id], element) for element in assignments) if assignments else ledger.append((player_labels[player_id], None))
        ledger.extend(("Shared", element) for element in by_player.get("shared", []))
        row_y = page_height - 151
        for index, (player_label, element) in enumerate(ledger[:27]):
            if index % 2 == 0:
                pdf.setFillColor(colors.HexColor("#f8fafc") if not black_white else colors.white)
                pdf.roundRect(346, row_y - 5, page_width - 376, 16, 2, fill=1, stroke=0)
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica-Bold", 6.6)
            pdf.drawString(350, row_y, player_label[:14])
            assignment = "No authored assignment" if element is None else str(element.get("type") or element.get("assignment") or element.get("responsibility") or element.get("kind") or "Assignment")
            pdf.setFont("Helvetica", 6.4)
            pdf.drawString(408, row_y, assignment[:27])
            if element:
                points = element.get("points", [])
                landmark = element.get("landmark") or element.get("depth") or (f"{points[-1].get('x', 0)},{points[-1].get('y', 0)}" if points else "")
                timing = element.get("timing", {}) if isinstance(element.get("timing"), dict) else {}
                timing_text = f"{timing.get('start_ms', element.get('start_ms', 0))}-{timing.get('end_ms', element.get('end_ms', 'end'))}ms"
                pdf.drawString(508, row_y, f"{str(landmark)[:13]} / {timing_text[:12]}")
            row_y -= 18

        pdf.setFillColor(colors.HexColor("#172033"))
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(30, page_height - 442, "Teaching notes")
        pdf.setFont("Helvetica", 7.2)
        notes = [str(item.get("text") or item.get("note") or item.get("content")) for item in design.get("elements", []) if isinstance(item, dict) and item.get("kind") == "annotation" and (not role or item.get("visibility") in {"shared", "all"} or item.get("role") in {role, "shared", "all"})]
        notes = notes or ["Confirm the alignment landmark, assignment ownership, and correction cue before releasing the install."]
        note_text = pdf.beginText(30, page_height - 456)
        note_text.setLeading(10)
        for note in notes[:8]:
            note_text.textLine(f"• {note[:115]}")
        pdf.drawText(note_text)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString(page_width / 2, 24, f"{brand['footer']} - Page {page_index + 1} of {len(designs)}")
        pdf.showPage()
    pdf.save()
    return stream.getvalue()


def _pdf_payload(designs: list[dict[str, Any]], *, kind: str, role: str | None, black_white: bool, branding: dict[str, Any] | None, layout: str) -> bytes:
    if kind in {"call_sheet", "wristband"}:
        return _packet_pdf_payload(designs, kind=kind, role=role, black_white=black_white, branding=branding, layout=layout)
    if kind == "install_sheet" and layout == "single":
        return _install_sheet_pdf_payload(designs, role=role, black_white=black_white, branding=branding)
    if layout in {"grid_2x2", "grid_3x2"}:
        return _grid_pdf_payload(designs, kind=kind, role=role, black_white=black_white, branding=branding, layout=layout)
    if canvas is None or colors is None or letter is None:
        return _minimal_pdf_payload(designs, kind=kind, role=role, branding=branding)
    brand = _brand(branding)
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=letter, pageCompression=1)
    page_width, page_height = letter
    total_pages = max(1, len(designs))
    for page_index, design in enumerate(designs):
        pdf.setFillColor(colors.HexColor(brand["accent_color"]))
        pdf.rect(0, page_height - 42, page_width, 42, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(30, page_height - 25, f"{brand['team_name']} - {brand['organization_name']}")
        pdf.setFont("Helvetica", 7.5)
        pdf.drawRightString(page_width - 30, page_height - 25, f"{kind.replace('_', ' ').title()} | {page_index + 1}/{total_pages}")
        if kind == "call_sheet":
            rows = _call_rows(designs)
            top = page_height - 70
            pdf.setFillColor(colors.HexColor("#172033"))
            pdf.setFont("Helvetica-Bold", 8)
            headers = ["Slot", "Code", "Call", "Unit", "Formation", "Situation"]
            widths = [32, 38, 142, 58, 105, 130]
            cursor = 30
            for header, width in zip(headers, widths):
                pdf.drawString(cursor, top, header)
                cursor += width
            pdf.setFont("Helvetica", 7.5)
            for row_index, row in enumerate(rows):
                top -= 22
                if top < 54:
                    pdf.showPage()
                    top = page_height - 70
                pdf.setFillColor(colors.HexColor("#f8fafc") if row_index % 2 == 0 else colors.white)
                pdf.roundRect(26, top - 8, page_width - 52, 18, 3, fill=1, stroke=0)
                pdf.setFillColor(colors.black)
                cursor = 30
                values = [row["slot"], row["code"], row["call"], row["unit"], row["formation"], row["situation"]]
                for value, width in zip(values, widths):
                    pdf.drawString(cursor, top - 2, str(value)[:24])
                    cursor += width
        elif kind == "wristband":
            rows = _call_rows(designs)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.setFillColor(colors.black)
            pdf.drawString(30, page_height - 70, "Wristband call layout")
            slot_y = page_height - 98
            for index, row in enumerate(rows):
                column = index % 2
                if column == 0 and index:
                    slot_y -= 36
                x = 30 + column * 270
                pdf.setFillColor(colors.HexColor("#f8fafc"))
                pdf.roundRect(x, slot_y - 14, 250, 26, 4, fill=1, stroke=1)
                pdf.setFillColor(colors.black)
                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawString(x + 8, slot_y, f"{row['code']}  {str(row['call'])[:28]}")
                pdf.setFont("Helvetica", 6.5)
                pdf.drawString(x + 8, slot_y - 9, f"{row['unit']} | {row['formation']} | {row['situation']}")
        else:
            title = str(design.get("concept") or design.get("id"))
            pdf.setFillColor(colors.HexColor("#172033"))
            pdf.setFont("Helvetica-Bold", 15)
            pdf.drawString(30, page_height - 70, title)
            pdf.setFont("Helvetica", 8)
            pdf.drawString(30, page_height - 84, f"{design.get('unit', '').title()} - {design.get('formation', '')} - {design.get('personnel', '')} - v{design.get('version', '')}")
            _draw_field(pdf, design, x=30, y=page_height - 440, width=page_width - 60, height=330, role=role, black_white=black_white)
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(30, page_height - 462, "Accessible assignment text")
            pdf.setFont("Helvetica", 7.5)
            text = pdf.beginText(30, page_height - 476)
            text.setLeading(10)
            for line in _accessible_text(design, role=role).splitlines():
                text.textLine(line[:125])
            pdf.drawText(text)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString(page_width / 2, 24, f"{brand['footer']} - Page {page_index + 1} of {total_pages}")
        pdf.showPage()
    pdf.save()
    return stream.getvalue()


def _minimal_png_payload(branding: dict[str, Any] | None) -> bytes:
    brand = _brand(branding)
    color_text = brand["accent_color"].lstrip("#")
    color = bytes.fromhex(color_text)
    width, height = 64, 32
    raw = b"".join(bytes([0]) + (color if row < 6 else b"\xff\xff\xff") * width for row in range(height))
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def _png_payload(design: dict[str, Any], *, role: str | None, black_white: bool, branding: dict[str, Any] | None) -> bytes:
    if Image is None or ImageDraw is None:
        return _minimal_png_payload(branding)
    brand = _brand(branding)
    image = Image.new("RGB", (1600, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((36, 70, 1564, 930), fill="#5a9d52" if not black_white else "white", outline="#111827", width=4)
    for yard in range(0, 101, 10):
        x = 36 + int(yard / 100 * 1528)
        draw.line((x, 70, x, 930), fill="#d7f0d0" if not black_white else "#9ca3af", width=2)
    players, elements = _visible(design, role)
    for element in elements:
        points = element.get("points", [])
        if len(points) < 2:
            continue
        color = "#111827" if black_white else COLOR_BY_KIND.get(element.get("kind"), "#111827")
        pixel_points = [(36 + int(float(point.get("x", 0)) / 100 * 1528), 70 + int(float(point.get("y", 0)) / 53.33 * 860)) for point in points]
        draw.line(pixel_points, fill=color, width=6, joint="curve")
        draw.ellipse((pixel_points[-1][0] - 8, pixel_points[-1][1] - 8, pixel_points[-1][0] + 8, pixel_points[-1][1] + 8), fill=color)
        for branch in element.get("branches", []) if isinstance(element.get("branches"), list) else []:
            if not isinstance(branch, dict) or len(branch.get("points", [])) < 2:
                continue
            branch_points = [(36 + int(float(point.get("x", 0)) / 100 * 1528), 70 + int(float(point.get("y", 0)) / 53.33 * 860)) for point in branch["points"]]
            for point_index in range(1, len(branch_points)):
                start, end = branch_points[point_index - 1], branch_points[point_index]
                draw.line((start, end), fill=color, width=4)
                draw.ellipse((end[0] - 6, end[1] - 6, end[0] + 6, end[1] + 6), fill=color)
    for player in players:
        point = player.get("start", {})
        x, y = 36 + int(float(point.get("x", 50)) / 100 * 1528), 70 + int(float(point.get("y", 26.66)) / 53.33 * 860)
        draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill="white", outline="#111827", width=3)
        draw.text((x, y), str(player.get("position") or "P"), fill="#111827", anchor="mm")
    draw.rectangle((36, 20, 1564, 58), fill=brand["accent_color"])
    draw.text((55, 39), f"{brand['team_name']} - {design.get('concept') or design.get('id')}", fill="white", anchor="lm")
    stream = io.BytesIO();image.save(stream, format="PNG", optimize=True);return stream.getvalue()


def _effective_layout(*, kind: str, format: str, layout: str | None) -> str:
    """Resolve the renderer layout once so preflight and rendering cannot drift."""
    return layout or ({"call_sheet": "table", "wristband": "wristband_2col"}.get(kind, "single") if format not in {"svg", "png"} else "single")


def _page_count(*, designs: list[dict[str, Any]], kind: str, layout: str) -> int:
    """Return the deterministic page budget used by packet renderers."""
    if kind == "call_sheet":
        return max(1, math.ceil(len(designs) / 27))
    if kind == "wristband":
        config = WRISTBAND_LAYOUTS.get(layout, WRISTBAND_LAYOUTS["wristband_2col"])
        return max(1, math.ceil(len(designs) / (config["columns"] * config["rows"])))
    if layout == "grid_2x2":
        return max(1, math.ceil(len(designs) / 4))
    if layout == "grid_3x2":
        return max(1, math.ceil(len(designs) / 6))
    return max(1, len(designs))


def _source_lock(designs: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe whether an export is tied to a persisted, render-identifiable source."""
    issues: list[dict[str, str]] = []
    for design in designs:
        design_id = str(design.get("id") or "unknown")
        required = {
            "snapshot_id": design.get("latest_snapshot_id"),
            "content_checksum": design.get("checksum"),
            "renderer_version": design.get("renderer_version"),
            "renderer_checksum": design.get("renderer_checksum"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            issues.append({"code": "EXPORT-SOURCE-LOCK-MISSING", "severity": "warning", "message": f"{design_id} is missing source lock fields: {', '.join(missing)}."})
    return {"status": "locked" if not issues else "review", "issues": issues}


def _artifact_page_metadata(*, designs: list[dict[str, Any]], kind: str, format: str, layout: str, role: str | None, black_white: bool) -> dict[str, Any]:
    printer_format = format in {"pdf", "html", "svg", "png"}
    print_profile = "data_export" if not printer_format else "letter_portrait_wristband" if kind == "wristband" else "letter_portrait"
    profile = PRINT_PROFILES[print_profile]
    return {
        "page_size": profile["page_size"],
        "page_count": _page_count(designs=designs, kind=kind, layout=layout),
        "printer_safe": printer_format,
        "print_profile": print_profile,
        "print_orientation": profile["orientation"],
        "safe_area_in": profile["safe_area_in"],
        "color_mode": "black_and_white" if black_white else "color",
        "black_white": black_white,
        "accessibility": {"has_alt_text": format in {"svg", "html"}, "has_accessible_text": format in {"pdf", "svg", "html", "json"}, "role": role or "coach"},
    }


def verify_export_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Verify an in-memory artifact's bytes, identity, source lock, and format signature."""
    issues: list[dict[str, str]] = []
    encoded = artifact.get("content_base64")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (TypeError, ValueError):
        payload = b""
        issues.append({"code": "EXPORT-ARTIFACT-BASE64", "severity": "error", "message": "Artifact content is not valid base64."})
    actual_hash = hashlib.sha256(payload).hexdigest()
    artifact_format = artifact.get("format")
    artifact_kind = artifact.get("kind")
    artifact_layout = artifact.get("layout")
    if artifact_format not in EXPORT_FORMATS:
        issues.append({"code": "EXPORT-ARTIFACT-FORMAT", "severity": "error", "message": "Artifact format is not supported by the export contract."})
    if artifact_kind not in EXPORT_KINDS:
        issues.append({"code": "EXPORT-ARTIFACT-KIND", "severity": "error", "message": "Artifact kind is not supported by the export contract."})
    if artifact_layout not in EXPORT_LAYOUTS:
        issues.append({"code": "EXPORT-ARTIFACT-LAYOUT", "severity": "error", "message": "Artifact layout is not supported by the export contract."})
    if artifact_kind == "wristband" and artifact_layout not in WRISTBAND_LAYOUTS:
        issues.append({"code": "EXPORT-ARTIFACT-LAYOUT-KIND", "severity": "error", "message": "Wristband artifacts must use a wristband layout."})
    if artifact_format in {"svg", "png"} and artifact_layout != "single":
        issues.append({"code": "EXPORT-ARTIFACT-LAYOUT-FORMAT", "severity": "error", "message": "SVG and PNG artifacts must use the single layout."})
    print_profile = artifact.get("print_profile")
    if print_profile not in PRINT_PROFILES:
        issues.append({"code": "EXPORT-PRINT-PROFILE", "severity": "error", "message": "Artifact is missing a supported print profile."})
    elif artifact_format in {"pdf", "html", "svg", "png"} and print_profile == "data_export":
        issues.append({"code": "EXPORT-PRINT-PROFILE-KIND", "severity": "error", "message": "Rendered visual artifacts must use a printer profile."})
    elif artifact_format in {"csv", "json"} and print_profile != "data_export":
        issues.append({"code": "EXPORT-PRINT-PROFILE-DATA", "severity": "error", "message": "CSV and JSON artifacts must use the data-export profile."})
    if artifact.get("color_mode") not in {"color", "black_and_white"}:
        issues.append({"code": "EXPORT-COLOR-MODE", "severity": "error", "message": "Artifact must declare color or black-and-white output mode."})
    if artifact.get("bytes") != len(payload):
        issues.append({"code": "EXPORT-ARTIFACT-BYTES", "severity": "error", "message": "Declared byte length does not match artifact content."})
    if artifact.get("sha256") != actual_hash:
        issues.append({"code": "EXPORT-ARTIFACT-HASH", "severity": "error", "message": "Declared content hash does not match artifact content."})
    if artifact.get("artifact_id") != f"EXPORT-{actual_hash[:16]}":
        issues.append({"code": "EXPORT-ARTIFACT-ID", "severity": "error", "message": "Artifact identifier is not derived from its content hash."})
    manifest = artifact.get("source_manifest")
    canonical = json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    manifest_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if artifact.get("source_manifest_hash") != manifest_hash:
        issues.append({"code": "EXPORT-SOURCE-MANIFEST-HASH", "severity": "error", "message": "Source manifest hash does not match the manifest."})
    signatures = {"pdf": b"%PDF", "png": b"\x89PNG\r\n\x1a\n", "svg": b"<svg", "html": b"<!doctype html", "json": b"{", "csv": b""}
    expected = signatures.get(artifact_format)
    if expected and not payload.lstrip().lower().startswith(expected.lower()):
        issues.append({"code": "EXPORT-FORMAT-SIGNATURE", "severity": "error", "message": f"Payload does not have the expected {artifact_format} signature."})
    if artifact_format == "csv" and (b"\n" not in payload or payload.lstrip().startswith((b"%PDF", b"\x89PNG", b"<svg"))):
        issues.append({"code": "EXPORT-CSV-EMPTY", "severity": "error", "message": "CSV export does not contain a header or row terminator."})
    if artifact_format == "json":
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            issues.append({"code": "EXPORT-JSON-INVALID", "severity": "error", "message": "JSON export is not parseable UTF-8 JSON."})
    if artifact.get("page_count", 0) < 1:
        issues.append({"code": "EXPORT-PAGE-COUNT", "severity": "error", "message": "Export must contain at least one planned page."})
    return {"status": "verified" if not issues else "invalid", "issues": issues, "sha256": actual_hash, "bytes": len(payload)}


def build_export_preflight(*, designs: list[dict[str, Any]], kind: str, format: str, role: str | None = None, layout: str | None = None) -> dict[str, Any]:
    """Validate a packet without rendering or creating an external artifact.

    The response intentionally includes the same source lock that a rendered
    artifact receives. The client can therefore show exactly what is about to
    be exported and require a fresh check when the selection changes.
    """
    if not designs:
        raise ValueError("At least one design is required for export preflight")
    # Keep preflight and rendering on the same canonical contract even when a
    # caller supplies an older draft or an unsaved design directly.
    designs = [normalize_timeline_design(deepcopy(design)) for design in designs]
    effective_layout = _effective_layout(kind=kind, format=format, layout=layout)
    issues: list[dict[str, str]] = []
    for design in designs:
        issues.extend(validate_export_design(design, kind=kind, format=format, role=role, layout=effective_layout))
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    source_manifest, source_manifest_hash = _source_manifest(designs)
    source_lock = _source_lock(designs)
    return {
        "kind": kind,
        "format": format,
        "layout": effective_layout,
        "role": role or "coach",
        "design_count": len(designs),
        "can_render": not errors,
        "validation": {"status": "invalid" if errors else "valid", "issues": issues},
        "source_manifest": source_manifest,
        "source_manifest_hash": source_manifest_hash,
        **_artifact_page_metadata(designs=designs, kind=kind, format=format, layout=effective_layout, role=role, black_white=False),
        "source_lock": source_lock,
    }


def build_export(*, designs: list[dict[str, Any]], kind: str, format: str, role: str | None = None, black_white: bool = False, branding: dict[str, Any] | None = None, layout: str | None = None) -> dict[str, Any]:
    if not designs:
        raise ValueError("At least one design is required for export")
    # Exporters are also used by batch jobs and draft previews, so do not
    # require every caller to have passed through PlayDesignService.save().
    designs = [normalize_timeline_design(deepcopy(design)) for design in designs]
    effective_layout = _effective_layout(kind=kind, format=format, layout=layout)
    issues: list[dict[str, str]] = []
    for design in designs:
        issues.extend(validate_export_design(design, kind=kind, format=format, role=role, layout=effective_layout))
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    if errors:
        raise ValueError({"code": "EXPORT-VALIDATION", "message": "Export validation failed", "issues": issues})
    if format == "svg":
        if len(designs) != 1:
            raise ValueError("SVG export accepts one design at a time")
        payload = _svg(designs[0], role=role, black_white=black_white, branding=branding).encode("utf-8")
        extension, mime = "svg", "image/svg+xml"
    elif format == "png":
        if len(designs) != 1:
            raise ValueError("PNG export accepts one design at a time")
        payload = _png_payload(designs[0], role=role, black_white=black_white, branding=branding)
        extension, mime = "png", "image/png"
    elif format == "pdf":
        payload = _pdf_payload(designs, kind=kind, role=role, black_white=black_white, branding=branding, layout=effective_layout)
        extension, mime = "pdf", "application/pdf"
    elif format == "html":
        payload = _html_payload(designs, kind=kind, role=role, black_white=black_white, branding=branding, layout=effective_layout)
        extension, mime = "html", "text/html; charset=utf-8"
    elif format == "json":
        payload = json.dumps({"kind": kind, "layout": effective_layout, "role": role, "black_white": black_white, "designs": deepcopy(designs)}, indent=2, sort_keys=True).encode("utf-8")
        extension, mime = "json", "application/json"
    elif format == "csv":
        if kind == "wristband":
            columns = ["slot", "code", "call", "unit", "formation", "personnel", "situation", "design_id", "version"]
        elif kind == "install_sheet":
            rows = [{"design_id": design.get("id"), "concept": design.get("concept") or design.get("name"), "unit": design.get("unit"), "formation": design.get("formation"), "player_id": element.get("player_id"), "assignment": element.get("type") or element.get("assignment") or element.get("responsibility") or element.get("kind")} for design in designs for element in design.get("elements", []) if isinstance(element, dict)]
            payload = _csv_payload(rows, ["design_id", "concept", "unit", "formation", "player_id", "assignment"]);extension, mime = "csv", "text/csv"
        else:
            columns = ["slot", "code", "call", "unit", "formation", "personnel", "situation", "design_id", "version"]
        if kind != "install_sheet":
            payload = _csv_payload(_call_rows(designs), columns);extension, mime = "csv", "text/csv"
    else:  # pragma: no cover - guarded by validation above.
        raise ValueError("Unsupported export format")
    content_hash = hashlib.sha256(payload).hexdigest()
    source_manifest, source_manifest_hash = _source_manifest(designs)
    first_id = _safe(designs[0].get("id"), "play")
    filename = f"{first_id}-{kind}{'-bw' if black_white else ''}.{extension}"
    artifact = {"artifact_id": f"EXPORT-{content_hash[:16]}", "filename": filename, "format": format, "kind": kind, "layout": effective_layout, "role": role or "coach", "mime_type": mime, "bytes": len(payload), "sha256": content_hash, "source_manifest": source_manifest, "source_manifest_hash": source_manifest_hash, "validation": {"status": "valid", "issues": issues}, "created_at": datetime.now(timezone.utc).isoformat(), "content_base64": base64.b64encode(payload).decode("ascii")}
    artifact.update(_artifact_page_metadata(designs=designs, kind=kind, format=format, layout=effective_layout, role=role, black_white=black_white))
    artifact["source_lock"] = _source_lock(designs)
    artifact["integrity"] = verify_export_artifact(artifact)
    if artifact["integrity"]["status"] != "verified":
        raise ValueError({"code": "EXPORT-INTEGRITY-INVALID", "message": "Rendered export failed self-verification", "issues": artifact["integrity"]["issues"]})
    return artifact
