import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_countermeasure, build_scheme


def offense_scheme():
    return {
        "id": "SCHEME-OFF-001", "version": "0.1.0", "unit": "offense", "name": "Example passing structure",
        "components": [
            {"id": "COMP-1", "kind": "personnel", "label": "11 personnel"},
            {"id": "COMP-2", "kind": "formation", "label": "shotgun"},
            {"id": "COMP-3", "kind": "concept", "label": "pass concept"},
        ],
        "assignments": [
            {"role": "QB", "responsibility": "execute progression"},
            {"role": "C", "responsibility": "communicate protection"},
        ],
        "constraints": ["team terminology required"],
        "source": {"kind": "team_playbook", "ref": "PB-001"},
    }


class SchemeTests(unittest.TestCase):
    def test_scheme_is_compositional_and_validated(self):
        result = build_scheme(offense_scheme())
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["issues"], [])

    def test_scheme_rejects_missing_component_kind(self):
        scheme = offense_scheme()
        scheme["components"] = scheme["components"][:2]
        result = build_scheme(scheme)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["issues"][0]["code"], "SCHEME-INCOMPLETE")

    def test_scheme_rejects_duplicate_roles(self):
        scheme = offense_scheme()
        scheme["assignments"].append({"role": "QB", "responsibility": "alternate"})
        result = build_scheme(scheme)
        self.assertTrue(any(issue["code"] == "SCHEME-DUPLICATE-ROLE" for issue in result["issues"]))

    def test_countermeasure_requires_evidence_and_human_review(self):
        counter = build_countermeasure(
            scheme_id="SCHEME-OFF-001", threat="pressure", response="change protection",
            trigger="front declaration", evidence_refs=["EVD-001"],
        )
        self.assertTrue(counter["requires_human_review"])
        self.assertEqual(counter["status"], "draft")


if __name__ == "__main__":
    unittest.main()
