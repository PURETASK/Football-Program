"""Validate machine-readable local browser-validation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_CHECK_TERMS = ("Dashboard loaded", "Stage 0 gate", "Program status", "Organization population readiness", "Controlled agent runtime", "console error")


def validate_browser_evidence(*, evidence_path: str | Path) -> dict[str, Any]:
    path = Path(evidence_path)
    issues: list[str] = []
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status":"invalid", "path":str(path), "issues":[str(exc)]}
    if evidence.get("stage") != "STAGE-22":
        issues.append("browser evidence must be assigned to STAGE-22")
    if evidence.get("status") != "passed":
        issues.append("browser evidence status must be passed")
    if not evidence.get("url", "").startswith("http://127.0.0.1:"):
        issues.append("evidence URL must identify a local reference service")
    checks = evidence.get("checks", [])
    if not isinstance(checks, list) or not checks:
        issues.append("browser evidence must contain checks")
    else:
        check_text = " ".join(str(item) for item in checks)
        for term in REQUIRED_CHECK_TERMS:
            if term.lower() not in check_text.lower():
                issues.append(f"browser evidence is missing check term: {term}")
    if evidence.get("external_state_changed") is not False:
        issues.append("browser evidence must prove external_state_changed=false")
    if evidence.get("production_implementation_allowed") is not False:
        issues.append("browser evidence must prove production implementation is disabled")
    limitations = " ".join(str(item) for item in evidence.get("limitations", []))
    if "pilot" not in limitations.lower() or "deployment" not in limitations.lower():
        issues.append("browser evidence must preserve deployment and pilot limitations")
    return {"status":"valid" if not issues else "invalid", "path":str(path), "stage":evidence.get("stage"), "check_count":len(checks) if isinstance(checks, list) else 0, "issues":issues, "external_state_changed":evidence.get("external_state_changed"), "production_implementation_allowed":evidence.get("production_implementation_allowed")}
