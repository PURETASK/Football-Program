import tempfile
import unittest
from pathlib import Path

from nfl_fidos.media_storage import copy_authorized_media


class MediaStorageTests(unittest.TestCase):
    def test_copy_is_atomic_scoped_and_provenance_preserving(self):
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory) / "source"
            storage_root = Path(directory) / "managed"
            source_root.mkdir()
            source = source_root / "game.mp4"
            source.write_bytes(b"media-bytes")
            result = copy_authorized_media(source_path=source, storage_root=storage_root, organization_id="ORG-STORE", asset_id="FILM-STORE-001", allowed_source_roots=[source_root])
            self.assertEqual(result["status"], "stored")
            self.assertTrue(Path(result["destination_path"]).exists())
            self.assertEqual(result["size_bytes"], len(b"media-bytes"))
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(result["retention_action"], "non_destructive_only")
            duplicate = copy_authorized_media(source_path=source, storage_root=storage_root, organization_id="ORG-STORE", asset_id="FILM-STORE-001", allowed_source_roots=[source_root])
            self.assertEqual(duplicate["status"], "rejected")

    def test_source_and_destination_boundaries_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "outside.mp4"
            source.write_bytes(b"media")
            result = copy_authorized_media(source_path=source, storage_root=root / "managed", organization_id="ORG-STORE", asset_id="FILM-STORE-002", allowed_source_roots=[root / "approved"])
            self.assertEqual(result["status"], "rejected")
            self.assertTrue(any("approved source roots" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
