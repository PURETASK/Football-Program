"""Compose an evidence-backed project completion checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evals import run_minimum_eval_suite
from .master_plan_audit import audit_master_plan
from .traceability import validate_traceability_ledger


def _source_paths(repository_root: str | Path) -> tuple[Path, Path]:
    """Resolve the checked-in plan first, with the original upload as a local fallback."""
    root = Path(repository_root)
    repository_markdown = root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md"
    repository_docx = root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.docx"
    if repository_markdown.is_file() and repository_docx.is_file():
        return repository_markdown, repository_docx
    return (Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).md"), Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).docx"))


def run_project_audit(*, root: str | Path, markdown: str | Path | None = None, docx: str | Path | None = None, run_evals: bool = True) -> dict[str, Any]:
    repository_root = Path(root)
    default_markdown, default_docx = _source_paths(repository_root)
    markdown_path = Path(markdown) if markdown else default_markdown
    docx_path = Path(docx) if docx else default_docx
    traceability_path = repository_root / "control" / "requirements-traceability.json"
    plan_audit = audit_master_plan(markdown_path, docx_path, repository_root, traceability_path)
    ledger = json.loads(traceability_path.read_text(encoding="utf-8"))
    traceability = validate_traceability_ledger(ledger, root=repository_root)
    evaluations = run_minimum_eval_suite() if run_evals else {"status":"not_run", "passed":None, "failed":None}
    manifest = json.loads((repository_root / "control" / "manifest.json").read_text(encoding="utf-8"))
    remaining = [{"stage":stage.get("stage"), "items":stage.get("remaining", [])} for stage in ledger.get("stages", []) if stage.get("remaining")]
    external_keywords = ("owner", "approval", "real organization", "provider", "production", "deployment", "pilot", "live", "licensed", "stakeholder", "credential")
    external_blockers = [{"stage":item["stage"], "item":text} for item in remaining for text in item["items"] if any(keyword in text.lower() for keyword in external_keywords)]
    checks = {"master_plan_audit":plan_audit.get("status") == "passed", "traceability":traceability.get("status") == "valid", "evaluations":evaluations.get("status") in {"passed", "not_run"}, "production_disabled":manifest.get("production_implementation_allowed") is False}
    return {"status":"foundation_verified" if all(checks.values()) else "failed", "checks":checks, "master_plan":plan_audit, "traceability":traceability, "evaluations":{"status":evaluations.get("status"), "passed":evaluations.get("passed"), "failed":evaluations.get("failed")}, "control":{"current_stage":manifest.get("current_stage"), "current_work_package":manifest.get("current_work_package"), "production_implementation_allowed":manifest.get("production_implementation_allowed")}, "remaining_stage_count":len(remaining), "remaining":remaining, "external_blockers":external_blockers, "completion_claimed":False}
