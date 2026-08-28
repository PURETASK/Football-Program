"""Deterministic accessible SVG rendering for validated visual play models."""

from __future__ import annotations

from html import escape
from typing import Any

from .visual_playbook import FIELD_LENGTH, FIELD_WIDTH, validate_visual_play


SVG_WIDTH = 1200
SVG_HEIGHT = 533


def _x(value: float) -> str:
    return f"{value / FIELD_LENGTH * SVG_WIDTH:.2f}"


def _y(value: float) -> str:
    return f"{value / FIELD_WIDTH * SVG_HEIGHT:.2f}"


def render_visual_svg(*, visual: dict[str, Any], role: str | None = None, scenario: dict[str, Any] | None = None) -> str:
    """Render a validated canonical visual or separately labeled what-if scenario."""
    issues = validate_visual_play(visual)
    if issues or visual.get("status") != "renderable":
        raise ValueError({"code":"SVG-VISUAL-INVALID", "issues":issues})
    player_map = {player.get("id"): player for player in visual["players"]}
    selected_ids = {player_id for player_id, player in player_map.items() if role is None or player.get("role") == role}
    mode = "what-if" if scenario else "canonical"
    title = f"{visual['play_id']} {role or 'coach'} {mode} view"
    elements: list[str] = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" role="img" aria-labelledby="title desc" data-visual-id="{escape(visual["id"])}" data-mode="{mode}">', f'<title id="title">{escape(title)}</title>', f'<desc id="desc">NFL play diagram with role labels and assignment paths. This is a {mode} rendering; canonical play data is not replaced.</desc>', f'<rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="#2c7a45" stroke="#fff" stroke-width="4"/>']
    for yard in range(0, 121, 10):
        x = _x(yard)
        elements.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{SVG_HEIGHT}" stroke="#ffffff" stroke-opacity=".35"/>')
        elements.append(f'<text x="{x}" y="18" fill="#ffffff" font-size="14" text-anchor="middle">{yard}</text>')
    for path in visual["paths"]:
        points = " ".join(f"{_x(point['x'])},{_y(point['y'])}" for point in path["points"])
        player = player_map.get(path.get("player_id"), {})
        visible = path.get("player_id") in selected_ids
        opacity = "1" if visible else ".22"
        label = f"{player.get('role', path.get('player_id'))} path"
        elements.append(f'<polyline points="{points}" fill="none" stroke="#ffd166" stroke-width="4" opacity="{opacity}" aria-label="{escape(label)}"/>')
    for player_id, player in player_map.items():
        visible = player_id in selected_ids
        opacity = "1" if visible else ".35"
        x, y = _x(player["position"]["x"]), _y(player["position"]["y"])
        role_label = escape(str(player.get("role", player_id)))
        elements.append(f'<g opacity="{opacity}" aria-label="Player {role_label}"><circle cx="{x}" cy="{y}" r="14" fill="#17324d" stroke="#fff" stroke-width="2"/><text x="{x}" y="{float(y) + 5:.2f}" fill="#fff" font-size="11" text-anchor="middle">{role_label}</text></g>')
    if scenario:
        elements.append(f'<text x="20" y="{SVG_HEIGHT - 18}" fill="#fff" font-size="16">WHAT-IF SCENARIO — HUMAN REVIEW REQUIRED — {escape(str(scenario.get("type", "adjustment")))}</text>')
    else:
        elements.append(f'<text x="20" y="{SVG_HEIGHT - 18}" fill="#fff" font-size="16">CANONICAL VIEW — {escape(role or "COACH")}</text>')
    elements.append("</svg>")
    return "".join(elements)
