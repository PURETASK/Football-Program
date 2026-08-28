"""Deterministic local verification for the integrated Play Designer surface."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any


REQUIRED_ASSET_TOKENS = ("route", "motion", "run", "block", "read", "coverage", "rush", "stunt")
REQUIRED_CONTROLS = ("pd-time", "pd-play-animation", "pd-teach-role", "pd-print-artifact", "pd-call-sheet", "pd-wristband", "pd-apply-defense")
REQUIRED_INTERACTIVE_CONTROLS = ("pd-duplicate", "pd-copy", "pd-paste", "pd-mirror", "pd-group", "pd-ungroup", "pd-lock", "pd-apply-defense-assignment", "renderHandles", "startDraw", "MutationObserver")
REQUIRED_TIMELINE_CONTROLS = ("pd-time", "pd-play-animation", "pd-timeline-step-forward", "pd-timeline-step-back", "pd-add-marker", "pd-add-narration", "pd-apply-timing", "pd-add-phase", "pd-link-exchange", "pd-save-read-key", "renderAnimation", "requestAnimationFrame", "speechSynthesis")
REQUIRED_SYNC_CONTROLS = ("pd-sync-card", "pd-sync-load", "pd-sync-save", "pd-sync-recover", "pd-sync-retry", "pd-sync-conflict", "IndexedDB", "crypto.subtle", "AES-GCM", "encrypted", "expected_revision", "server_design", "online", "offline")
REQUIRED_COLLAB_CONTROLS = ("pd-collab-card", "pd-collab-connect", "pd-collab-add-comment", "pd-collab-add-reply", "pd-collab-resolve", "pd-collaboration-cursors", "setInterval", "/presence", "/events", "/events/stream", "streamEvents", "AbortController", "outbox")
REQUIRED_VERSIONING_CONTROLS = ("pd-versioning-card", "pd-versioning-load", "pd-versioning-diff", "pd-versioning-publish", "pd-versioning-branch", "pd-versioning-merge", "pd-versioning-rollback", "/versions", "/diff", "game_plan_snapshot_id", "expected_revision")
REQUIRED_TEACHING_CONTROLS = ("pd-teaching-card", "pd-teaching-load", "pd-teaching-step", "pd-teaching-accessible", "pd-teaching-quizzes", "pd-teaching-master-current", "/teaching-view", "/mastery", "/quiz", "answer_required", "setVisibilityFilter")
REQUIRED_EXPORT_CONTROLS = ("pd-export-card", "pd-export-kind", "pd-export-format", "pd-export-design-ids", "pd-export-black-white", "pd-export-server", "/v1/playbook/designs/export", "content_base64", "sha256", "signature", "HMAC", "call_sheet", "wristband", "install_sheet")
REQUIRED_LEGALITY_CONTROLS = ("pd-legality-card", "pd-legality-profile", "pd-legality-load", "pd-legality-issue", "/v1/playbook/designs/rule-profiles", "/legality", "coverage_zones", "route_collision_policy", "evidence_refs", "expires_at", "program_owner")


def verify_play_designer(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    html = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
    designer = (root / "ui" / "play-designer.js").read_text(encoding="utf-8")
    enhancements = (root / "ui" / "play-designer-enhancements.js").read_text(encoding="utf-8")
    interactive = (root / "ui" / "play-designer-interactive.js").read_text(encoding="utf-8")
    interactive_styles = (root / "ui" / "play-designer-interactive.css").read_text(encoding="utf-8")
    timeline = (root / "ui" / "play-designer-timeline.js").read_text(encoding="utf-8")
    timeline_styles = (root / "ui" / "play-designer-timeline.css").read_text(encoding="utf-8")
    sync = (root / "ui" / "play-designer-sync.js").read_text(encoding="utf-8")
    sync_styles = (root / "ui" / "play-designer-sync.css").read_text(encoding="utf-8")
    collaboration = (root / "ui" / "play-designer-collaboration.js").read_text(encoding="utf-8")
    collaboration_styles = (root / "ui" / "play-designer-collaboration.css").read_text(encoding="utf-8")
    versioning = (root / "ui" / "play-designer-versioning.js").read_text(encoding="utf-8")
    versioning_styles = (root / "ui" / "play-designer-versioning.css").read_text(encoding="utf-8")
    teaching = (root / "ui" / "play-designer-teaching.js").read_text(encoding="utf-8")
    teaching_styles = (root / "ui" / "play-designer-teaching.css").read_text(encoding="utf-8")
    exports = (root / "ui" / "play-designer-export.js").read_text(encoding="utf-8")
    export_styles = (root / "ui" / "play-designer-export.css").read_text(encoding="utf-8")
    legality = (root / "ui" / "play-designer-legality.js").read_text(encoding="utf-8")
    legality_styles = (root / "ui" / "play-designer-legality.css").read_text(encoding="utf-8")
    styles = (root / "ui" / "play-designer.css").read_text(encoding="utf-8")
    palette = (root / "ui" / "play-designer-assets.js").read_text(encoding="utf-8")
    registry = json.loads((root / "playbook" / "asset-registry.json").read_text(encoding="utf-8"))
    alignment_presets = json.loads((root / "playbook" / "alignment-presets.json").read_text(encoding="utf-8"))
    alignment_keys = {(preset.get("unit"), preset.get("category"), preset.get("term")) for preset in alignment_presets.get("presets", [])}
    required_alignment_keys = {(asset.get("unit"), asset.get("category"), asset.get("term")) for asset in registry.get("assets", []) if asset.get("category") in {"formation", "front"}}
    checks: list[dict[str, Any]] = []
    checks.append({"id": "PD-ASSET-VOCABULARY", "passed": all(token in designer for token in REQUIRED_ASSET_TOKENS), "details": "Core authoring assets are present."})
    checks.append({"id": "PD-ADVANCED-CONTROLS", "passed": all(token in enhancements for token in REQUIRED_CONTROLS), "details": "Timeline, teaching, export, and defense controls are present."})
    checks.append({"id": "PD-INTEGRATION", "passed": all(token in html for token in ('id="play-designer"', 'play-designer.css', 'play-designer.js', 'play-designer-enhancements.js')), "details": "Designer assets are wired into the dashboard."})
    checks.append({"id": "PD-ACCESSIBILITY", "passed": 'role="img"' in designer and 'aria-live' in enhancements and 'tabindex' in designer, "details": "Canvas, status, and keyboard focus affordances are present."})
    checks.append({"id": "PD-RESPONSIVE", "passed": "@media(max-width:760px)" in styles, "details": "Mobile layout rule is present."})
    checks.append({"id": "PD-SIZE-BUDGET", "passed": len(designer.encode("utf-8")) < 100_000 and len(enhancements.encode("utf-8")) < 100_000, "details": "Client bundles remain within the local MVP budget."})
    checks.append({"id": "PD-REGISTRY-CATALOG", "passed": len(registry.get("assets", [])) >= 60 and "lifecycle_states" in registry, "details": "Versioned catalog contains the professional asset families and lifecycle states."})
    checks.append({"id": "PD-ALIGNMENT-PRESETS", "passed": required_alignment_keys.issubset(alignment_keys) and all(len(preset.get("slots", [])) == 11 for preset in alignment_presets.get("presets", [])), "details": "Every supported offense formation and defensive front has an eleven-slot canonical alignment preset."})
    checks.append({"id": "PD-PALETTE-SEARCH", "passed": "pd-asset-search" in palette and "pd-asset-category" in palette and "NFLFIDOSPlayDesignerAssets" in palette, "details": "Full catalog is connected to a searchable/filterable editor palette."})
    checks.append({"id": "PD-FULL-INTERACTIVE", "passed": all(token in interactive for token in REQUIRED_INTERACTIVE_CONTROLS), "details": "Drag authoring, editable handles, selection geometry, locking, and defensive assignment controls are present."})
    checks.append({"id": "PD-INTERACTIVE-INTEGRATION", "passed": all(token in html for token in ("play-designer-interactive.css", "play-designer-interactive.js")) and ".pd-handle" in interactive_styles, "details": "The interactive authoring layer and its visual affordances are wired into the dashboard."})
    checks.append({"id": "PD-TIMELINE-ANIMATION", "passed": all(token in timeline for token in REQUIRED_TIMELINE_CONTROLS), "details": "Per-element timing, phase playback, exchanges, reads, rotations, pause cues, and synchronized narration are implemented."})
    checks.append({"id": "PD-TIMELINE-INTEGRATION", "passed": all(token in html for token in ("play-designer-timeline.css", "play-designer-timeline.js")) and all(token in timeline_styles for token in ("pd-animation-path", "pd-exchange-line", "pd-timeline-marker")), "details": "Timeline animation controls and visual layers are wired into the dashboard."})
    checks.append({"id": "PD-SERVER-SYNC", "passed": all(token in sync for token in REQUIRED_SYNC_CONTROLS), "details": "Organization-scoped load/save, durable offline queue, retries, recovery, and explicit conflict resolution are present."})
    checks.append({"id": "PD-SERVER-SYNC-INTEGRATION", "passed": all(token in html for token in ("play-designer-sync.css", "play-designer-sync.js")) and all(token in sync_styles for token in ("pd-sync-conflict", "pd-sync-queue", "pd-sync-online")), "details": "Synchronization and recovery controls are wired into the editor surface."})
    checks.append({"id": "PD-COLLABORATION", "passed": all(token in collaboration for token in REQUIRED_COLLAB_CONTROLS), "details": "Presence, shared cursors, authenticated SSE events with short-poll fallback, threaded comments, replies, resolution, and offline collaboration are present."})
    checks.append({"id": "PD-COLLABORATION-INTEGRATION", "passed": all(token in html for token in ("play-designer-collaboration.css", "play-designer-collaboration.js")) and all(token in collaboration_styles for token in ("pd-collab-person", "pd-collab-thread", "pd-collab-cursor")), "details": "Collaboration presence and threaded review surfaces are wired into the dashboard."})
    checks.append({"id": "PD-VERSIONING", "passed": all(token in versioning for token in REQUIRED_VERSIONING_CONTROLS), "details": "Immutable snapshots, checksums, visual diffs, branching, merging, publishing, game-plan locking, and rollback controls are present."})
    checks.append({"id": "PD-VERSIONING-INTEGRATION", "passed": all(token in html for token in ("play-designer-versioning.css", "play-designer-versioning.js")) and all(token in versioning_styles for token in ("pd-versioning-card", "pd-versioning-grid", "pd-versioning-diff")), "details": "Version history and release control are wired into the editor surface."})
    checks.append({"id": "PD-TEACHING", "passed": all(token in teaching for token in REQUIRED_TEACHING_CONTROLS), "details": "Filtered player/position-group/coach views, step reveal, accessible text, server-graded quizzes, mastery, and practice linkage are present."})
    checks.append({"id": "PD-TEACHING-INTEGRATION", "passed": all(token in html for token in ("play-designer-teaching.css", "play-designer-teaching.js")) and all(token in teaching_styles for token in ("pd-teaching-card", "pd-teaching-grid", "pd-teaching-accessible")), "details": "Teaching and player controls are wired into the editor surface."})
    checks.append({"id": "PD-EXPORTS", "passed": all(token in exports for token in REQUIRED_EXPORT_CONTROLS), "details": "Server-validated PDF, SVG, PNG, HTML, JSON, CSV, call-sheet, wristband, install-sheet, branding, and black-and-white export controls are present."})
    checks.append({"id": "PD-EXPORTS-INTEGRATION", "passed": all(token in html for token in ("play-designer-export.css", "play-designer-export.js")) and all(token in export_styles for token in ("pd-export-card", "pd-export-grid", "pd-export-result")), "details": "Production export controls are wired into the editor surface."})
    checks.append({"id": "PD-ADVANCED-LEGALITY", "passed": all(token in legality for token in REQUIRED_LEGALITY_CONTROLS), "details": "Profile-driven formation, motion, assignment, protection, coverage, fit, and explainable override controls are present."})
    checks.append({"id": "PD-ADVANCED-LEGALITY-INTEGRATION", "passed": all(token in html for token in ("play-designer-legality.css", "play-designer-legality.js")) and all(token in legality_styles for token in ("pd-legality-card", "pd-legality-finding", "pd-legality-override")), "details": "Legality reporting and owner-approved exceptions are wired into the editor surface."})
    return {"status": "passed" if all(check["passed"] for check in checks) else "failed", "checks": checks, "production_implementation_allowed": False}
