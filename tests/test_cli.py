import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos.cli import main


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = main(list(args))
        return status, json.loads(output.getvalue())

    def test_validate_returns_program_state(self):
        status, result = self.run_cli("validate")
        self.assertEqual(status, 0)
        self.assertEqual(result["scope"], "NFL only")
        self.assertEqual(result["current_work_package"], "STAGE-0A")

    def test_resolve_returns_canonical_term(self):
        status, result = self.run_cli("resolve", "gun")
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["term_id"], "TERM-FORMATION-SHOTGUN")

    def test_evals_returns_passing_suite(self):
        status, result = self.run_cli("evals")
        self.assertEqual(status, 0)
        self.assertEqual(result["status"], "passed")


if __name__ == "__main__":
    unittest.main()
