import unittest

from nfl_fidos.visual_playbook import build_animation_timeline, build_visual_play, simulate_what_if


class VisualPlaybookTests(unittest.TestCase):
    def visual(self):
        return build_visual_play(
            visual_id="VISUAL-001", play={"id":"PLAY-001", "version":"0.1.0"},
            players=[{"id":"P-QB","role":"QB","position":{"x":0,"y":26.5}},{"id":"P-WR","role":"X","position":{"x":0,"y":10}}],
            paths=[{"player_id":"P-WR","notation":"route","points":[{"x":0,"y":10},{"x":8,"y":10},{"x":20,"y":18}]}],
            timeline=[{"time_ms":0,"event":"snap"},{"time_ms":500,"event":"break"}],
            role_views=["coach","QB","X"], accessibility=["role labels", "text read progression"],
        )

    def test_visual_play_is_renderable(self):
        result = self.visual()
        self.assertEqual(result["status"], "renderable")
        self.assertIn("toggle_overlay", result["interactions"])

    def test_what_if_keeps_canonical_unchanged(self):
        result = simulate_what_if(simulation_id="SIM-001", canonical_visual=self.visual(), adjustment={"type":"rotate_coverage"}, requester_role="coach_staff")
        self.assertEqual(result["status"], "scenario_ready")
        self.assertTrue(result["canonical_unchanged"])
        self.assertTrue(result["human_review_required"])

    def test_animation_requires_ordered_events(self):
        result = build_animation_timeline(timeline_id="TIMELINE-001", events=[{"time_ms":500},{"time_ms":100}])
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["seek_safe"])

    def test_out_of_bounds_visual_is_rejected(self):
        result = self.visual()
        result["players"][0]["position"]["x"] = 121
        from nfl_fidos.visual_playbook import validate_visual_play
        self.assertTrue(validate_visual_play(result))
