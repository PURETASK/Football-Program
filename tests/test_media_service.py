import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_service import MediaCatalogService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class MediaCatalogServiceTests(unittest.TestCase):
    def test_authorized_asset_and_bounded_clip_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "game.mp4"
            media.write_bytes(b"authorized test media")
            service = MediaCatalogService(TenantRepository(JsonRepository(root / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST-1"))
            asset = service.register_asset(file_path=media, asset_id="FILM-MEDIA-001", duration_seconds=120.0, source={"kind":"licensed_film", "ref":"LICENSE-001"}, captured_at="2026-08-23", team_context="TEAM-1", allowed_roots=[root], actor="ANALYST-1")
            self.assertEqual(asset["status"], "registered")
            clip = service.create_clip(clip_id="CLIP-MEDIA-001", asset_id="FILM-MEDIA-001", start_seconds=10.0, end_seconds=20.0, team="TEAM-1", opponent="TEAM-2", situation="third_down", actor="ANALYST-1")
            self.assertEqual(clip["status"], "ready")
            self.assertEqual(len(service.list_clips(opponent="TEAM-2")), 1)

    def test_out_of_range_clip_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "game.mp4"
            media.write_bytes(b"authorized test media")
            service = MediaCatalogService(TenantRepository(JsonRepository(root / "state.json"), organization_id="ORG-MEDIA", actor="ANALYST-1"))
            service.register_asset(file_path=media, asset_id="FILM-MEDIA-002", duration_seconds=10.0, source={"kind":"team_film", "ref":"TEAM-FILM-001"}, captured_at="2026-08-23", team_context="TEAM-1", allowed_roots=[root], actor="ANALYST-1")
            clip = service.create_clip(clip_id="CLIP-MEDIA-002", asset_id="FILM-MEDIA-002", start_seconds=9.0, end_seconds=11.0, team="TEAM-1", opponent="TEAM-2", situation="red_zone", actor="ANALYST-1")
            self.assertEqual(clip["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
