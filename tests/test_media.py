import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_film_tag, create_film_clip, register_film_asset


class MediaTests(unittest.TestCase):
    def asset(self):
        return register_film_asset(
            asset_id="FILM-100", uri="s3://film/game-1.mp4", duration_seconds=600,
            source={"kind": "licensed_video", "ref": "GAME-1"}, captured_at="2026-08-23", team_context="TEAM-A",
        )

    def test_asset_registration_preserves_source_and_duration(self):
        asset = self.asset()
        self.assertEqual(asset["status"], "registered")
        self.assertEqual(asset["source"]["ref"], "GAME-1")
        self.assertEqual(asset["duration_seconds"], 600)

    def test_clip_range_and_context_are_validated(self):
        clip = create_film_clip(
            clip_id="CLIP-100", asset=self.asset(), start_seconds=10, end_seconds=30,
            team="TEAM-A", opponent="TEAM-B", situation="third_and_medium",
        )
        self.assertEqual(clip["status"], "ready")
        self.assertEqual(clip["source"]["ref"], "FILM-100")

    def test_clip_outside_asset_duration_is_rejected(self):
        clip = create_film_clip(
            clip_id="CLIP-101", asset=self.asset(), start_seconds=590, end_seconds=601,
            team="TEAM-A", opponent="TEAM-B", situation="red_zone",
        )
        self.assertEqual(clip["status"], "rejected")
        self.assertEqual(clip["issues"][0]["code"], "CLIP-RANGE")

    def test_rejected_asset_cannot_be_clipped(self):
        asset = self.asset()
        asset["status"] = "rejected"
        clip = create_film_clip(
            clip_id="CLIP-102", asset=asset, start_seconds=1, end_seconds=2,
            team="TEAM-A", opponent="TEAM-B", situation="early_down",
        )
        self.assertEqual(clip["status"], "rejected")
        self.assertEqual(clip["issues"][0]["code"], "CLIP-ASSET")

    def test_film_tag_can_point_to_time_bounded_clip(self):
        tag = build_film_tag(
            tag_id="FILM-TAG-100", film_asset_id="FILM-100", clip_id="CLIP-100", tag="pressure",
            team="TEAM-A", opponent="TEAM-B", situation="third_and_medium", source_ref="CLIP-100",
        )
        self.assertEqual(tag["status"], "valid")
        self.assertEqual(tag["clip_id"], "CLIP-100")


if __name__ == "__main__":
    unittest.main()
