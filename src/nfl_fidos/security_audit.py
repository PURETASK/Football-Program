"""Evidence-producing security and operations posture checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .security_controls import configured_rate_limit


REQUIRED_CONTROL_FILES = (
    "control/security-threat-model.json",
    "monitoring/observability-contract.json",
    "src/nfl_fidos/security_controls.py",
    "src/nfl_fidos/tenant_repository.py",
    "src/nfl_fidos/observability.py",
    "src/nfl_fidos/media_retention.py",
    "ui/play-designer-sync.js",
    "src/nfl_fidos/play_design_service.py",
)


def run_security_audit(*, root: str | Path, environ: dict[str, str] | None = None, environment: str = "local") -> dict[str, Any]:
    root_path = Path(root).resolve()
    values = environ or {}
    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in REQUIRED_CONTROL_FILES:
        path = root_path / relative
        exists = path.is_file()
        checks.append({"id": "SEC-FILE-" + relative.replace("/", "-").replace(".", "-"), "status": "pass" if exists else "blocker", "path": str(path), "exists": exists})
        if not exists:
            missing.append(relative)
    threat_model_path = root_path / "control" / "security-threat-model.json"
    threat_model: dict[str, Any] = {}
    threat_issues: list[str] = []
    try:
        threat_model = json.loads(threat_model_path.read_text(encoding="utf-8"))
        threats = threat_model.get("threats", [])
        required_ids = {"TENANT-ISOLATION", "AUTH-BYPASS", "EXPORT-TAMPERING", "OFFLINE-DATA", "AUDIT-LEAK", "AVAILABILITY"}
        seen_ids = {item.get("id") for item in threats if isinstance(item, dict)}
        if not required_ids.issubset(seen_ids):
            threat_issues.append("security threat model is missing one or more required threat classes")
        if threat_model.get("production_implementation_allowed") is not False:
            threat_issues.append("security audit must remain non-activating before Stage 0 owner approval")
    except (OSError, ValueError) as exc:
        threat_issues.append(f"security threat model unavailable: {exc}")
    checks.append({"id": "SEC-THREAT-MODEL", "status": "pass" if not threat_issues else "blocker", "issues": threat_issues, "threat_count": len(threat_model.get("threats", []))})
    try:
        rate_limit = configured_rate_limit(values)
        rate_limit_issue = None
    except ValueError as exc:
        rate_limit = None
        rate_limit_issue = str(exc)
    checks.append({"id": "SEC-RATE-LIMIT", "status": "pass" if rate_limit_issue is None else "blocker", "limit_per_minute": rate_limit, "issue": rate_limit_issue})
    return {
        "status": "ready" if not missing and not threat_issues and rate_limit_issue is None else "blocked",
        "environment": environment,
        "checks": checks,
        "control_families": ["tenant_isolation", "authentication", "rate_limiting", "signed_exports", "encrypted_offline_storage", "redacted_audit", "retention", "monitoring", "recovery"],
        "production_implementation_allowed": False,
        "activation_performed": False,
        "external_state_changed": False,
        "human_approval_required": environment == "production",
    }
