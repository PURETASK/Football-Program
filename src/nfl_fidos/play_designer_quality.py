"""Deterministic Play Designer performance, accessibility, and render gates."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .play_design_exports import build_export
from .play_design_convergence import run_convergence_rehearsal
from .play_legality import validate_advanced_legality, validate_rule_profile_catalog


class _AccessibilityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.labels = 0
        self.form_controls = 0
        self.unlabelled_controls = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "label":
            self.labels += 1
        if tag in {"input", "select", "textarea", "button"}:
            self.form_controls += 1
            if tag == "button":
                return
            if not values.get("id") and not values.get("name") and not values.get("aria-label") and not values.get("aria-labelledby"):
                self.unlabelled_controls += 1


def _stress_design(element_count: int) -> dict[str, Any]:
    players = [{"id": f"P{index}", "position": "WR", "start": {"x": 5 + (index % 10) * 9, "y": 5 + (index // 10) * 4}} for index in range(11)]
    elements = []
    for index in range(element_count):
        lane = index % 50
        elements.append({"id": f"ROUTE-{index}", "kind": "route", "player_id": f"P{index % 11}", "type": "go", "points": [{"x": 2, "y": 1 + lane}, {"x": 4, "y": 1 + lane}], "arrow_style": "route", "start_ms": 0, "end_ms": 1200})
    return {"id": "QUALITY-STRESS-001", "version": "1.0.0", "unit": "offense", "concept": "stress", "formation": "synthetic", "players": players, "elements": elements, "timeline": {"snap_ms": 0}, "route_collision_policy": "warn"}


def run_large_play_rehearsal(*, element_count: int = 250, max_duration_ms: float = 2000.0) -> dict[str, Any]:
    if element_count <= 0 or element_count > 1000:
        raise ValueError("element_count must be between 1 and 1000")
    design = _stress_design(element_count)
    started = time.perf_counter()
    findings = validate_advanced_legality(design)
    duration_ms = (time.perf_counter() - started) * 1000
    return {"status": "passed" if duration_ms <= max_duration_ms else "blocked", "element_count": element_count, "duration_ms": round(duration_ms, 3), "budget_ms": max_duration_ms, "finding_count": len(findings), "external_state_changed": False}


def _render_fingerprint() -> tuple[str, str]:
    design = _stress_design(1)
    design["id"] = "QUALITY-VISUAL-BASELINE-001"
    artifact = build_export(designs=[design], kind="play_card", format="svg", branding={"team_name": "NFL FIDOS", "organization_name": "Quality Gate"})
    content = base64.b64decode(artifact["content_base64"])
    return artifact["sha256"], hashlib.sha256(content).hexdigest()


def run_export_matrix_rehearsal() -> dict[str, Any]:
    """Render every supported local export family and verify its contract."""
    design = _stress_design(3)
    matrix = (
        ("play_card", "svg", "single"),
        ("play_card", "png", "single"),
        ("play_card", "pdf", "single"),
        ("play_card", "html", "single"),
        ("play_card", "json", "single"),
        ("call_sheet", "pdf", "table"),
        ("call_sheet", "html", "table"),
        ("call_sheet", "csv", "table"),
        ("wristband", "pdf", "wristband_2col"),
        ("wristband", "html", "wristband_2col"),
        ("wristband", "csv", "wristband_2col"),
        ("install_sheet", "pdf", "single"),
        ("install_sheet", "html", "single"),
        ("install_sheet", "csv", "single"),
    )
    results: list[dict[str, Any]] = []
    for kind, format_name, layout in matrix:
        try:
            artifact = build_export(designs=[design], kind=kind, format=format_name, layout=layout, black_white=True)
            integrity = artifact.get("integrity", {})
            passed = integrity.get("status") == "verified" and artifact.get("bytes", 0) > 0 and artifact.get("layout") == layout
            results.append({"kind": kind, "format": format_name, "layout": layout, "artifact_id": artifact.get("artifact_id"), "bytes": artifact.get("bytes", 0), "print_profile": artifact.get("print_profile"), "page_count": artifact.get("page_count"), "integrity": integrity.get("status"), "passed": passed})
        except (TypeError, ValueError, KeyError, OSError) as exc:
            results.append({"kind": kind, "format": format_name, "layout": layout, "passed": False, "error": str(exc)})
    return {"status": "passed" if all(item["passed"] for item in results) else "blocked", "case_count": len(results), "passed_count": sum(1 for item in results if item["passed"]), "results": results, "external_state_changed": False}


def run_play_designer_quality_gates(*, root: str | Path, element_count: int = 250) -> dict[str, Any]:
    root_path = Path(root).resolve()
    document = (root_path / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
    designer = (root_path / "ui" / "play-designer.js").read_text(encoding="utf-8")
    interactive = (root_path / "ui" / "play-designer-interactive.js").read_text(encoding="utf-8")
    sync = (root_path / "ui" / "play-designer-sync.js").read_text(encoding="utf-8")
    exports = (root_path / "src" / "nfl_fidos" / "play_design_exports.py").read_text(encoding="utf-8")
    parser = _AccessibilityParser()
    parser.feed(document)
    accessibility_tokens = ("lang=\"en\"", "viewport", "skip-link", "main-content", "prefers-reduced-motion", "focus-visible", "aria-label", "role=\"status\"", "play-designer-legality.js")
    accessibility_issues = [token for token in accessibility_tokens if token not in document]
    if parser.unlabelled_controls:
        accessibility_issues.append(f"{parser.unlabelled_controls} static form controls have no accessible identifier")
    performance = run_large_play_rehearsal(element_count=element_count)
    convergence = run_convergence_rehearsal()
    export_matrix = run_export_matrix_rehearsal()
    profile_catalog = validate_rule_profile_catalog()
    renderer_sha256, svg_sha256 = _render_fingerprint()
    baseline_path = root_path / "control" / "play-designer-visual-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else {}
    visual_issues = []
    if baseline.get("svg_sha256") and baseline.get("svg_sha256") != svg_sha256:
        visual_issues.append("deterministic SVG fingerprint differs from the approved local baseline")
    checks = [
        {"id": "PDQ-ACCESSIBILITY", "status": "passed" if not accessibility_issues else "blocked", "issues": accessibility_issues, "static_control_count": parser.form_controls, "label_count": parser.labels},
        {"id": "PDQ-KEYBOARD-AUTHORING", "status": "passed" if all(token in interactive for token in ("keydown", "tabindex", "aria-")) else "blocked", "issues": [] if all(token in interactive for token in ("keydown", "tabindex", "aria-")) else ["keyboard authoring tokens are incomplete"]},
        {"id": "PDQ-OFFLINE-ENCRYPTION", "status": "passed" if all(token in sync for token in ("AES-GCM", "crypto.subtle", "encrypted")) else "blocked", "issues": [] if all(token in sync for token in ("AES-GCM", "crypto.subtle", "encrypted")) else ["encrypted offline storage controls are incomplete"]},
        {"id": "PDQ-PRINT-ACCESSIBILITY", "status": "passed" if all(token in exports for token in ("accessible_text", "black_white", "Page ")) else "blocked", "issues": [] if all(token in exports for token in ("accessible_text", "black_white", "Page ")) else ["print export accessibility tokens are incomplete"]},
        {"id": "PDQ-LARGE-PLAY-PERFORMANCE", "status": performance["status"], **performance},
        {"id": "PDQ-COLLAB-CONVERGENCE-REHEARSAL", "status": convergence["status"], **convergence},
        {"id": "PDQ-EXPORT-MATRIX-REHEARSAL", "status": export_matrix["status"], **export_matrix},
        {"id": "PDQ-RULE-PROFILE-CATALOG", "status": "passed" if profile_catalog["status"] == "valid" else "blocked", "catalog_status": profile_catalog["status"], "path": profile_catalog["path"], "profile_count": profile_catalog.get("profile_count", 0), "issues": profile_catalog["issues"]},
        {"id": "PDQ-VISUAL-REGRESSION", "status": "passed" if not visual_issues else "blocked", "issues": visual_issues, "renderer_sha256": renderer_sha256, "svg_sha256": svg_sha256, "baseline_path": str(baseline_path)},
    ]
    return {"status": "passed" if all(item["status"] == "passed" for item in checks) else "blocked", "checks": checks, "limitations": ["Visual regression is deterministic SVG fingerprinting; moderated tablet and screen-reader sessions still require human pilot participants."], "production_implementation_allowed": False, "external_state_changed": False}
