import unittest

from nfl_fidos.visual_playbook import build_visual_play
from nfl_fidos.visual_render import render_visual_svg


def visual():
    return build_visual_play(
        visual_id="VISUAL-RENDER-001", play={"id":"PLAY-RENDER-001", "version":"0.1.0"},
        players=[{"id":"P-QB", "role":"QB", "position":{"x":15,"y":26.5}}, {"id":"P-WR", "role":"X", "position":{"x":10,"y":10}}],
        paths=[{"player_id":"P-WR", "notation":"route", "points":[{"x":10,"y":10},{"x":25,"y":10},{"x":45,"y":18}]}],
        timeline=[{"time_ms":0,"event":"snap"}], role_views=["coach","QB","X"], accessibility=["role labels","text read progression"],
    )


class VisualRenderTests(unittest.TestCase):
    def test_canonical_role_render_is_accessible_svg(self):
        svg = render_visual_svg(visual=visual(), role="QB")
        self.assertIn('role="img"', svg)
        self.assertIn('data-mode="canonical"', svg)
        self.assertIn("QB", svg)

    def test_what_if_render_is_separately_labeled(self):
        svg = render_visual_svg(visual=visual(), role="X", scenario={"type":"add_rotation"})
        self.assertIn('data-mode="what-if"', svg)
        self.assertIn("HUMAN REVIEW REQUIRED", svg)
        self.assertIn("canonical play data is not replaced", svg)


if __name__ == "__main__":
    unittest.main()
