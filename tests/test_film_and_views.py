import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_film_tag, build_playbook_view, build_self_scout_report
from test_play_compiler import valid_play


class FilmAndViewTests(unittest.TestCase):
    def test_film_tag_requires_context_and_provenance(self):
        tag = build_film_tag(
            tag_id="FILM-TAG-001", film_asset_id="FILM-001", tag="pressure",
            team="TEAM-A", opponent="TEAM-B", situation="third_and_medium", source_ref="FILM-001:00:10",
        )
        self.assertEqual(tag["status"], "valid")
        self.assertEqual(tag["source"]["ref"], "FILM-001:00:10")

    def test_self_scout_only_uses_matching_team_tags(self):
        tags = [
            build_film_tag(tag_id="FILM-TAG-002", film_asset_id="FILM-002", tag="motion", team="TEAM-A", opponent="TEAM-B", situation="early_down", source_ref="A"),
            build_film_tag(tag_id="FILM-TAG-003", film_asset_id="FILM-003", tag="motion", team="TEAM-B", opponent="TEAM-A", situation="early_down", source_ref="B"),
        ]
        report = build_self_scout_report(report_id="SELF-SCOUT-001", team="TEAM-A", tags=tags)
        self.assertEqual(report["sample_size"], 1)
        self.assertEqual(report["tag_distribution"], {"motion": 1})

    def test_playbook_view_is_role_specific_and_versioned(self):
        view = build_playbook_view(view_id="VIEW-001", play=valid_play(), role="QB")
        self.assertEqual(view["capability_id"], "CAP-011")
        self.assertEqual(view["source_play_version"], "0.1.0")
        self.assertEqual(view["elements"][2]["value"], "read coverage and execute concept")
        with self.assertRaises(ValueError):
            build_playbook_view(view_id="VIEW-002", play=valid_play(), role="TE")


if __name__ == "__main__":
    unittest.main()
