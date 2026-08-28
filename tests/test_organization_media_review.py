import unittest

from nfl_fidos.organization_media_review import approve_organization_media_review, build_organization_media_review


class OrganizationMediaReviewTests(unittest.TestCase):
    def media(self):
        asset = {"id":"FILM-001","organization_id":"ORG-MEDIA-001","uri":"file:///media/game.mp4","duration_seconds":20,"sha256":"a"*64,"status":"registered"}
        clip = {"id":"CLIP-001","asset_id":"FILM-001","status":"ready"}
        playlist = {"id":"PLAYLIST-001","clip_ids":["CLIP-001"],"status":"draft"}
        observation = {"id":"FILM-OBS-001","clip_id":"CLIP-001","confidence":"high","classification":"observed"}
        return [asset], [clip], [playlist], [observation]

    def test_review_composes_qa_and_owner_validation_stays_non_activating(self):
        assets, clips, playlists, observations = self.media()
        package = build_organization_media_review(package_id="ORG-MEDIA-REVIEW-001", organization_id="ORG-MEDIA-001", season="2026", assets=assets, clips=clips, playlists=playlists, observations=observations, qa_id="QA-001", reviewer="ANALYST-1")
        self.assertEqual(package["status"], "under_review")
        self.assertEqual(package["qa"]["status"], "passed")
        approved = approve_organization_media_review(package=package, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-MEDIA-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])
        self.assertFalse(approved["external_storage_deployed"])

    def test_integrity_and_tenant_mismatch_rejected(self):
        assets, clips, playlists, observations = self.media()
        assets[0]["sha256"] = ""
        assets[0]["organization_id"] = "ORG-OTHER"
        package = build_organization_media_review(package_id="ORG-MEDIA-REVIEW-002", organization_id="ORG-MEDIA-001", season="2026", assets=assets, clips=clips, playlists=playlists, observations=observations, qa_id="QA-002", reviewer="ANALYST-1")
        self.assertEqual(package["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-MEDIA-TENANCY" for issue in package["issues"]))


if __name__ == "__main__":
    unittest.main()
