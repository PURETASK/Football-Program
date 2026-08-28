"""Auditable application facade for the first Football OS workflows."""

from __future__ import annotations

from typing import Any

from .agent_contracts import create_handoff
from .drill_library import validate_drill
from .analytics_dictionary import build_analytics_report
from .film_intelligence import build_film_playlist, validate_film_qa
from .delivery import build_release_candidate, evaluate_delivery_wave
from .governance_audit import run_governance_audit
from .play_compiler import compile_play
from .player_learning import build_player_lesson
from .playbook_architecture import approve_play, build_extended_play, request_play_approval, validate_play_spec
from .playbook_view import build_playbook_view
from .rules_knowledge import build_rule_aware_recommendation
from .repository import JsonRepository


class FootballIntelligenceService:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    @staticmethod
    def _tenant(record: dict[str, Any], organization_id: str | None) -> dict[str, Any]:
        output = dict(record)
        if organization_id:
            output["organization_id"] = organization_id
        return output

    def publish_play(self, play: dict[str, Any], *, actor: str) -> dict[str, Any]:
        result = compile_play(play)
        if not result.valid:
            self.repository.put(
                "compile_rejections", play.get("id", "UNKNOWN"),
                {"play": play, "issues": [issue.__dict__ for issue in result.issues]},
                actor=actor, reason="play_compiler_rejection",
            )
            raise ValueError({"code": "SERVICE-PLAY-REJECTED", "issues": [issue.__dict__ for issue in result.issues]})
        return self.repository.put("plays", play["id"], result.normalized_play, actor=actor, reason="validated_play_publish")

    def create_lesson(self, *, play_id: str, learner_role: str, actor: str) -> dict[str, Any]:
        play = self.repository.get("plays", play_id)
        if play is None:
            raise KeyError(f"Unknown play: {play_id}")
        lesson = build_player_lesson(play, learner_role)
        return self.repository.put("lessons", lesson["id"], lesson, actor=actor, reason="player_lesson_created")

    def create_handoff(self, *, handoff_id: str, from_agent: str, to_agent: str, workflow_id: str, payload: dict[str, Any], actor: str, requested_permissions: set[str] | None = None, human_review_required: bool = False) -> dict[str, Any]:
        handoff = create_handoff(
            handoff_id=handoff_id, from_agent=from_agent, to_agent=to_agent,
            workflow_id=workflow_id, payload=payload,
            requested_permissions=requested_permissions,
            human_review_required=human_review_required,
        )
        return self.repository.put("handoffs", handoff_id, handoff, actor=actor, reason="agent_handoff_created")

    def create_core_play_slice(
        self, *, play: dict[str, Any], role: str, drill: dict[str, Any], actor: str, decision_ref: str, organization_id: str | None = None
    ) -> dict[str, Any]:
        """Create the Wave 1 play-to-teaching-to-practice review package.

        This package remains pending until a human approval is recorded. Each
        derived artifact is persisted independently so revisions and audit
        history remain inspectable across repository implementations.
        """
        spec_issues = validate_play_spec(play)
        drill_issues = validate_drill(drill)
        if spec_issues or drill_issues:
            rejection = {
                "play_id": play.get("id", "UNKNOWN"),
                "spec_issues": spec_issues,
                "drill_issues": drill_issues,
            }
            self.repository.put("slice_rejections", rejection["play_id"], rejection, actor=actor, reason="core_slice_validation_rejection")
            raise ValueError({"code": "SERVICE-CORE-SLICE-REJECTED", **rejection})
        play = self._tenant(play, organization_id)
        drill = self._tenant(drill, organization_id)
        pending = request_play_approval(play, requester=actor, decision_ref=decision_ref)
        view = build_playbook_view(view_id=f"VIEW-{play['id']}-{role}", play=pending, role=role)
        self.repository.put("play_drafts", play["id"], pending, actor=actor, reason="core_slice_review_created")
        self.repository.put("play_views", view["id"], view, actor=actor, reason="core_slice_role_view_created")
        self.repository.put("drills", drill["id"], drill, actor=actor, reason="core_slice_drill_linked")
        package = {
            "id": f"SLICE-{play['id']}",
            "play_id": play["id"],
            "play_view_id": view["id"],
            "drill_id": drill["id"],
            "role": role,
            "decision_ref": decision_ref,
            "approval_state": pending["approval"]["state"],
            "status": "pending_approval",
        }
        package = self._tenant(package, organization_id)
        return self.repository.put("core_play_slices", package["id"], package, actor=actor, reason="core_slice_package_created")

    def approve_core_play_slice(self, *, play_id: str, approver: str, decision_ref: str, organization_id: str | None = None) -> dict[str, Any]:
        draft = self.repository.get("play_drafts", play_id)
        if draft is None:
            raise KeyError(f"Unknown play draft: {play_id}")
        approved = approve_play(draft, approver=approver, decision_ref=decision_ref)
        self.repository.put("play_drafts", play_id, approved, actor=approver, reason="core_slice_approval_decision")
        package_id = f"SLICE-{play_id}"
        package = self.repository.get("core_play_slices", package_id)
        if package is None:
            raise KeyError(f"Unknown core play slice: {package_id}")
        if approved["approval"]["state"] != "approved":
            package.update({"approval_state": approved["approval"]["state"], "status": "rejected"})
            return self.repository.put("core_play_slices", package_id, package, actor=approver, reason="core_slice_rejected")
        self.repository.put("plays", play_id, approved, actor=approver, reason="core_slice_approved_and_published")
        package.update({"approval_state": "approved", "status": "approved"})
        package = self._tenant(package, organization_id)
        return self.repository.put("core_play_slices", package_id, package, actor=approver, reason="core_slice_approval_recorded")

    def create_evidence_intelligence_slice(
        self, *, asset: dict[str, Any], clip: dict[str, Any], observation: dict[str, Any],
        scouting_report: dict[str, Any], metric_observation: dict[str, Any],
        analyst: str, qa_reviewer: str, organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist a source-linked film, scouting, and analytics review package."""
        qa = validate_film_qa(
            qa_id=f"QA-{observation.get('id', 'UNKNOWN')}",
            clips=[clip], observations=[observation], reviewer=qa_reviewer,
        )
        analytics = build_analytics_report(
            report_id=f"ANALYTICS-REPORT-{metric_observation.get('id', 'UNKNOWN')}",
            audience="coach_staff", metric_observations=[metric_observation],
            context=observation.get("context", {}),
            caveats=["Available sample only; opponent adaptation remains possible."], analyst=analyst,
        )
        issues: list[Any] = []
        if asset.get("status") not in {"registered", "ready"}:
            issues.append({"code": "EVIDENCE-ASSET", "message": "Film asset must be registered", "path": "asset.status"})
        if clip.get("status") != "ready":
            issues.append({"code": "EVIDENCE-CLIP", "message": "Film clip must be ready", "path": "clip.status"})
        if observation.get("status") != "ready_for_review":
            issues.append({"code": "EVIDENCE-OBSERVATION", "message": "Observation must be ready for review", "path": "observation.status"})
        if scouting_report.get("status") != "under_review":
            issues.append({"code": "EVIDENCE-SCOUTING", "message": "Scouting report must remain under review", "path": "scouting_report.status"})
        if metric_observation.get("status") != "valid":
            issues.append({"code": "EVIDENCE-METRIC", "message": "Metric observation must be valid", "path": "metric_observation.status"})
        if qa.get("status") != "passed":
            issues.append({"code": "EVIDENCE-QA", "message": "Film QA must pass before package creation", "path": "qa.status"})
        if analytics.get("status") != "draft":
            issues.append({"code": "EVIDENCE-ANALYTICS", "message": "Analytics report must be valid", "path": "analytics.status"})
        package_id = f"EVIDENCE-SLICE-{observation.get('id', 'UNKNOWN')}"
        if issues:
            rejection = {"id": package_id, "issues": issues, "asset_id": asset.get("id"), "observation_id": observation.get("id")}
            self.repository.put("evidence_slice_rejections", package_id, rejection, actor=analyst, reason="evidence_slice_validation_rejection")
            raise ValueError({"code": "SERVICE-EVIDENCE-SLICE-REJECTED", **rejection})
        for collection, record in (("film_assets", asset), ("film_clips", clip), ("film_observations", observation), ("scouting_reports", scouting_report), ("metric_observations", metric_observation), ("film_qa", qa), ("analytics_reports", analytics)):
            record = self._tenant(record, organization_id)
            self.repository.put(collection, record["id"], record, actor=analyst, reason="evidence_slice_artifact_created")
        package = {
            "id": package_id, "asset_id": asset["id"], "clip_id": clip["id"],
            "observation_id": observation["id"], "scouting_report_id": scouting_report["id"],
            "metric_observation_id": metric_observation["id"], "qa_id": qa["id"],
            "analytics_report_id": analytics["id"], "status": "under_review",
            "human_review_required": True,
        }
        package = self._tenant(package, organization_id)
        return self.repository.put("evidence_intelligence_slices", package_id, package, actor=analyst, reason="evidence_slice_package_created")

    def create_weekly_delivery_package(
        self, *, game_plan: dict[str, Any], rule_recommendation: dict[str, Any], eval_result: dict[str, Any],
        capability_ids: list[str], feature_gates: list[dict[str, Any]], actor: str,
        human_approval: str | None = None, organization_id: str | None = None,
    ) -> dict[str, Any]:
        """Assemble the weekly plan through governance and release readiness gates."""
        if game_plan.get("status") != "under_review":
            raise ValueError({"code": "SERVICE-WEEKLY-PLAN", "message": "Game plan must be valid and under review"})
        if rule_recommendation.get("status") != "under_review":
            raise ValueError({"code": "SERVICE-RULE-RECOMMENDATION", "message": "Rule recommendation must be authoritative and under review"})
        audit = run_governance_audit(
            audit_id=f"AUDIT-{game_plan['id']}", eval_result=eval_result,
            critical_failures=[], safety_failures=[], permission_failures=[],
            audit_event_id=f"EVENT-GOV-{game_plan['id']}",
            observability_evidence=[f"TRACE-{game_plan['id']}", f"EVAL-{game_plan['id']}"],
            human_approval=human_approval,
        )
        wave = evaluate_delivery_wave(
            wave_id=f"WAVE-{game_plan['id']}", number=3, outcome="weekly game-plan review",
            capability_ids=capability_ids, feature_gates=feature_gates, eval_result=eval_result,
        )
        release = build_release_candidate(
            release_id=f"RC-{game_plan['id']}", wave=wave,
            feature_gate_ids=[gate.get("id") for gate in feature_gates],
            eval_result=eval_result, approver=human_approval,
        )
        for collection, record in (("game_plans", game_plan), ("rule_recommendations", rule_recommendation), ("governance_audits", audit), ("delivery_waves", wave), ("release_candidates", release)):
            record = self._tenant(record, organization_id)
            self.repository.put(collection, record["id"], record, actor=actor, reason="weekly_delivery_package_created")
        package = {
            "id": f"WEEKLY-DELIVERY-{game_plan['id']}", "game_plan_id": game_plan["id"],
            "rule_recommendation_id": rule_recommendation["id"], "audit_id": audit["id"],
            "wave_id": wave["id"], "release_id": release["id"],
            "status": "approved" if release["status"] == "approved" else "blocked",
            "human_approval_required": True, "blockers": release["blockers"] + audit["issues"],
        }
        package = self._tenant(package, organization_id)
        return self.repository.put("weekly_delivery_packages", package["id"], package, actor=actor, reason="weekly_delivery_package_recorded")
