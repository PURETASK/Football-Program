import unittest

from nfl_fidos import resolve_organization_term, validate_organization_terminology


def bundle(status="approved"):
    return {
        "id":"TERM-BUNDLE-ORG-TEAM-2026", "organization_id":"ORG-TEAM", "team_id":"TEAM-A", "season":"2026", "version":"TERM-0.1.0", "owner":"OWNER", "source_refs":["TEAM-SOURCE-1"], "approval_ref":"APPROVAL-1", "status":status,
        "aliases":[{"alias":"Blue Right", "term_id":"TERM-FORMATION-SHOTGUN", "source_refs":["TEAM-SOURCE-1"], "approval_ref":"APPROVAL-1", "status":"locked"}],
    }


class OrganizationTerminologyTests(unittest.TestCase):
    def test_approved_bundle_validates_and_resolves_locked_alias(self):
        result = validate_organization_terminology(bundle())
        self.assertEqual(result["status"], "valid")
        resolved = resolve_organization_term(bundle(), "blue right")
        self.assertEqual(resolved["status"], "resolved_organization_alias")
        self.assertEqual(resolved["term_id"], "TERM-FORMATION-SHOTGUN")

    def test_duplicate_or_unapproved_alias_is_rejected(self):
        invalid = bundle("approved")
        invalid["aliases"].append({"alias":"blue right", "term_id":"TERM-CONCEPT-MESH", "source_refs":[], "approval_ref":"", "status":"review_required"})
        result = validate_organization_terminology(invalid)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("duplicates" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
