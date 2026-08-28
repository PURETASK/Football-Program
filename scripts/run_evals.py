"""Run the named minimum NFL FIDOS evaluation suite."""

import json

from nfl_fidos import run_minimum_eval_suite


if __name__ == "__main__":
    result = run_minimum_eval_suite()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
