import unittest
from pathlib import Path
import re


class OperatorUITests(unittest.TestCase):
    def test_dashboard_is_accessible_and_wired_to_control_routes(self):
        path = Path(__file__).parents[1] / "ui" / "operator-dashboard.html"
        document = path.read_text(encoding="utf-8")
        self.assertIn('lang="en"', document)
        self.assertIn("/v1/control", document)
        self.assertIn("/v1/evals", document)
        self.assertIn("/v1/film/search", document)
        self.assertIn("film-search-form", document)
        self.assertIn("/v1/operator/summary", document)
        self.assertIn("Organization population", document)
        self.assertIn("workspace-load", document)
        self.assertIn("/v1/governance/inbox", document)
        self.assertIn("inbox-load", document)
        self.assertIn("/v1/player/today", document)
        self.assertIn("/v1/game-plan/workspace", document)
        self.assertIn("game-plan-form", document)
        self.assertIn("/v1/practice/workspace", document)
        self.assertIn("practice-workspace", document)
        self.assertIn("/v1/schemes/workspace", document)
        self.assertIn("scheme-workspace-form", document)
        self.assertIn("/v1/analytics/workspace", document)
        self.assertIn("analytics-workspace-form", document)
        self.assertIn("/v1/scouting/workspace", document)
        self.assertIn("scouting-workspace-form", document)
        self.assertIn("/v1/playbook/visual", document)
        self.assertIn("visual-playbook-form", document)
        self.assertIn("/v1/workflows/core-play", document)
        self.assertIn("core-play-form", document)
        self.assertIn("core-play-approval-form", document)
        self.assertIn("corePlayFixture", document)
        self.assertIn("PLAY-FAM-UI-001", document)
        self.assertIn("pending-approval", document)
        self.assertIn("/what-if", document)
        self.assertIn("/v1/film/annotation-sessions", document)
        self.assertIn("film-annotation-form", document)
        self.assertIn("/v1/film/playlists", document)
        self.assertIn("film-playlist-form", document)
        self.assertIn("film-annotation-append-form", document)
        self.assertIn("correction_required", document)
        self.assertIn("Canonical timeline playback", document)
        self.assertIn("Play or pause canonical timeline", document)
        self.assertIn("What-if scenario review details", document)
        self.assertIn("human review and approval", document)
        self.assertIn("aria-label", document)
        self.assertIn("media-workspace", document)
        self.assertIn("media-asset-form", document)
        self.assertIn("/v1/media/assets", document)
        self.assertIn("media-job-form", document)
        self.assertIn("/v1/media/jobs", document)
        self.assertIn("pilot-readiness-form", document)
        self.assertIn("/v1/delivery/pilot-readiness", document)
        self.assertIn("/v1/delivery/pilot-organization", document)
        self.assertIn("pilot-organization-form", document)
        self.assertIn("/v1/delivery/pilot-package", document)
        self.assertIn("pilot-delivery-package-form", document)
        self.assertIn("production_implementation_allowed", document)
        self.assertIn("organization-onboarding-form", document)
        self.assertIn("/v1/organizations/context", document)
        self.assertIn("organization-approval-form", document)
        self.assertIn("/v1/organizations/context/approve", document)
        self.assertIn("organization-operating-bundle-form", document)
        self.assertIn("/v1/organizations/operating-bundle", document)
        self.assertIn("organization-operating-bundle-approval-form", document)
        self.assertIn("approved_for_non_production", document)
        self.assertIn('id="scouting-workspace"', document)
        self.assertIn('id="scouting-workspace-form"', document)
        self.assertIn('id="scouting-report-form"', document)
        self.assertIn("/v1/scouting/reports", document)
        self.assertIn('organization-population-readiness-form', document)
        self.assertIn('/v1/organizations/population-readiness', document)
        self.assertIn('never creates synthetic organization data', document)
        self.assertIn('id="agent-runtime"', document)
        self.assertIn('agent-runtime-form', document)
        self.assertIn('/v1/agents/runs', document)
        self.assertIn('local_validation:true', document)

    def test_every_static_dom_binding_has_a_matching_element(self):
        document = (Path(__file__).parents[1] / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        element_ids = set(re.findall(r'id="([^"]+)"', document))
        bindings = set(re.findall(r"getElementById\('([^']+)'\)", document))
        self.assertTrue(bindings)
        self.assertEqual(sorted(bindings - element_ids), [])

    def test_dashboard_smoke_allows_cold_eval_runtime(self):
        smoke = (Path(__file__).parents[1] / "scripts" / "dashboard_smoke.py").read_text(encoding="utf-8")
        self.assertIn("timeout=30", smoke)

    def test_dashboard_has_production_ux_foundations(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        self.assertIn("--navy:", document)
        self.assertIn("@media (max-width:760px)", document)
        self.assertIn("prefers-reduced-motion", document)
        self.assertIn('class="skip-link"', document)
        self.assertIn('id="main-content"', document)
        self.assertIn("button:hover", document)

    def test_comprehensive_tutorial_exists(self):
        tutorial = (Path(__file__).parents[1] / "NFL_FIDOS_TUTORIAL.md").read_text(encoding="utf-8")
        for heading in ("## 1. What this project is", "## 5. The verification loop", "## 7. How the dashboard is organized", "## 13. UX and UI design system", "## 14. How to add a new feature"):
            self.assertIn(heading, tutorial)

    def test_interactive_play_designer_assets_are_integrated(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        designer = (root / "ui" / "play-designer.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer.css").read_text(encoding="utf-8")
        self.assertIn('id="play-designer"', document)
        self.assertIn('href="/play-designer.css"', document)
        self.assertIn('src="/play-designer.js"', document)
        for token in ("Interactive Play Designer", "data-asset", "pd-canvas", "pd-save", "localStorage", "pd-issues"):
            self.assertIn(token, designer)
        self.assertIn(".pd-layout", styles)
        enhancements = (root / "ui" / "play-designer-enhancements.js").read_text(encoding="utf-8")
        enhancement_styles = (root / "ui" / "play-designer-enhancements.css").read_text(encoding="utf-8")
        for token in ("pd-time", "pd-play-animation", "pd-teach-role", "pd-print-artifact", "pd-call-sheet", "pd-wristband", "pd-apply-defense"):
            self.assertIn(token, enhancements)
        self.assertIn("pd-enhancements", enhancement_styles)
        asset_palette = (root / "ui" / "play-designer-assets.js").read_text(encoding="utf-8")
        self.assertIn("NFLFIDOSPlayDesignerAssets", asset_palette)
        self.assertIn("pd-asset-search", asset_palette)
        self.assertIn("pd-asset-category", asset_palette)
        self.assertGreaterEqual(asset_palette.count("['route'"), 10)
        self.assertGreaterEqual(asset_palette.count("['coverage'"), 8)

    def test_play_designer_has_core_asset_vocabulary(self):
        designer = (Path(__file__).parents[1] / "ui" / "play-designer.js").read_text(encoding="utf-8")
        for token in ("route", "motion", "run", "block", "coverage", "rush", "stunt", "undo", "redo", "Export JSON"):
            self.assertIn(token, designer)

    def test_play_designer_has_full_interactive_authoring_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        interactive = (root / "ui" / "play-designer-interactive.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-interactive.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-interactive.css", document)
        self.assertIn("play-designer-interactive.js", document)
        for token in ("pd-duplicate", "pd-copy", "pd-paste", "pd-mirror", "pd-group", "pd-ungroup", "pd-lock", "pd-apply-defense-assignment", "startDraw", "renderHandles", "MutationObserver", "follow_player"):
            self.assertIn(token, interactive)
        for token in (".pd-tool-grid", ".pd-handle", ".pd-draw-preview", ".pd-multi-selected", ".pd-locked"):
            self.assertIn(token, styles)

    def test_play_designer_has_canonical_timeline_animation_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        timeline = (root / "ui" / "play-designer-timeline.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-timeline.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-timeline.css", document)
        self.assertIn("play-designer-timeline.js", document)
        for token in ("pd-time", "pd-play-animation", "pd-timeline-step-forward", "pd-timeline-step-back", "pd-add-marker", "pd-add-narration", "pd-apply-timing", "pd-add-phase", "pd-link-exchange", "pd-save-read-key", "renderAnimation", "speechSynthesis"):
            self.assertIn(token, timeline)
        for token in (".pd-animation-path", ".pd-exchange-line", ".pd-timeline-marker", ".pd-timeline-phase", "prefers-reduced-motion"):
            self.assertIn(token, styles)

    def test_play_designer_has_server_sync_recovery_and_conflict_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        sync = (root / "ui" / "play-designer-sync.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-sync.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-sync.css", document)
        self.assertIn("play-designer-sync.js", document)
        for token in ("pd-sync-card", "pd-sync-load", "pd-sync-save", "pd-sync-recover", "pd-sync-retry", "pd-sync-conflict", "IndexedDB", "expected_revision", "server_design", "addEventListener('online'", "addEventListener('offline'"):
            self.assertIn(token, sync)
        for token in (".pd-sync-card", ".pd-sync-queue", ".pd-sync-conflict", ".pd-sync-online"):
            self.assertIn(token, styles)

    def test_play_designer_has_live_collaboration_and_threaded_review_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        collaboration = (root / "ui" / "play-designer-collaboration.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-collaboration.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-collaboration.css", document)
        self.assertIn("play-designer-collaboration.js", document)
        for token in ("pd-collab-card", "pd-collab-connect", "pd-collab-add-comment", "pd-collab-add-reply", "pd-collab-resolve", "pd-collaboration-cursors", "setInterval", "/presence", "/events", "/events/stream", "streamEvents", "AbortController", "outbox"):
            self.assertIn(token, collaboration)
        for token in (".pd-collab-person", ".pd-collab-thread", ".pd-collab-cursor"):
            self.assertIn(token, styles)

    def test_play_designer_has_immutable_versioning_and_release_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        versioning = (root / "ui" / "play-designer-versioning.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-versioning.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-versioning.css", document)
        self.assertIn("play-designer-versioning.js", document)
        for token in ("pd-versioning-card", "pd-versioning-load", "pd-versioning-diff", "pd-versioning-publish", "pd-versioning-branch", "pd-versioning-merge", "pd-versioning-rollback", "/versions", "/diff", "game_plan_snapshot_id", "expected_revision"):
            self.assertIn(token, versioning)
        for token in (".pd-versioning-card", ".pd-versioning-grid", ".pd-versioning-diff"):
            self.assertIn(token, styles)

    def test_play_designer_has_teaching_player_and_mastery_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        teaching = (root / "ui" / "play-designer-teaching.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-teaching.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-teaching.css", document)
        self.assertIn("play-designer-teaching.js", document)
        for token in ("pd-teaching-card", "pd-teaching-load", "pd-teaching-step", "pd-teaching-accessible", "pd-teaching-quizzes", "pd-teaching-master-current", "/teaching-view", "/mastery", "/quiz", "answer_required", "setVisibilityFilter"):
            self.assertIn(token, teaching)
        for token in (".pd-teaching-card", ".pd-teaching-grid", ".pd-teaching-accessible"):
            self.assertIn(token, styles)

    def test_play_designer_has_production_export_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        exports = (root / "ui" / "play-designer-export.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-export.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-export.css", document)
        self.assertIn("play-designer-export.js", document)
        for token in ("pd-export-card", "pd-export-kind", "pd-export-format", "pd-export-design-ids", "pd-export-black-white", "pd-export-server", "/v1/playbook/designs/export", "content_base64", "sha256", "call_sheet", "wristband", "install_sheet"):
            self.assertIn(token, exports)
        for token in (".pd-export-card", ".pd-export-grid", ".pd-export-result"):
            self.assertIn(token, styles)

    def test_play_designer_has_advanced_legality_and_owner_override_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        legality = (root / "ui" / "play-designer-legality.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "play-designer-legality.css").read_text(encoding="utf-8")
        self.assertIn("play-designer-legality.css", document)
        self.assertIn("play-designer-legality.js", document)
        for token in ("pd-legality-card", "pd-legality-profile", "pd-legality-load", "pd-legality-issue", "/v1/playbook/designs/rule-profiles", "/legality", "coverage_zones", "route_collision_policy", "evidence_refs", "expires_at", "program_owner"):
            self.assertIn(token, legality)
        for token in (".pd-legality-card", ".pd-legality-finding", ".pd-legality-override"):
            self.assertIn(token, styles)

    def test_dashboard_has_moderated_pilot_metrics_surface(self):
        root = Path(__file__).parents[1]
        document = (root / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
        pilot = (root / "ui" / "pilot-verification.js").read_text(encoding="utf-8")
        styles = (root / "ui" / "pilot-verification.css").read_text(encoding="utf-8")
        self.assertIn("pilot-verification.css", document)
        self.assertIn("pilot-verification.js", document)
        for token in ("pd-pilot-metrics-card", "pd-pilot-metrics-load", "/v1/ux/usability-feedback/summary", "pilot_validation_complete"):
            self.assertIn(token, pilot)
        self.assertIn(".pd-pilot-metrics-card", styles)


if __name__ == "__main__":
    unittest.main()
