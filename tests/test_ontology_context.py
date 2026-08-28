import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import OntologyResolver, TeamContextRegistry


class OntologyContextTests(unittest.TestCase):
    def test_canonical_and_alias_terms_resolve(self):
        resolver = OntologyResolver()
        canonical = resolver.resolve("shotgun")
        alias = resolver.resolve("gun")
        self.assertEqual(canonical["status"], "resolved")
        self.assertEqual(alias["term_id"], canonical["term_id"])
        self.assertFalse(alias["requires_review"])

    def test_unknown_term_is_explicitly_unresolved(self):
        result = OntologyResolver().resolve("unknown team phrase")
        self.assertEqual(result["status"], "unresolved")
        self.assertTrue(result["requires_review"])

    def test_team_alias_can_lock_to_canonical_term(self):
        resolver = OntologyResolver()
        registry = TeamContextRegistry(resolver)
        record = registry.lock_alias(team_id="TEAM-A", alias="Blue Right", term_id="TERM-FORMATION-SHOTGUN", owner="coach-1", reason="team playbook terminology")
        self.assertEqual(record["status"], "locked")
        resolved = registry.resolve(team_id="TEAM-A", value="blue right")
        self.assertEqual(resolved["status"], "resolved_team_alias")
        self.assertEqual(resolved["term_id"], "TERM-FORMATION-SHOTGUN")

    def test_team_alias_conflict_is_rejected(self):
        resolver = OntologyResolver()
        registry = TeamContextRegistry(resolver)
        registry.lock_alias(team_id="TEAM-A", alias="same phrase", term_id="TERM-FORMATION-SHOTGUN", owner="coach-1", reason="first lock")
        with self.assertRaises(ValueError) as raised:
            registry.lock_alias(team_id="TEAM-A", alias="same phrase", term_id="TERM-CONCEPT-FOUR-VERTICALS", owner="coach-2", reason="conflicting lock")
        self.assertEqual(raised.exception.args[0]["code"], "TEAM-ALIAS-CONFLICT")

    def test_ontology_has_no_unexpected_ambiguity(self):
        issues = OntologyResolver().validate()
        self.assertEqual(issues, [])

    def test_controlled_alias_and_relationship_graph_are_available(self):
        resolver = OntologyResolver()
        self.assertEqual(resolver.resolve("glance read")["term_id"], "TERM-RPO-GLANCE")
        related = resolver.related("TERM-CONCEPT-MESH", relationship_type="stresses")
        self.assertEqual(related[0]["term_id"], "TERM-COVERAGE-COVER-1")


if __name__ == "__main__":
    unittest.main()
