"""Compose deployment, release, operations, and control evidence safely."""

from __future__ import annotations

from typing import Any


def compose_deployment_release_preflight(*, release_validation: dict[str, Any], deployment_preflight: dict[str, Any], operational_readiness: dict[str, Any], eval_result: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if release_validation.get("artifact_status") != "complete":
        blockers.append("release_artifacts")
    if release_validation.get("deployment_status") != "valid":
        blockers.append("deployment_contract")
    if deployment_preflight.get("status") != "ready":
        blockers.append("deployment_preflight")
    if operational_readiness.get("status") != "ready":
        blockers.append("operational_readiness")
    if eval_result.get("status") != "passed":
        blockers.append("evaluation_suite")
    if release_validation.get("production_implementation_allowed") is not False:
        blockers.append("production_safety_boundary")
    return {
        "status": "ready_for_validation" if not blockers else "blocked",
        "environment": deployment_preflight.get("environment"),
        "release_validation": release_validation,
        "deployment_preflight": deployment_preflight,
        "operational_readiness": operational_readiness,
        "eval_result": eval_result,
        "blockers": blockers,
        "activation_performed": False,
        "production_implementation_allowed": False,
        "external_state_changed": False,
        "human_approval_required": True,
    }
