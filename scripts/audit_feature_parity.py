from __future__ import annotations

import json

from nfl_fidos.feature_parity import audit_feature_parity


if __name__ == "__main__":
    report = audit_feature_parity()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "ready_for_human_review" else 1)
