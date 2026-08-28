"""Non-deploying release-candidate artifact validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .deployment_contract import validate_deployment_contract


REQUIRED_ARTIFACTS = ("Dockerfile", "pyproject.toml", ".github/workflows/ci.yml", "control/manifest.json", "control/eval-manifest.json", "control/master-codex-build-spec.json", "contracts/api-response.schema.json", "contracts/deployment-contract.schema.json", "contracts/play-design-variant.schema.json", "deployment/nfl-fidos-deployment.json", "scripts/validate_control_plane.py", "scripts/run_evals.py")


def validate_release_artifacts(*, root: str | Path, eval_result: dict[str, Any] | None = None) -> dict[str, Any]:
    repository_root = Path(root).resolve()
    missing = [path for path in REQUIRED_ARTIFACTS if not (repository_root / path).is_file()]
    issues: list[str] = [f"missing required release artifact: {path}" for path in missing]
    manifest: dict[str, Any] = {}
    try:
        manifest = json.loads((repository_root / "control" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        issues.append(f"control manifest unreadable: {exc}")
    eval_passed = (eval_result or {}).get("status") == "passed"
    if eval_result is not None and not eval_passed:
        issues.append("current evaluation suite is not passing")
    deployment = validate_deployment_contract(path=repository_root / "deployment" / "nfl-fidos-deployment.json")
    if deployment["status"] != "valid":
        issues.extend(f"deployment contract: {issue}" for issue in deployment["issues"])
    approval_blocker = None if manifest.get("production_implementation_allowed") else "Stage 0 owner approval is required before production release"
    return {"status":"blocked" if issues or approval_blocker else "ready", "artifact_status":"complete" if not issues else "incomplete", "root":str(repository_root), "required_artifact_count":len(REQUIRED_ARTIFACTS), "missing_artifacts":missing, "deployment_status":deployment["status"], "eval_status":(eval_result or {}).get("status", "not_run"), "stage":manifest.get("current_stage"), "production_implementation_allowed":manifest.get("production_implementation_allowed"), "approval_blocker":approval_blocker, "issues":issues, "deploy_performed":False, "human_approval_required":bool(approval_blocker)}
