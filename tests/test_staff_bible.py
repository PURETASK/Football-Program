import json
import unittest
from pathlib import Path

from nfl_fidos.staff_bible import validate_staff_bible


class StaffBibleTests(unittest.TestCase):
    def test_staff_roles_pathway_and_review_boundaries(self):
        root = Path(__file__).parents[1]
        bible = json.loads((root / "staff" / "coaching-staff-bible.json").read_text(encoding="utf-8"))
        result = validate_staff_bible(bible)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["role_count"], 8)


if __name__ == "__main__":
    unittest.main()
