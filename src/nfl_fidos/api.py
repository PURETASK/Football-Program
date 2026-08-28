"""Pure JSON API router for UI and integration adapters."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .evals import run_minimum_eval_suite
from .auth import authorize_principal, verify_token
from .ontology import OntologyResolver
from .team_ontology import TeamOntologyService
from .play_compiler import compile_play
from .repository import JsonRepository
from .service import FootballIntelligenceService
from .film_room_service import FilmRoomService
from .tenant_repository import TenantRepository
from .media_service import MediaCatalogService
from .media_jobs import MediaProcessingJobService
from .source_connectors import SourceConnectorService
from .source_scheduler import SourceRefreshScheduler
from .operator_summary import build_operator_summary
from .approval_inbox import build_approval_inbox
from .governance_reviews import review_inbox_item
from .operations_inbox import build_operations_inbox, mark_notifications_read
from .roster_workspace import build_roster_workspace, create_roster_player, save_depth_chart, save_personnel_package
from .player_workspace import PlayerWorkspaceService
from .game_plan_workspace import build_game_plan_workspace
from .game_plan_collaboration import GamePlanCollaborationService
from .release_room import build_release_room, create_release_snapshot, approve_release_snapshot, rollback_release_snapshot
from .delivery_workspace import build_delivery_workspace, create_delivery_packet, create_delivery_task, complete_delivery_task
from .collaboration_workspace import CollaborationWorkspaceService
from .analytics_integration import calculate_provider_batch
from .media_worker_runner import MediaWorkerRunner
from .practice_workspace import PracticeWorkspaceService
from .practice_attendance import PracticeAttendanceService
from .resource_integration import plan_resource_integration
from .performance_integration import ingest_provider_batch
from .playbook_workspace import PlaybookWorkspaceService
from .play_design_service import PlayDesignService
from .play_design_collaboration import PlayDesignCollaborationService
from .play_legality import RULE_PROFILE_CATALOG
from .scheme_workspace import SchemeWorkspaceService
from .analytics_workspace import AnalyticsWorkspaceService
from .analytics_outcomes import AnalyticsOutcomeService
from .scouting_workspace import ScoutingWorkspaceService
from .scouting_intelligence import build_situational_scouting_report
from .visual_workspace import VisualWorkspaceService
from .media_retention import plan_media_retention
from .media_retention_scheduler import MediaRetentionScheduler
from .media_retention_executor import execute_media_retention
from .config import resolve_auth_secret
from .knowledge_search import KnowledgeRetrievalService
from .media_transform_orchestrator import MediaTransformOrchestrator
from .pilot_readiness import evaluate_pilot_readiness
from .organization_onboarding import approve_onboarding_package, build_onboarding_package
from .stage0 import evaluate_stage0_exit
from .stage0_approval import build_stage0_owner_approval, validate_stage0_owner_approval
from .pilot_selection import build_pilot_selection
from .pilot_delivery import build_pilot_delivery_package
from .master_spec_acceptance import build_stage25_spec_acceptance, load_master_spec, validate_stage25_spec_acceptance
from .master_spec import validate_master_spec
from .usability_feedback import build_usability_feedback, validate_usability_feedback
from .pilot_verification import summarize_pilot_feedback
from .organization_drill_validation import approve_organization_drill_validation, build_organization_drill_validation
from .organization_play_corpus import approve_organization_play_corpus, build_organization_play_corpus
from .organization_doctrine import approve_organization_doctrine, build_organization_doctrine
from .organization_staff_review import approve_organization_staff_package, build_organization_staff_package
from .organization_player_development import approve_organization_player_development, build_organization_player_development
from .organization_scouting import approve_organization_scouting_package, build_organization_scouting_package
from .organization_analytics import approve_organization_analytics_package, build_organization_analytics_package
from .organization_game_plan import approve_organization_game_plan, build_organization_game_plan
from .organization_special_teams import approve_organization_special_teams, build_organization_special_teams
from .organization_performance import approve_organization_performance, build_organization_performance
from .organization_media_review import approve_organization_media_review, build_organization_media_review
from .organization_operating_bundle import approve_organization_operating_bundle, build_organization_operating_bundle, load_persisted_organization_components
from .provider_adapter_registration import approve_provider_adapter_registration, build_provider_adapter_registration
from .organization_media_review import approve_organization_media_review, build_organization_media_review
from .source_authorization import validate_source_authorization
from .organization_population_readiness import build_organization_population_readiness
from .agent_runtime import AgentRuntime, load_agent_bible
from .local_agent_adapters import register_local_validation_adapters


def _response(status: str, data: Any, error: str | None = None) -> dict[str, Any]:
    return {"status": status, "data": data, "error": error}


def _authenticated(headers: dict[str, str] | None, *, action: str, organization_id: str) -> tuple[Any | None, tuple[int, dict[str, Any]] | None]:
    authorization = (headers or {}).get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None, (401, _response("error", None, "Bearer authentication is required"))
    try:
        secret = resolve_auth_secret()
    except ValueError:
        secret = ""
    if not secret:
        return None, (503, _response("error", None, "Authentication secret is not configured"))
    try:
        principal = verify_token(authorization.removeprefix("Bearer ").strip(), secret=secret)
    except ValueError:
        return None, (401, _response("error", None, "Invalid or expired authentication token"))
    decision = authorize_principal(principal=principal, action=action, organization_id=organization_id)
    if not decision["allowed"]:
        return None, (403, _response("error", decision, "Permission or organization scope denied"))
    return principal, None


def _film_service(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> FilmRoomService:
    return FilmRoomService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _media_service(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> MediaCatalogService:
    return MediaCatalogService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _media_jobs(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> MediaProcessingJobService:
    return MediaProcessingJobService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _sources(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> SourceConnectorService:
    return SourceConnectorService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _player_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PlayerWorkspaceService:
    return PlayerWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _practice_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PracticeWorkspaceService:
    return PracticeWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _practice_attendance(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PracticeAttendanceService:
    return PracticeAttendanceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _scheme_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> SchemeWorkspaceService:
    return SchemeWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _analytics_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> AnalyticsWorkspaceService:
    return AnalyticsWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _analytics_outcomes(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> AnalyticsOutcomeService:
    return AnalyticsOutcomeService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _scouting_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> ScoutingWorkspaceService:
    return ScoutingWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _visual_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> VisualWorkspaceService:
    return VisualWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _playbook_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PlaybookWorkspaceService:
    return PlaybookWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _play_designs(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PlayDesignService:
    return PlayDesignService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _play_design_collaboration(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> PlayDesignCollaborationService:
    return PlayDesignCollaborationService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _game_plan_collaboration(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> GamePlanCollaborationService:
    return GamePlanCollaborationService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def _collaboration_workspace(service: FootballIntelligenceService, *, organization_id: str, actor: str) -> CollaborationWorkspaceService:
    return CollaborationWorkspaceService(TenantRepository(service.repository, organization_id=organization_id, actor=actor))


def handle_request(*, method: str, path: str, body: dict[str, Any] | None = None, service: FootballIntelligenceService | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    """Handle a request without network or framework dependencies."""
    body = body or {}
    parsed = urlparse(path)
    query = parse_qs(parsed.query)
    # Structured play designs use a separate route from the legacy minimum play record.
    extra_post_routes = {"/v1/playbook/designs", "/v1/playbook/designs/validate", "/v1/playbook/designs/templates", "/v1/playbook/designs/variants", "/v1/playbook/designs/request-review", "/v1/playbook/designs/publish", "/v1/playbook/designs/branch", "/v1/playbook/designs/versioning/merge", "/v1/playbook/designs/versioning/rollback", "/v1/playbook/designs/mastery", "/v1/playbook/designs/quiz", "/v1/playbook/designs/export/preflight", "/v1/playbook/designs/export", "/v1/playbook/designs/legality/override", "/v1/playbook/designs/legality/override/approve", "/v1/playbook/designs/comments", "/v1/playbook/designs/comments/reply", "/v1/playbook/designs/comments/resolve", "/v1/playbook/designs/presence", "/v1/playbook/designs/presence/leave", "/v1/playbook/designs/assets/lifecycle", "/v1/playbook/designs/assets/migrate"}
    post_routes = {"/v1/plays/compile", "/v1/workflows/core-play", "/v1/workflows/evidence-intelligence", "/v1/workflows/weekly-delivery", "/v1/film/observations", "/v1/film/quizzes", "/v1/film/playlists", "/v1/media/assets", "/v1/media/clips", "/v1/media/jobs", "/v1/media/retention-scan", "/v1/media/retention-execute", "/v1/media/transform-batch", "/v1/media/worker/run", "/v1/sources", "/v1/sources/authorized", "/v1/player/assignments", "/v1/practice/plans", "/v1/practice/drill-validation", "/v1/practice/drill-validation/approve", "/v1/practice/resources/preflight", "/v1/performance/batches", "/v1/performance/organization-package", "/v1/performance/organization-package/approve", "/v1/playbook/drafts", "/v1/playbook/drafts/request-approval", "/v1/playbook/drafts/approve", "/v1/playbook/organization-corpus", "/v1/playbook/organization-corpus/approve", "/v1/game-plan/threads", "/v1/game-plan/threads/comments", "/v1/game-plan/threads/resolve", "/v1/game-plan/organization-package", "/v1/game-plan/organization-package/approve", "/v1/schemes", "/v1/schemes/organization-doctrine", "/v1/schemes/organization-doctrine/approve", "/v1/staff/organization-review", "/v1/staff/organization-review/approve", "/v1/player-development/organization-package", "/v1/player-development/organization-package/approve", "/v1/analytics/batches", "/v1/analytics/reports", "/v1/analytics/organization-package", "/v1/analytics/organization-package/approve", "/v1/scouting/reports", "/v1/scouting/organization-package", "/v1/scouting/organization-package/approve", "/v1/special-teams/organization-package", "/v1/special-teams/organization-package/approve", "/v1/media/organization-review", "/v1/media/organization-review/approve", "/v1/integrations/provider-adapter", "/v1/integrations/provider-adapter/approve", "/v1/playbook/visuals", "/v1/film/annotation-sessions", "/v1/ontology/team-aliases", "/v1/delivery/pilot-readiness", "/v1/delivery/pilot-organization", "/v1/delivery/pilot-package", "/v1/organizations/context", "/v1/organizations/context/approve", "/v1/organizations/operating-bundle", "/v1/organizations/operating-bundle/approve", "/v1/control/stage-0-approval", "/v1/control/stage-25-acceptance", "/v1/governance/inbox/review", "/v1/ux/usability-feedback", "/v1/agents/runs"}
    post_routes.add("/v1/operations/inbox/notifications/read")
    post_routes.add("/v1/film/voice-notes")
    post_routes.add("/v1/practice/attendance")
    post_routes.add("/v1/analytics/outcomes")
    post_routes.update({"/v1/roster/players", "/v1/roster/depth-charts", "/v1/roster/personnel-packages", "/v1/game-plan/release-room/snapshots", "/v1/game-plan/release-room/approve", "/v1/game-plan/release-room/rollback", "/v1/delivery/tasks", "/v1/delivery/tasks/complete", "/v1/delivery/packets", "/v1/collaboration/threads", "/v1/collaboration/comments", "/v1/collaboration/threads/resolve", "/v1/collaboration/threads/assign", "/v1/collaboration/notifications/read", "/v1/collaboration/presence", "/v1/collaboration/presence/leave"})
    if method.upper() != "GET" and parsed.path not in post_routes and parsed.path not in extra_post_routes and not parsed.path.startswith("/v1/workflows/core-play/") and not parsed.path.startswith("/v1/film/quizzes/") and not parsed.path.startswith("/v1/media/jobs/") and not parsed.path.startswith("/v1/sources/") and not (parsed.path.startswith("/v1/playbook/visuals/") and parsed.path.endswith("/what-if")) and not (parsed.path.startswith("/v1/film/annotation-sessions/") and parsed.path.endswith("/annotations")):
        return 405, _response("error", None, "Only GET is supported except declared POST workflow, compiler, and film-room routes")
    if parsed.path in {"/v1/playbook/designs/assets", "/v1/playbook/designs/templates", "/v1/playbook/designs/templates/lineage-impact", "/v1/playbook/designs/rule-profiles"} and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        registry = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject)
        if parsed.path.endswith("/rule-profiles"):
            return 200, _response("ok", {"profiles": [{"id": profile_id, **profile} for profile_id, profile in RULE_PROFILE_CATALOG.items()]})
        if parsed.path.endswith("/lineage-impact"):
            template_id = query.get("template_id", [""])[0]
            if not template_id:
                return 400, _response("error", None, "template_id query parameter is required")
            try:
                return 200, _response("ok", registry.template_lineage_impact(template_id))
            except KeyError as exc:
                return 404, _response("error", None, str(exc))
        if parsed.path.endswith("/assets"):
            return 200, _response("ok", {"assets": registry.assets(unit=query.get("unit", [None])[0], kind=query.get("kind", [None])[0], category=query.get("category", [None])[0], query=query.get("q", [None])[0], status=query.get("status", [None])[0], formation=query.get("formation", [None])[0], context_formation=query.get("context_formation", [None])[0], personnel=query.get("personnel", [None])[0], rule_profile=query.get("rule_profile", [None])[0])})
        return 200, _response("ok", {"templates": registry.templates(unit=query.get("unit", [None])[0])})
    if parsed.path == "/v1/playbook/designs/templates" and method.upper() == "POST":
        required = ("organization_id", "design_id", "name")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        if body.get("tags") is not None and not isinstance(body.get("tags"), list):
            return 400, _response("error", None, "tags must be a list")
        if body.get("element_ids") is not None and (not isinstance(body.get("element_ids"), list) or not all(isinstance(item, str) for item in body["element_ids"])):
            return 400, _response("error", None, "element_ids must be a list of strings")
        if body.get("parent_template_id") is not None and not isinstance(body.get("parent_template_id"), str):
            return 400, _response("error", None, "parent_template_id must be a string")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            template = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).create_template(
                body["design_id"],
                name=body["name"],
                actor=principal.subject,
                description=body.get("description", ""),
                tags=body.get("tags", []),
                template_kind=body.get("template_kind", "custom"),
                layer=body.get("layer", "complete_call"),
                element_ids=body.get("element_ids"),
                parent_template_id=body.get("parent_template_id"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", template)
    if parsed.path == "/v1/playbook/designs/variants" and method.upper() == "POST":
        required = ("organization_id", "design_id", "variants")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        if not isinstance(body.get("variants"), list):
            return 400, _response("error", None, "variants must be a list")
        if body.get("batch_id") is not None and not isinstance(body.get("batch_id"), str):
            return 400, _response("error", None, "batch_id must be a string")
        for index, variant in enumerate(body["variants"], start=1):
            if not isinstance(variant, dict):
                return 400, _response("error", None, f"variant {index} must be an object")
            if "label" in variant and not isinstance(variant["label"], str):
                return 400, _response("error", None, f"variant {index} label must be a string")
            look_patch = variant.get("patch", variant.get("look", {}))
            if not isinstance(look_patch, dict):
                return 400, _response("error", None, f"variant {index} patch must be an object")
            assignment_patches = variant.get("assignment_patches", [])
            if assignment_patches is not None and not isinstance(assignment_patches, list):
                return 400, _response("error", None, f"variant {index} assignment_patches must be a list")
            for patch_index, assignment_patch in enumerate(assignment_patches or [], start=1):
                if not isinstance(assignment_patch, dict):
                    return 400, _response("error", None, f"variant {index} assignment patch {patch_index} must be an object")
                if "element_id" in assignment_patch and not isinstance(assignment_patch["element_id"], str):
                    return 400, _response("error", None, f"variant {index} assignment patch {patch_index} element_id must be a string")
                if "patch" in assignment_patch and not isinstance(assignment_patch["patch"], dict):
                    return 400, _response("error", None, f"variant {index} assignment patch {patch_index} patch must be an object")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            report = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).create_batch_variants(body["design_id"], variants=body["variants"], actor=principal.subject, batch_id=body.get("batch_id"))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", report)
    if parsed.path == "/v1/playbook/designs" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).workspace(include_invalid=query.get("include_invalid", ["true"])[0].lower() == "true"))
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/presence") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            presence = _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).active_presence(design_id=design_id)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", {"design_id": design_id, "presence": presence})
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/events") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        try:
            since = int(query.get("since", ["0"])[0])
        except ValueError:
            return 400, _response("error", None, "since must be an integer")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            events = _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).events(design_id=design_id, since_sequence=since)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", {"design_id": design_id, "events": events, "next_sequence": max((int(event.get("sequence", 0)) for event in events), default=since)})
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/versions") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            versions = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).versions(design_id)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", versions)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/diff") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        base_snapshot_id = query.get("base_snapshot_id", query.get("base", [""]))[0]
        compare_snapshot_id = query.get("compare_snapshot_id", query.get("compare", [""]))[0]
        if not organization_id or not base_snapshot_id or not compare_snapshot_id:
            return 400, _response("error", None, "organization_id, base_snapshot_id, and compare_snapshot_id are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            diff = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).diff(design_id, base_snapshot_id=base_snapshot_id, compare_snapshot_id=compare_snapshot_id)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", diff)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/teaching-view") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        role = query.get("role", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id or not role:
            return 400, _response("error", None, "organization_id and role query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        if principal.role == "player":
            user_id = principal.subject
        else:
            user_id = query.get("user_id", [None])[0]
        try:
            step_value = query.get("step", [None])[0]
            step = int(step_value) if step_value not in (None, "") else None
            view = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).role_view(design_id, role=role, mode=query.get("mode", ["player"])[0], step=step, user_id=user_id)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", view)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/mastery") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            mastery = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).mastery(design_id, role=query.get("role", [None])[0], user_id=query.get("user_id", [None])[0] or principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", mastery)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/legality") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            report = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).legality_report(design_id)
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", report)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/role-view") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        role = query.get("role", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id or not role:
            return 400, _response("error", None, "organization_id and role query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            step_value = query.get("step", [None])[0]
            step = int(step_value) if step_value not in (None, "") else None
            view = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).role_view(design_id, role=role, mode=query.get("mode", ["player"])[0], step=step, user_id=principal.subject if principal.role == "player" else query.get("user_id", [None])[0])
        except (KeyError, TypeError, ValueError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", view)
    if parsed.path == "/v1/playbook/designs/validate" and method.upper() == "POST":
        if not body.get("organization_id") or not isinstance(body.get("design"), dict):
            return 400, _response("error", None, "organization_id and design are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            report = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).validate_draft(body["design"])
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", report)
    if parsed.path == "/v1/playbook/designs" and method.upper() == "POST":
        if not body.get("organization_id") or not isinstance(body.get("design"), dict):
            return 400, _response("error", None, "organization_id and design are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            saved = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).save(design=body["design"], actor=principal.subject, expected_revision=body.get("expected_revision"))
        except (KeyError, TypeError, ValueError) as exc:
            details = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
            if details.get("code") == "DESIGN-CONFLICT":
                current = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).repository.get("play_designs", body.get("design", {}).get("id", ""))
                conflict = {**details, "server_design": current}
                return 409, _response("conflict", conflict, str(details.get("message", "Design changed since it was loaded")))
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=saved["id"], event_type="design_saved", actor=principal.subject, payload={"revision": saved.get("_revision"), "status": saved.get("status")})
        return 201, _response("ok", saved)
    if parsed.path == "/v1/playbook/designs/presence" and method.upper() == "POST":
        required = ("organization_id", "design_id", "session_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).heartbeat(design_id=body["design_id"], session_id=body["session_id"], subject=principal.subject, role=principal.role, display_name=body.get("display_name", principal.subject), color=body.get("color", "#2563eb"), cursor=body.get("cursor"))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/presence/leave" and method.upper() == "POST":
        required = ("organization_id", "design_id", "session_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).leave(design_id=body["design_id"], session_id=body["session_id"], actor=principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/comments/reply" and method.upper() == "POST":
        required = ("organization_id", "design_id", "comment_id", "text")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).reply_comment(body["design_id"], comment_id=body["comment_id"], actor=principal.subject, text=body["text"])
            _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="comment_replied", actor=principal.subject, payload={"comment_id": body["comment_id"], "reply_id": result["id"]})
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/comments/resolve" and method.upper() == "POST":
        required = ("organization_id", "design_id", "comment_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).resolve_comment(body["design_id"], comment_id=body["comment_id"], actor=principal.subject, resolved=body.get("resolved", True) is not False)
            _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="comment_resolved" if result.get("status") == "resolved" else "comment_reopened", actor=principal.subject, payload={"comment_id": body["comment_id"], "status": result.get("status")})
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/request-review" and method.upper() == "POST":
        required = ("organization_id", "design_id", "decision_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).request_review(body["design_id"], actor=principal.subject, decision_ref=body["decision_ref"])
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/publish" and method.upper() == "POST":
        required = ("organization_id", "design_id", "decision_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="lock_artifact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may publish a play design")
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).publish(body["design_id"], actor=principal.subject, decision_ref=body["decision_ref"], game_plan_snapshot_id=body.get("game_plan_snapshot_id"))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="design_published", actor=principal.subject, payload={"release_id": result.get("release_id"), "snapshot_id": result.get("latest_snapshot_id")})
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/branch" and method.upper() == "POST":
        required = ("organization_id", "design_id", "branch_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).branch(body["design_id"], branch_id=body["branch_id"], actor=principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/versioning/merge" and method.upper() == "POST":
        required = ("organization_id", "design_id", "branch_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).merge(body["design_id"], branch_id=body["branch_id"], actor=principal.subject, expected_revision=body.get("expected_revision"))
        except (KeyError, TypeError, ValueError) as exc:
            details = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
            if details.get("code") == "DESIGN-CONFLICT":
                return 409, _response("conflict", details, str(details.get("message", "Design changed since it was loaded")))
            return 422, _response("invalid", None, str(exc))
        if result.get("status") == "conflict":
            return 409, _response("conflict", result, "The branch and target contain element-level merge conflicts")
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="branch_merged", actor=principal.subject, payload={"branch_id": body["branch_id"], "merge_base_snapshot_id": result.get("merge_base_snapshot_id")})
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/versioning/rollback" and method.upper() == "POST":
        required = ("organization_id", "design_id", "snapshot_id", "decision_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="lock_artifact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may roll back a play design")
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).rollback(body["design_id"], snapshot_id=body["snapshot_id"], actor=principal.subject, decision_ref=body["decision_ref"], expected_revision=body.get("expected_revision"))
        except (KeyError, TypeError, ValueError) as exc:
            details = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
            if details.get("code") == "DESIGN-CONFLICT":
                return 409, _response("conflict", details, str(details.get("message", "Design changed since it was loaded")))
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="design_rolled_back", actor=principal.subject, payload={"snapshot_id": body["snapshot_id"], "decision_ref": body["decision_ref"]})
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/mastery" and method.upper() == "POST":
        required = ("organization_id", "design_id", "role", "step_id", "score")
        missing = [field for field in required if body.get(field) in (None, "")]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="record_play_mastery", organization_id=body["organization_id"])
        if denial:
            return denial
        learner_id = principal.subject if principal.role == "player" else body.get("user_id") or principal.subject
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).record_mastery(body["design_id"], role=body["role"], user_id=learner_id, step_id=body["step_id"], score=body["score"], result=body.get("result", "attempted"), actor=principal.subject, practice_ref=body.get("practice_ref"), notes=body.get("notes", ""), attempt_id=body.get("attempt_id"))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="mastery_recorded", actor=principal.subject, payload={"role": body["role"], "step_id": body["step_id"], "status": result.get("status")})
        return 201, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/quiz" and method.upper() == "POST":
        required = ("organization_id", "design_id", "role", "quiz_id", "answer")
        missing = [field for field in required if body.get(field) in (None, "")]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="record_play_mastery", organization_id=body["organization_id"])
        if denial:
            return denial
        learner_id = principal.subject if principal.role == "player" else body.get("user_id") or principal.subject
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).submit_quiz(body["design_id"], role=body["role"], user_id=learner_id, quiz_id=body["quiz_id"], answer=body["answer"], actor=principal.subject, practice_ref=body.get("practice_ref"))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="quiz_submitted", actor=principal.subject, payload={"quiz_id": body["quiz_id"], "correct": result.get("correct")})
        return 201, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/legality/override" and method.upper() == "POST":
        required = ("organization_id", "design_id", "issue_code", "rationale", "decision_ref", "evidence_refs", "expires_at")
        missing = [field for field in required if body.get(field) in (None, "", [])]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        if not isinstance(body.get("evidence_refs"), list):
            return 400, _response("error", None, "evidence_refs must be a list")
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).request_legality_override(body["design_id"], issue_code=body["issue_code"], rationale=body["rationale"], decision_ref=body["decision_ref"], evidence_refs=body["evidence_refs"], expires_at=body["expires_at"], actor=principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="legality_override_requested", actor=principal.subject, payload={"override_id": result.get("id"), "issue_code": body["issue_code"]})
        return 201, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/legality/override/approve" and method.upper() == "POST":
        required = ("organization_id", "design_id", "override_id", "decision_ref")
        missing = [field for field in required if body.get(field) in (None, "")]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="lock_artifact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may approve a legality override")
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).approve_legality_override(body["design_id"], override_id=body["override_id"], decision_ref=body["decision_ref"], actor=principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="legality_override_approved", actor=principal.subject, payload={"override_id": result.get("id"), "decision_ref": body["decision_ref"]})
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/export/preflight" and method.upper() == "POST":
        required = ("organization_id", "kind", "format")
        missing = [field for field in required if body.get(field) in (None, "")]
        design_ids = body.get("design_ids") if isinstance(body.get("design_ids"), list) else ([body.get("design_id")] if body.get("design_id") else [])
        if missing or not design_ids:
            fields = missing + ([] if design_ids else ["design_id or design_ids"])
            return 400, _response("error", None, f"Missing required fields: {', '.join(fields)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=body["organization_id"])
        if denial:
            principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            preflight = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).export_preflight(design_ids, kind=body["kind"], format=body["format"], role=body.get("role"), layout=body.get("layout"))
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            details = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else None
            return 422, _response("invalid", details, str(exc))
        return 200, _response("ok", preflight)
    if parsed.path == "/v1/playbook/designs/export" and method.upper() == "POST":
        required = ("organization_id", "kind", "format")
        missing = [field for field in required if body.get(field) in (None, "")]
        design_ids = body.get("design_ids") if isinstance(body.get("design_ids"), list) else ([body.get("design_id")] if body.get("design_id") else [])
        if missing or not design_ids:
            fields = missing + ([] if design_ids else ["design_id or design_ids"])
            return 400, _response("error", None, f"Missing required fields: {', '.join(fields)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=body["organization_id"])
        if denial:
            principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            artifact = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).export_artifact(design_ids, kind=body["kind"], format=body["format"], actor=principal.subject, role=body.get("role"), black_white=bool(body.get("black_white", False)), branding=body.get("branding"), layout=body.get("layout"), signing_secret=resolve_auth_secret())
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            details = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else None
            return 422, _response("invalid", details, str(exc))
        _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=design_ids[0], event_type="export_created", actor=principal.subject, payload={"artifact_id": artifact.get("artifact_id"), "kind": artifact.get("kind"), "format": artifact.get("format"), "sha256": artifact.get("sha256")})
        return 200, _response("ok", artifact)
    if parsed.path == "/v1/playbook/designs/comments" and method.upper() == "POST":
        required = ("organization_id", "design_id", "text")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).add_comment(body["design_id"], actor=principal.subject, text=body["text"], element_id=body.get("element_id"))
            _play_design_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).record_event(design_id=body["design_id"], event_type="comment_added", actor=principal.subject, payload={"comment_id": result["id"], "element_id": result.get("element_id")})
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", result)
    if parsed.path.startswith("/v1/playbook/designs/") and parsed.path.endswith("/comments") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        design_id = parsed.path.split("/")[4]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        comments = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).comments(design_id)
        roots = [comment for comment in comments if not comment.get("parent_comment_id")]
        threads = [{"thread_id": root.get("thread_id", root.get("id")), "root": root, "replies": [comment for comment in comments if comment.get("parent_comment_id") == root.get("id")]} for root in roots]
        return 200, _response("ok", {"comments": comments, "threads": threads})
    if parsed.path == "/v1/playbook/designs/assets/lifecycle" and method.upper() == "POST":
        required = ("organization_id", "asset_id", "status")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="manage_ontology", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).update_asset_lifecycle(body["asset_id"], status=body["status"], actor=principal.subject, replacement_id=body.get("replacement_id"), reason=body.get("reason", ""))
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/designs/assets/migrate" and method.upper() == "POST":
        required = ("organization_id", "old_asset_id", "new_asset_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _play_designs(service, organization_id=principal.organization_id, actor=principal.subject).migrate_asset(body["old_asset_id"], body["new_asset_id"], actor=principal.subject)
        except (KeyError, TypeError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/health":
        return 200, _response("ok", {"service": "NFL-FIDOS", "scope": "NFL only"})
    if parsed.path == "/v1/control":
        root = Path(__file__).resolve().parents[2]
        with (root / "control" / "manifest.json").open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        return 200, _response("ok", {"scope": manifest["scope"], "stage": manifest["current_stage"], "work_package": manifest["current_work_package"]})
    if parsed.path == "/v1/control/stage-25-acceptance" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        spec = load_master_spec()
        spec_validation = validate_master_spec(spec)
        acceptances = [item for item in service.repository.list("stage25_spec_acceptances") if item.get("organization_id") == principal.organization_id]
        return 200, _response("ok", {"spec": {"spec_id": spec.get("spec_id"), "version": spec.get("version"), "validation": spec_validation}, "acceptances": acceptances, "production_implementation_allowed": False, "stage_advance_authorized": False})
    if parsed.path == "/v1/control/stage-25-acceptance" and method.upper() == "POST":
        required = ("organization_id", "acceptance_id", "rationale", "evidence_refs", "accepted_at")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may submit Stage 25 specification acceptance evidence")
        spec = load_master_spec()
        record = build_stage25_spec_acceptance(acceptance_id=body["acceptance_id"], spec=spec, approver=principal.subject, rationale=body["rationale"], evidence_refs=body["evidence_refs"], accepted_at=body["accepted_at"])
        record["organization_id"] = principal.organization_id
        validation = validate_stage25_spec_acceptance(record, spec=spec)
        if validation["status"] != "valid":
            return 422, _response("invalid", {"record": record, "validation": validation}, "Stage 25 specification acceptance evidence is not valid")
        service.repository.put("stage25_spec_acceptances", record["id"], record, actor=principal.subject, reason="stage25_spec_acceptance_evidence_recorded")
        return 201, _response("ok", {"record": record, "validation": validation, "production_implementation_allowed": False, "stage_advance_authorized": False})
    if parsed.path == "/v1/ux/usability-feedback/summary" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        summary = summarize_pilot_feedback(organization_id=principal.organization_id, feedback=tenant.list("ux_usability_feedback"))
        return 200, _response("ok", summary)
    if parsed.path == "/v1/ux/usability-feedback" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "feedback": tenant.list("ux_usability_feedback"), "pilot_validation_complete": False})
    if parsed.path == "/v1/ux/usability-feedback" and method.upper() == "POST":
        required = ("organization_id", "feedback_id", "session_id", "screen_id", "task_id", "outcome", "severity", "feedback_text", "submitted_at", "evidence_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="submit_usability_feedback", organization_id=body["organization_id"])
        if denial:
            return denial
        root = Path(__file__).resolve().parents[2]
        try:
            architecture = json.loads((root / "ux" / "ux-architecture.json").read_text(encoding="utf-8"))
            screen_ids = {screen.get("id") for screen in architecture.get("screen_inventory", [])}
            feedback = build_usability_feedback(feedback_id=body["feedback_id"], organization_id=principal.organization_id, session_id=body["session_id"], user_role=principal.role, screen_id=body["screen_id"], task_id=body["task_id"], outcome=body["outcome"], severity=body["severity"], feedback_text=body["feedback_text"], submitted_at=body["submitted_at"], evidence_refs=body["evidence_refs"], accessibility_issue=body.get("accessibility_issue", False), duration_seconds=body.get("duration_seconds"), satisfaction_score=body.get("satisfaction_score"))
            validation = validate_usability_feedback(feedback, screen_ids=screen_ids)
        except (TypeError, ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
            return 422, _response("invalid", None, str(exc))
        if validation["status"] != "valid":
            return 422, _response("invalid", {"feedback": feedback, "validation": validation}, "Usability feedback is not valid")
        saved = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject).put("ux_usability_feedback", feedback["feedback_id"], feedback, actor=principal.subject, reason="ux_usability_feedback_recorded")
        return 201, _response("ok", {"feedback": saved, "validation": validation, "pilot_validation_complete": False})
    if parsed.path == "/v1/control/stage-0-approval" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        root = Path(__file__).resolve().parents[2]
        registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
        gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
        gate = evaluate_stage0_exit(registry, gap_audit_complete=gap_audit.get("status") == "complete")
        approvals = [item for item in service.repository.list("stage0_owner_approvals") if item.get("organization_id") == principal.organization_id]
        return 200, _response("ok", {"gate": gate, "approvals": approvals, "production_implementation_allowed": False, "stage_advance_authorized": False})
    if parsed.path == "/v1/control/stage-0-approval" and method.upper() == "POST":
        required = ("organization_id", "approval_id", "rationale", "evidence_refs", "approved_at")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may submit Stage 0 approval evidence")
        root = Path(__file__).resolve().parents[2]
        registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
        gap_audit = json.loads((root / "control" / "stage-0-gap-audit.json").read_text(encoding="utf-8"))
        gate = evaluate_stage0_exit(registry, gap_audit_complete=gap_audit.get("status") == "complete")
        record = build_stage0_owner_approval(approval_id=body["approval_id"], gate_result=gate, registry_id=registry["registry_id"], approver=principal.subject, rationale=body["rationale"], evidence_refs=body["evidence_refs"], approved_at=body["approved_at"])
        record["organization_id"] = principal.organization_id
        validation = validate_stage0_owner_approval(record, gate_result=gate)
        if validation["status"] != "valid":
            return 422, _response("invalid", {"record": record, "validation": validation}, "Stage 0 approval evidence is not valid")
        service.repository.put("stage0_owner_approvals", record["id"], record, actor=principal.subject, reason="stage0_owner_approval_evidence_recorded")
        return 201, _response("ok", {"record": record, "validation": validation, "production_implementation_allowed": False, "stage_advance_authorized": False})
    if parsed.path == "/v1/delivery/pilot-organization" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id":principal.organization_id, "selections":tenant.list("pilot_selections"), "live_pilot":False, "production_implementation_allowed":False})
    if parsed.path == "/v1/delivery/pilot-organization" and method.upper() == "POST":
        required = ("organization_id", "selection_id", "wave_id", "pilot_users", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may select a pilot organization")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        organization = tenant.get("organizations", principal.organization_id)
        bundles = tenant.list("organization_terminology_bundles")
        bundle = next((item for item in bundles if item.get("status") == "approved"), None)
        if organization is None or bundle is None:
            return 409, _response("blocked", None, "An active organization context and approved terminology bundle are required before pilot selection")
        selection = build_pilot_selection(selection_id=body["selection_id"], organization=organization, terminology_bundle=bundle, wave_id=body["wave_id"], pilot_users=body["pilot_users"], owner=principal.subject, decision_ref=body["decision_ref"])
        if selection["status"] != "selected":
            return 422, _response("invalid", selection)
        saved = tenant.put("pilot_selections", selection["id"], selection, actor=principal.subject, reason="pilot_organization_selected")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/delivery/pilot-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id":principal.organization_id, "packages":tenant.list("pilot_delivery_packages"), "live_pilot":False, "production_implementation_allowed":False})
    if parsed.path == "/v1/delivery/pilot-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "selection_id", "readiness_report_id", "rollback")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may compose a pilot delivery package")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        selection = tenant.get("pilot_selections", body["selection_id"])
        readiness = tenant.get("pilot_readiness_reports", body["readiness_report_id"])
        if selection is None or readiness is None:
            return 404, _response("error", None, "Pilot selection and readiness report are required")
        package = build_pilot_delivery_package(package_id=body["package_id"], selection=selection, readiness=readiness, rollback=body["rollback"])
        if package["status"] != "ready_for_bounded_pilot":
            return 422, _response("blocked", package)
        saved = tenant.put("pilot_delivery_packages", package["id"], package, actor=principal.subject, reason="pilot_delivery_package_composed")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/organizations/context" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id":principal.organization_id, "contexts":tenant.list("organizations"), "terminology_bundles":tenant.list("organization_terminology_bundles")})
    if parsed.path == "/v1/organizations/context" and method.upper() == "POST":
        required = ("organization_id", "name", "season", "team_id", "people", "terminology_version", "source")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="manage_organization", organization_id=body["organization_id"])
        if denial:
            return denial
        package = build_onboarding_package(organization_id=principal.organization_id, name=body["name"], season=body["season"], team_id=body["team_id"], people=body["people"], terminology_version=body["terminology_version"], owner=principal.subject, source=body["source"], terminology_bundle=body.get("terminology_bundle"))
        if package["status"] == "rejected":
            return 422, _response("invalid", package)
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        organization_record = dict(package["organization"])
        organization_record["organization_id"] = organization_record["id"]
        tenant.put("organizations", organization_record["id"], organization_record, actor=principal.subject, reason="organization_onboarding_context_created")
        tenant.put("organization_terminology_bundles", package["terminology_bundle"]["id"], package["terminology_bundle"], actor=principal.subject, reason="organization_terminology_bundle_initialized")
        return 201, _response("ok", package)
    if parsed.path == "/v1/organizations/context/approve" and method.upper() == "POST":
        required = ("organization_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_organization", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        organization = tenant.get("organizations", body["organization_id"])
        bundles = tenant.list("organization_terminology_bundles")
        bundle = next((item for item in bundles if item.get("organization_id") == principal.organization_id), None)
        if organization is None or bundle is None:
            return 404, _response("error", None, "Draft organization context and terminology bundle are required")
        result = approve_onboarding_package(organization=organization, terminology_bundle=bundle, approver=principal.subject, decision_ref=body["decision_ref"])
        if result["status"] != "approved":
            return 422, _response("invalid", result)
        tenant.put("organizations", result["organization"]["id"], result["organization"], actor=principal.subject, reason="organization_context_approved")
        tenant.put("organization_terminology_bundles", result["terminology_bundle"]["id"], result["terminology_bundle"], actor=principal.subject, reason="organization_terminology_bundle_approved")
        return 200, _response("ok", result)
    if parsed.path == "/v1/organizations/operating-bundle" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "bundles": tenant.list("organization_operating_bundles"), "production_implementation_allowed": False})
    if parsed.path == "/v1/organizations/operating-bundle" and method.upper() == "POST":
        required = ("organization_id", "bundle_id", "season")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        if "components" not in body and "component_ids" not in body:
            return 400, _response("error", None, "Either components or component_ids is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="manage_organization", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        components = body.get("components") if "components" in body else load_persisted_organization_components(tenant, body.get("component_ids"))
        bundle = build_organization_operating_bundle(bundle_id=body["bundle_id"], organization_id=principal.organization_id, season=body["season"], components=components)
        if bundle["status"] != "ready_for_owner_review":
            return 422, _response("blocked", bundle)
        saved = tenant.put("organization_operating_bundles", bundle["id"], bundle, actor=principal.subject, reason="organization_operating_bundle_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/organizations/operating-bundle/approve" and method.upper() == "POST":
        required = ("organization_id", "bundle_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_organization", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        bundle = tenant.get("organization_operating_bundles", body["bundle_id"])
        if bundle is None:
            return 404, _response("error", None, "Organization operating bundle is required")
        result = approve_organization_operating_bundle(bundle=bundle, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if result["status"] != "approved_for_non_production":
            return 422, _response("invalid", result)
        saved = tenant.put("organization_operating_bundles", result["id"], result, actor=principal.subject, reason="organization_operating_bundle_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/evals":
        return 200, _response("ok", run_minimum_eval_suite())
    if parsed.path in {"/v1/ontology/resolve", "/v1/ontology/related"}:
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        resolver = OntologyResolver()
        if parsed.path.endswith("/resolve"):
            term = query.get("term", [""])[0]
            if not term:
                return 400, _response("error", None, "term query parameter is required")
            if query.get("team_id", [""])[0]:
                service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
                result = TeamOntologyService(TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject), resolver).resolve(team_id=query["team_id"][0], value=term)
            else:
                result = resolver.resolve(term)
        else:
            term_id = query.get("term_id", [""])[0]
            if not term_id:
                return 400, _response("error", None, "term_id query parameter is required")
            result = {"term_id": term_id, "relationships": resolver.related(term_id, relationship_type=query.get("relationship_type", [None])[0])}
        result["organization_id"] = principal.organization_id
        return 200, _response("ok", result)
    if parsed.path == "/v1/ontology/team-aliases" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        aliases = TeamOntologyService(TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)).list_aliases(team_id=query.get("team_id", [None])[0])
        return 200, _response("ok", {"organization_id": principal.organization_id, "aliases": aliases})
    if parsed.path == "/v1/film/search":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        filters = {key: query[key][0] for key in ("query", "team", "opponent", "domain", "label", "confidence") if query.get(key, [""])[0]}
        return 200, _response("ok", {"organization_id": principal.organization_id, "results": _film_service(service, organization_id=principal.organization_id, actor=principal.subject).search(**filters)})
    if parsed.path == "/v1/knowledge/search":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        try:
            limit = int(query.get("limit", ["100"])[0])
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            results = KnowledgeRetrievalService(tenant).search(query=query.get("query", [""])[0], classification=query.get("classification", [None])[0], state=query.get("state", [None])[0], collection=query.get("collection", [None])[0], limit=limit)
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok", {"organization_id":principal.organization_id, "results":results, "count":len(results)})
    if parsed.path == "/v1/film/annotation-sessions" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        sessions = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).repository.list("film_annotation_sessions")
        return 200, _response("ok", {"organization_id": principal.organization_id, "sessions": sessions})
    if parsed.path == "/v1/film/playlists" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", {"organization_id": principal.organization_id, "playlists": _film_service(service, organization_id=principal.organization_id, actor=principal.subject).list_playlists(role=principal.role)})
    if parsed.path == "/v1/film/voice-notes" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        notes = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).list_voice_notes(role=principal.role)
        return 200, _response("ok", {"organization_id": principal.organization_id, "voice_notes": notes})
    if parsed.path in {"/v1/media/assets", "/v1/media/clips"} and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        catalog = _media_service(service, organization_id=principal.organization_id, actor=principal.subject)
        if parsed.path.endswith("/assets"):
            return 200, _response("ok", {"organization_id": principal.organization_id, "assets": catalog.list_assets()})
        return 200, _response("ok", {"organization_id": principal.organization_id, "clips": catalog.list_clips(opponent=query.get("opponent", [None])[0], team=query.get("team", [None])[0])})
    if parsed.path == "/v1/media/jobs" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
        if denial:
            return denial
        jobs = _media_jobs(service, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "jobs": jobs.list_jobs(status=query.get("status", [None])[0])})
    if parsed.path == "/v1/media/retention-plan" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            days = int(query.get("retention_days", ["365"])[0])
            report = plan_media_retention(repository=tenant, retention_days=days)
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok", report)
    if parsed.path == "/v1/media/retention-scan":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="read_governance", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            retention_days = int(body.get("retention_days", 365))
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            report = MediaRetentionScheduler(tenant).run_scan(actor=principal.subject, retention_days=retention_days)
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok", report)
    if parsed.path == "/v1/media/retention-execute":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or "managed_root" not in body:
            return 400, _response("error", None, "organization_id and managed_root are required")
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            root = Path(__file__).resolve().parents[2]
            with (root / "control" / "manifest.json").open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            report = execute_media_retention(repository=tenant, actor=principal.subject, actor_role=principal.role, approval_ref=body.get("approval_ref"), managed_root=body["managed_root"], retention_days=int(body.get("retention_days", 365)), execute=bool(body.get("execute", False)), environment=body.get("environment", "validation"), production_implementation_allowed=bool(manifest.get("production_implementation_allowed", False)))
        except (TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
            return 400, _response("error", None, str(exc))
        status = "ok" if report["status"] in {"planned", "executed"} else "blocked"
        return (200 if status == "ok" else 403), _response(status, report, report.get("blocker"))
    if parsed.path == "/v1/media/transform-batch":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            report = MediaTransformOrchestrator(tenant).run_batch(actor=principal.subject, worker_id=body.get("worker_id", principal.subject), max_jobs=body.get("max_jobs", 10), allowed_roots=body.get("allowed_roots", []))
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok" if report["status"] == "completed" else "partial", report)
    if parsed.path == "/v1/sources" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", {"organization_id": principal.organization_id, "sources": _sources(service, organization_id=principal.organization_id, actor=principal.subject).list_sources()})
    if parsed.path == "/v1/sources/refresh-all":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="refresh_source", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            report = _sources(service, organization_id=principal.organization_id, actor=principal.subject).refresh_all(actor=principal.subject, stale_only=body.get("stale_only", True), max_sources=body.get("max_sources", 100))
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok" if report["status"] == "completed" else "partial", report)
    if parsed.path == "/v1/sources/scheduled-refresh":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="refresh_source", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            report = SourceRefreshScheduler(tenant).run_due(actor=principal.subject, max_sources=body.get("max_sources", 100))
        except (TypeError, ValueError) as exc:
            return 400, _response("error", None, str(exc))
        return 200, _response("ok" if report["status"] in {"completed", "current"} else "partial", report)
    if parsed.path == "/v1/operator/summary" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        root = Path(__file__).resolve().parents[2]
        with (root / "control" / "manifest.json").open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        eval_result = run_minimum_eval_suite() if query.get("include_evals", [""])[0].lower() == "true" else {"status":"not_requested", "passed":0, "failed":0}
        summary = build_operator_summary(repository=tenant, role=principal.role, stage=manifest["current_stage"], work_package=manifest["current_work_package"], season=query.get("season", [None])[0], eval_result=eval_result)
        return 200, _response("ok", summary)
    if parsed.path == "/v1/governance/inbox" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_approval_inbox(repository=tenant, role=principal.role))
    if parsed.path == "/v1/governance/inbox/review" and method.upper() == "POST":
        required = ("organization_id", "collection", "record_id", "decision", "decision_ref", "rationale")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_change", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = review_inbox_item(
                repository=TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject),
                collection=body["collection"],
                record_id=body["record_id"],
                decision=body["decision"],
                decision_ref=body["decision_ref"],
                rationale=body["rationale"],
                reviewer=principal.subject,
                reviewer_role=principal.role,
            )
        except KeyError as exc:
            return 404, _response("error", None, str(exc))
        except (TypeError, ValueError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/operations/inbox" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_operations_inbox", organization_id=organization_id)
        if denial:
            return denial
        filter_keys = ("category", "status", "urgency", "due_state", "assigned_to", "assigned_to_me", "unread_only", "include_read", "search")
        filters = {key: query[key][0] for key in filter_keys if query.get(key)}
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_operations_inbox(repository=tenant, role=principal.role, actor=principal.subject, filters=filters))
    if parsed.path == "/v1/operations/inbox/notifications/read" and method.upper() == "POST":
        organization_id = body.get("organization_id")
        notification_ids = body.get("notification_ids")
        if not organization_id or not isinstance(notification_ids, list) or not notification_ids:
            return 400, _response("error", None, "organization_id and a non-empty notification_ids list are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="update_operations_inbox", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            result = mark_notifications_read(repository=tenant, notification_ids=[str(item) for item in notification_ids], actor=principal.subject)
        except (TypeError, ValueError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/collaboration/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_collaboration", organization_id=organization_id)
        if denial:
            return denial
        workspace = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(
            actor=principal.subject,
            role=principal.role,
            status=query.get("status", [None])[0],
            assigned_to=query.get("assigned_to", [None])[0],
            unread_only=query.get("unread_only", ["false"])[0].lower() == "true",
        )
        return 200, _response("ok", workspace)
    if parsed.path == "/v1/collaboration/events" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        try:
            since = max(0, int(query.get("since", ["0"])[0]))
        except (TypeError, ValueError):
            return 400, _response("error", None, "since must be an integer")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_collaboration", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "events": CollaborationWorkspaceService(tenant).events(since_sequence=since, actor=principal.subject, role=principal.role)})
    if parsed.path == "/v1/collaboration/presence" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_collaboration", organization_id=organization_id)
        if denial:
            return denial
        workspace = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(actor=principal.subject, role=principal.role)
        return 200, _response("ok", {"organization_id": principal.organization_id, "presence": workspace["presence"]})
    if parsed.path == "/v1/collaboration/threads":
        required = ("organization_id", "thread_id", "title", "body", "entity_type", "entity_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_workspace", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            thread = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_thread(
                thread_id=body["thread_id"], title=body["title"], body=body["body"], entity_type=body["entity_type"], entity_id=body["entity_id"],
                deep_link=body.get("deep_link", "/inbox"), author=principal.subject, role=principal.role, assignee=body.get("assignee"),
                mentions=body.get("mentions", []), participants=body.get("participants", []), priority=body.get("priority", "normal"), due_at=body.get("due_at"),
            )
        except (TypeError, ValueError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", thread)
    if parsed.path == "/v1/collaboration/comments":
        required = ("organization_id", "thread_id", "comment_id", "body")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_workspace", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            thread = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).append_comment(thread_id=body["thread_id"], comment_id=body["comment_id"], body=body["body"], mentions=body.get("mentions", []), author=principal.subject, role=principal.role)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", thread)
    if parsed.path == "/v1/collaboration/threads/assign":
        required = ("organization_id", "thread_id", "assignee")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="assign_collaboration", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            thread = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).assign_thread(thread_id=body["thread_id"], assignee=body["assignee"], due_at=body.get("due_at"), priority=body.get("priority"), actor=principal.subject, role=principal.role)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", thread)
    if parsed.path == "/v1/collaboration/threads/resolve":
        required = ("organization_id", "thread_id", "decision", "rationale")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="resolve_collaboration", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            thread = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).resolve_thread(thread_id=body["thread_id"], decision=body["decision"], rationale=body["rationale"], actor=principal.subject, role=principal.role)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", thread)
    if parsed.path == "/v1/collaboration/notifications/read":
        organization_id = body.get("organization_id")
        notification_ids = body.get("notification_ids")
        if not organization_id or not isinstance(notification_ids, list) or not notification_ids:
            return 400, _response("error", None, "organization_id and a non-empty notification_ids list are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="update_collaboration", organization_id=organization_id)
        if denial:
            return denial
        result = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).mark_notifications_read(notification_ids=[str(item) for item in notification_ids], actor=principal.subject)
        return 200, _response("ok", result)
    if parsed.path == "/v1/collaboration/presence":
        required = ("organization_id", "session_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="update_collaboration", organization_id=body["organization_id"])
        if denial:
            return denial
        presence = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).heartbeat(session_id=body["session_id"], actor=principal.subject, role=principal.role, display_name=body.get("display_name", principal.subject), color=body.get("color", "#2563eb"), cursor=body.get("cursor"))
        return 200, _response("ok", presence)
    if parsed.path == "/v1/collaboration/presence/leave":
        required = ("organization_id", "session_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="update_collaboration", organization_id=body["organization_id"])
        if denial:
            return denial
        result = _collaboration_workspace(service, organization_id=principal.organization_id, actor=principal.subject).leave(session_id=body["session_id"], actor=principal.subject)
        return 200, _response("ok", result)
    if parsed.path == "/v1/delivery/pilot-readiness" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        reports = tenant.list("pilot_readiness_reports")
        return 200, _response("ok", {"organization_id": principal.organization_id, "reports": reports, "human_review_required": True, "production_implementation_allowed": False})
    if parsed.path == "/v1/delivery/pilot-readiness" and method.upper() == "POST":
        required = ("organization_id", "wave_id", "pilot_users", "completed_capabilities", "acceptance_evidence", "feature_flags", "rollback_tested")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            root = Path(__file__).resolve().parents[2]
            strategy = json.loads((root / "delivery" / "mvp-strategy.json").read_text(encoding="utf-8"))
            waves = {wave.get("id"): wave for wave in strategy.get("waves", [])}
            wave = waves.get(body["wave_id"])
            if wave is None:
                return 422, _response("invalid", None, f"Unknown delivery wave: {body['wave_id']}")
            eval_result = run_minimum_eval_suite()
            owner_approval = body.get("owner_approval") if principal.role == "program_owner" else None
            report = evaluate_pilot_readiness(
                organization_id=principal.organization_id,
                pilot_users=body["pilot_users"],
                wave=wave,
                completed_capabilities=set(body["completed_capabilities"]),
                eval_result={"status":eval_result["status"], "passed":eval_result["passed"], "failed":eval_result["failed"]},
                acceptance_evidence=body["acceptance_evidence"],
                feature_flags=body["feature_flags"],
                rollback_tested=bool(body["rollback_tested"]),
                owner_approval=owner_approval,
            )
            report.update({"id":f"PILOT-READINESS-{principal.organization_id}-{body['wave_id']}", "requested_by":principal.subject, "requested_role":principal.role, "eval_checkpoint":{"status":eval_result["status"], "passed":eval_result["passed"], "failed":eval_result["failed"]}})
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            tenant.put("pilot_readiness_reports", report["id"], report, actor=principal.subject, reason="pilot_readiness_evaluated")
        except (OSError, TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", report)
    if parsed.path == "/v1/roster/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_roster", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_roster_workspace(repository=tenant, role=principal.role, actor=principal.subject, position_group=query.get("position_group", [None])[0], status=query.get("status", [None])[0], search=query.get("search", [None])[0]))
    if parsed.path == "/v1/roster/players":
        required = ("organization_id", "player_id", "display_name", "position", "position_group", "status", "availability", "owner", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_roster", organization_id=body["organization_id"])
        if denial:
            return denial
        player = create_roster_player(player_id=body["player_id"], organization_id=principal.organization_id, display_name=body["display_name"], position=body["position"], position_group=body["position_group"], jersey_number=body.get("jersey_number"), aliases=body.get("aliases", []), eligibility=body.get("eligibility", []), role_groups=body.get("role_groups", []), status=body["status"], availability=body["availability"], owner=body["owner"], source_refs=body["source_refs"], actor=principal.subject)
        if player["status"] == "invalid":
            return 422, _response("invalid", player, "Roster player was rejected")
        saved = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject).put("roster_players", player["id"], player, actor=principal.subject, reason="roster_player_created")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/roster/depth-charts":
        required = ("organization_id", "depth_chart_id", "unit", "position", "slots", "season")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_roster", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        chart = save_depth_chart(repository=tenant, depth_chart_id=body["depth_chart_id"], unit=body["unit"], position=body["position"], slots=body["slots"], season=body["season"], week=body.get("week"), actor=principal.subject)
        if chart["status"] == "invalid":
            return 422, _response("invalid", chart, "Depth chart was rejected")
        return 201, _response("ok", tenant.put("depth_charts", chart["id"], chart, actor=principal.subject, reason="depth_chart_saved"))
    if parsed.path == "/v1/roster/personnel-packages":
        required = ("organization_id", "package_id", "name", "unit", "roles", "player_ids", "season")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_roster", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = save_personnel_package(repository=tenant, package_id=body["package_id"], name=body["name"], unit=body["unit"], roles=body["roles"], player_ids=body["player_ids"], season=body["season"], actor=principal.subject)
        if package["status"] == "invalid":
            return 422, _response("invalid", package, "Personnel package was rejected")
        return 201, _response("ok", tenant.put("personnel_packages", package["id"], package, actor=principal.subject, reason="personnel_package_saved"))
    if parsed.path == "/v1/player/today" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        player_id = query.get("player_id", [""])[0]
        if not organization_id or not player_id:
            return 400, _response("error", None, "organization_id and player_id query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_own_development", organization_id=organization_id)
        if denial:
            return denial
        if principal.subject != player_id and principal.role not in {"coach_staff", "program_owner"}:
            return 403, _response("error", None, "Player workspace is restricted to the player or authorized coaching authority")
        return 200, _response("ok", _player_workspace(service, organization_id=principal.organization_id, actor=principal.subject).today(player_id=player_id))
    if parsed.path == "/v1/game-plan/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_game_plan", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_game_plan_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/delivery/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_delivery", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_delivery_workspace(repository=tenant, week=query.get("week", [None])[0]))
    if parsed.path == "/v1/delivery/tasks":
        required = ("organization_id", "task_id", "title", "category", "owner", "due_at", "week")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_delivery", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        task = create_delivery_task(repository=tenant, task_id=body["task_id"], title=body["title"], category=body["category"], owner=body["owner"], due_at=body["due_at"], week=body["week"], linked_records=body.get("linked_records", []), priority=body.get("priority", "normal"), actor=principal.subject)
        return (201 if task.get("status") == "scheduled" else 422), _response("ok" if task.get("status") == "scheduled" else "invalid", task)
    if parsed.path == "/v1/delivery/tasks/complete":
        required = ("organization_id", "task_id")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="update_delivery", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            task = complete_delivery_task(repository=tenant, task_id=body["task_id"], actor=principal.subject, note=body.get("note", ""))
        except KeyError as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", task)
    if parsed.path == "/v1/delivery/packets":
        required = ("organization_id", "packet_id", "packet_type", "week")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_delivery", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        packet = create_delivery_packet(repository=tenant, packet_id=body["packet_id"], packet_type=body["packet_type"], week=body["week"], linked_records=body.get("linked_records", []), actor=principal.subject)
        return (201 if packet.get("status") in {"under_review", "blocked"} else 422), _response("ok" if packet.get("status") in {"under_review", "blocked"} else "invalid", packet)
    if parsed.path == "/v1/game-plan/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "season", "team_context", "week_context", "plan")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_game_plan", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_game_plan(package_id=body["package_id"], organization_id=principal.organization_id, season=body["season"], team_context=body["team_context"], week_context=body["week_context"], plan=body["plan"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization game-plan package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_game_plan_packages", package["id"], package, actor=principal.subject, reason="organization_game_plan_package_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/game-plan/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization game plans")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_game_plan_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization game-plan package was not found")
        approved = approve_organization_game_plan(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization game-plan approval was not accepted")
        saved = tenant.put("organization_game_plan_packages", approved["id"], approved, actor=principal.subject, reason="organization_game_plan_package_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/game-plan/release-room" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_game_plan", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_release_room(repository=tenant, week=query.get("week", [None])[0]))
    if parsed.path == "/v1/game-plan/release-room/snapshots":
        required = ("organization_id", "snapshot_id", "plan_id", "week", "note")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_game_plan", organization_id=body["organization_id"])
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        snapshot = create_release_snapshot(repository=tenant, snapshot_id=body["snapshot_id"], plan_id=body["plan_id"], week=body["week"], note=body["note"], actor=principal.subject, artifact_refs=body.get("artifact_refs") or body.get("source_refs") or [])
        return (201 if snapshot.get("status") == "pending_approval" else 422), _response("ok" if snapshot.get("status") == "pending_approval" else "invalid", snapshot)
    if parsed.path == "/v1/game-plan/release-room/approve":
        required = ("organization_id", "snapshot_id", "decision_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may approve a release snapshot")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            snapshot = approve_release_snapshot(repository=tenant, snapshot_id=body["snapshot_id"], decision_ref=body["decision_ref"], actor=principal.subject)
        except (KeyError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", snapshot)
    if parsed.path == "/v1/game-plan/release-room/rollback":
        required = ("organization_id", "snapshot_id", "decision_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may roll back a release snapshot")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            snapshot = rollback_release_snapshot(repository=tenant, snapshot_id=body["snapshot_id"], decision_ref=body["decision_ref"], actor=principal.subject)
        except (KeyError, ValueError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", snapshot)
    if parsed.path == "/v1/game-plan/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_game_plan", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", build_game_plan_workspace(repository=tenant, week=query.get("week", [None])[0]))
    if parsed.path == "/v1/game-plan/threads" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_game_plan", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _game_plan_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).workspace(plan_id=query.get("plan_id", [None])[0]))
    if parsed.path == "/v1/game-plan/threads":
        required = ("organization_id", "thread_id", "plan_id", "week", "topic", "comment", "evidence_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_game_plan", organization_id=body["organization_id"])
        if denial:
            return denial
        result = _game_plan_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).create_thread(thread_id=body["thread_id"], plan_id=body["plan_id"], week=body["week"], topic=body["topic"], comment=body["comment"], evidence_refs=body["evidence_refs"], author=principal.subject, role=principal.role)
        return 201 if result["status"] == "open" else 422, _response("ok" if result["status"] == "open" else "invalid", result)
    if parsed.path == "/v1/game-plan/threads/comments":
        required = ("organization_id", "thread_id", "comment_id", "comment", "evidence_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_game_plan", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _game_plan_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).append_comment(thread_id=body["thread_id"], comment_id=body["comment_id"], comment=body["comment"], evidence_refs=body["evidence_refs"], author=principal.subject, role=principal.role)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/game-plan/threads/resolve":
        required = ("organization_id", "thread_id", "decision", "decision_ref", "rationale")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="collaborate_game_plan", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _game_plan_collaboration(service, organization_id=principal.organization_id, actor=principal.subject).resolve_thread(thread_id=body["thread_id"], decision=body["decision"], decision_ref=body["decision_ref"], resolver=principal.subject, role=principal.role, rationale=body["rationale"])
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/practice/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_practice", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _practice_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(week=query.get("week", [None])[0]))
    if parsed.path == "/v1/practice/drills" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_practice", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        search = query.get("search", [""])[0].strip().lower()
        position_group = query.get("position_group", [""])[0].strip().lower()
        drills = tenant.list("drills")
        if search:
            drills = [drill for drill in drills if search in json.dumps(drill, sort_keys=True, default=str).lower()]
        if position_group:
            drills = [drill for drill in drills if position_group in {str(value).lower() for value in drill.get("position_groups", [])}]
        return 200, _response("ok", {"organization_id": principal.organization_id, "status": "ready" if drills else "empty", "drills": drills})
    if parsed.path == "/v1/schemes/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_scheme", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _scheme_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(unit=query.get("unit", [None])[0]))
    if parsed.path == "/v1/analytics/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_analytics", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _analytics_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(situation=query.get("situation", [None])[0]))
    if parsed.path == "/v1/scouting/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_scouting", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _scouting_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(opponent=query.get("opponent", [None])[0]))
    if parsed.path == "/v1/scouting/tendency-explorer" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_scouting", organization_id=organization_id)
        if denial:
            return denial
        filters = {key: query[key][0] for key in ("down", "distance", "field_zone", "personnel", "formation", "motion", "front", "coverage", "pressure") if query.get(key, [""])[0]}
        return 200, _response("ok", _scouting_workspace(service, organization_id=principal.organization_id, actor=principal.subject).tendency_explorer(opponent=query.get("opponent", [None])[0], filters=filters))
    if parsed.path == "/v1/playbook/visual" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        visual_id = query.get("visual_id", [""])[0]
        if not organization_id or not visual_id:
            return 400, _response("error", None, "organization_id and visual_id query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_assigned_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            data = _visual_workspace(service, organization_id=principal.organization_id, actor=principal.subject).get_visual(visual_id, role=query.get("role", [None])[0])
        except (TypeError, ValueError, KeyError) as exc:
            return 404, _response("error", None, str(exc))
        return 200, _response("ok", data)
    if parsed.path == "/v1/ontology/team-aliases" and method.upper() == "POST":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "team_id", "alias", "term_id", "reason", "source_refs", "approval_ref")
        missing = [field for field in required if not body.get(field)]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="manage_ontology", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            record = TeamOntologyService(tenant).lock_alias(team_id=body["team_id"], alias=body["alias"], term_id=body["term_id"], owner=principal.subject, reason=body["reason"], source_refs=body["source_refs"], approval_ref=body["approval_ref"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", record)
    if parsed.path == "/v1/playbook/workspace" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _playbook_workspace(service, organization_id=principal.organization_id, actor=principal.subject).workspace(include_rejected=query.get("include_rejected", ["false"])[0].lower() == "true"))
    if parsed.path.startswith("/v1/playbook/drafts/") and parsed.path.endswith("/role-view") and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        role = query.get("role", [""])[0]
        play_id = parsed.path.split("/")[4]
        if not organization_id or not role:
            return 400, _response("error", None, "organization_id and role query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_playbook", organization_id=organization_id)
        if denial:
            return denial
        try:
            view = _playbook_workspace(service, organization_id=principal.organization_id, actor=principal.subject).role_view(play_id=play_id, role=role)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", view)
    if parsed.path == "/v1/playbook/organization-corpus" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_team_context", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "corpora": tenant.list("organization_play_corpora"), "production_implementation_allowed": False})
    if parsed.path == "/v1/playbook/organization-corpus" and method.upper() == "POST":
        required = ("organization_id", "corpus_id", "team_context", "season", "plays", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            corpus = build_organization_play_corpus(corpus_id=body["corpus_id"], organization_id=principal.organization_id, team_context=body["team_context"], season=body["season"], plays=body["plays"], source_refs=body["source_refs"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if corpus["status"] != "under_review":
            return 422, _response("invalid", corpus, "Organization play corpus was rejected by the compiler")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_play_corpora", corpus["id"], corpus, actor=principal.subject, reason="organization_play_corpus_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/playbook/organization-corpus/approve" and method.upper() == "POST":
        required = ("organization_id", "corpus_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate an organization play corpus")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        corpus = tenant.get("organization_play_corpora", body["corpus_id"])
        if corpus is None:
            return 404, _response("error", None, "Organization play corpus was not found")
        approved = approve_organization_play_corpus(corpus=corpus, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization play corpus approval was not accepted")
        saved = tenant.put("organization_play_corpora", approved["id"], approved, actor=principal.subject, reason="organization_play_corpus_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/playbook/drafts":
        required = ("organization_id", "play", "play_family_id", "install_level", "checks", "situational_variants", "opponent_notes", "coaching_notes", "dependencies")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            draft = _playbook_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_draft(play=body["play"], play_family_id=body["play_family_id"], install_level=body["install_level"], checks=body["checks"], situational_variants=body["situational_variants"], opponent_notes=body["opponent_notes"], coaching_notes=body["coaching_notes"], dependencies=body["dependencies"], actor=principal.subject)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if draft.get("status") == "draft" else 422, _response("ok" if draft.get("status") == "draft" else "invalid", draft)
    if parsed.path == "/v1/playbook/drafts/request-approval":
        required = ("organization_id", "play_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _playbook_workspace(service, organization_id=principal.organization_id, actor=principal.subject).request_approval(play_id=body["play_id"], requester=principal.subject, decision_ref=body["decision_ref"])
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", result)
    if parsed.path == "/v1/playbook/drafts/approve":
        required = ("organization_id", "play_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="lock_artifact", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = _playbook_workspace(service, organization_id=principal.organization_id, actor=principal.subject).approve(play_id=body["play_id"], approver=principal.subject, decision_ref=body["decision_ref"])
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200 if result.get("status") == "locked" else 422, _response("ok" if result.get("status") == "locked" else "invalid", result)
    if parsed.path == "/v1/plays/compile":
        result = compile_play(body)
        payload = {"valid": result.valid, "normalized_play": result.normalized_play, "issues": [issue.__dict__ for issue in result.issues]}
        return (200 if result.valid else 422), _response("ok" if result.valid else "invalid", payload, None if result.valid else "Play compiler rejected the record")
    if parsed.path == "/v1/workflows/core-play":
        if service is None:
            service = FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("play", "role", "drill", "decision_ref", "organization_id")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = service.create_core_play_slice(
                play=body["play"], role=body["role"], drill=body["drill"], actor=principal.subject, decision_ref=body["decision_ref"], organization_id=principal.organization_id
            )
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", package)
    if parsed.path == "/v1/film/observations":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        organization_id = body.get("organization_id")
        if not organization_id or not body.get("observation"):
            return 400, _response("error", None, "organization_id and observation are required")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=organization_id)
        if denial:
            return denial
        observation = dict(body["observation"])
        observation["organization_id"] = principal.organization_id
        try:
            saved = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).save_observation(observation, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", saved)
    if parsed.path == "/v1/film/annotation-sessions":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "session_id", "clip_id", "allowed_domains", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            session = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).create_annotation_session(session_id=body["session_id"], clip_id=body["clip_id"], annotator=principal.subject, allowed_domains=body["allowed_domains"], source_refs=body["source_refs"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if session["status"] == "open" else 422, _response("ok" if session["status"] == "open" else "invalid", session)
    if parsed.path == "/v1/film/playlists":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "playlist_id", "name", "purpose", "clip_ids", "filters", "access_roles")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            playlist = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).create_playlist(playlist_id=body["playlist_id"], name=body["name"], purpose=body["purpose"], clip_ids=body["clip_ids"], filters=body["filters"], owner=principal.subject, access_roles=body["access_roles"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if playlist["status"] == "draft" else 422, _response("ok" if playlist["status"] == "draft" else "invalid", playlist)
    if parsed.path == "/v1/film/voice-notes":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "note_id", "clip_id", "frame_seconds", "mime_type", "audio_data", "transcript")
        missing = [field for field in required if field not in body or body[field] in (None, "")]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            note = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).create_voice_note(note_id=body["note_id"], clip_id=body["clip_id"], frame_seconds=float(body["frame_seconds"]), mime_type=body["mime_type"], audio_data=body["audio_data"], transcript=body["transcript"], access_roles=body.get("access_roles", []), author=principal.subject, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", note)
    if parsed.path.startswith("/v1/film/annotation-sessions/") and parsed.path.endswith("/annotations"):
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or not body.get("observation"):
            return 400, _response("error", None, "organization_id and observation are required")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        session_id = parsed.path.split("/")[-2]
        try:
            session = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).append_session_annotation(session_id=session_id, observation=body["observation"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", session)
    if parsed.path == "/v1/media/assets":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "file_path", "asset_id", "duration_seconds", "source", "captured_at", "team_context", "allowed_roots")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            asset = _media_service(service, organization_id=principal.organization_id, actor=principal.subject).register_asset(file_path=body["file_path"], asset_id=body["asset_id"], duration_seconds=body["duration_seconds"], source=body["source"], captured_at=body["captured_at"], team_context=body["team_context"], allowed_roots=body["allowed_roots"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError, OSError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if asset["status"] == "registered" else 422, _response("ok" if asset["status"] == "registered" else "invalid", asset)
    if parsed.path == "/v1/media/clips":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "clip_id", "asset_id", "start_seconds", "end_seconds", "team", "opponent", "situation")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            clip = _media_service(service, organization_id=principal.organization_id, actor=principal.subject).create_clip(clip_id=body["clip_id"], asset_id=body["asset_id"], start_seconds=body["start_seconds"], end_seconds=body["end_seconds"], team=body["team"], opponent=body["opponent"], situation=body["situation"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if clip["status"] == "ready" else 422, _response("ok" if clip["status"] == "ready" else "invalid", clip)
    if parsed.path == "/v1/media/worker/run":
        required = ("organization_id", "worker_id", "allowed_roots")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="run_media_worker", organization_id=body["organization_id"])
        if denial:
            return denial
        result = MediaWorkerRunner(TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)).run_batch(worker_id=body["worker_id"], actor=principal.subject, allowed_roots=body["allowed_roots"], max_jobs=body.get("max_jobs", 10))
        return 200 if result["status"] in {"completed", "partial_failure"} else 422, _response("ok" if result["status"] in {"completed", "partial_failure"} else "invalid", result)
    if parsed.path == "/v1/media/jobs":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "job_id", "asset_id", "operation", "payload")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            job = _media_jobs(service, organization_id=principal.organization_id, actor=principal.subject).create_job(job_id=body["job_id"], asset_id=body["asset_id"], operation=body["operation"], payload=body["payload"], requested_by=principal.subject, max_attempts=body.get("max_attempts", 3))
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if job["status"] == "queued" else 422, _response("ok" if job["status"] == "queued" else "invalid", job)
    if parsed.path.startswith("/v1/media/jobs/"):
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        parts = parsed.path.strip("/").split("/")
        job_id = parts[3] if len(parts) > 3 else ""
        action_name = parts[4] if len(parts) > 4 else ""
        if method.upper() == "GET" and job_id and not action_name:
            organization_id = query.get("organization_id", [""])[0]
            if not organization_id:
                return 400, _response("error", None, "organization_id query parameter is required")
            principal, denial = _authenticated(headers, action="read_film", organization_id=organization_id)
            if denial:
                return denial
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            job = tenant.get("media_processing_jobs", job_id)
            if job is None:
                return 404, _response("error", None, "Unknown media job")
            outputs = [record for record in tenant.list("media_processing_outputs") if record.get("job_id") == job_id]
            batches = [record for record in tenant.list("media_worker_batches") if any(item.get("job_id") == job_id for item in record.get("results", []))]
            return 200, _response("ok", {"organization_id": principal.organization_id, "job": job, "outputs": outputs, "batches": batches})
        if not job_id or action_name not in {"claim", "complete", "fail"}:
            return 404, _response("error", None, "Unknown media job route")
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        jobs = _media_jobs(service, organization_id=principal.organization_id, actor=principal.subject)
        try:
            if action_name == "claim":
                if not body.get("worker_id"):
                    return 400, _response("error", None, "worker_id is required")
                job = jobs.claim_job(job_id=job_id, worker_id=body["worker_id"])
            elif action_name == "complete":
                job = jobs.complete_job(job_id=job_id, worker_id=body.get("worker_id", ""), output_refs=body.get("output_refs", []))
            else:
                job = jobs.fail_job(job_id=job_id, worker_id=body.get("worker_id", ""), error_code=body.get("error_code", "UNKNOWN"), error_message=body.get("error_message", "unspecified failure"))
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", job)
    if parsed.path == "/v1/integrations/provider-adapter" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_provider_adapter", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "registrations": tenant.list("provider_adapter_registrations"), "production_implementation_allowed": False})
    if parsed.path == "/v1/integrations/provider-adapter" and method.upper() == "POST":
        required = ("organization_id", "adapter_id", "provider", "capabilities", "credential_ref", "healthcheck_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_provider_adapter", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            registration = build_provider_adapter_registration(adapter_id=body["adapter_id"], organization_id=principal.organization_id, provider=body["provider"], capabilities=body["capabilities"], credential_ref=body["credential_ref"], healthcheck_ref=body["healthcheck_ref"], owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if registration["status"] != "under_review":
            return 422, _response("invalid", registration, "Provider adapter registration was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("provider_adapter_registrations", registration["id"], registration, actor=principal.subject, reason="provider_adapter_registration_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/integrations/provider-adapter/approve" and method.upper() == "POST":
        required = ("organization_id", "adapter_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate a provider adapter registration")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        registration = tenant.get("provider_adapter_registrations", body["adapter_id"])
        if registration is None:
            return 404, _response("error", None, "Provider adapter registration was not found")
        approved = approve_provider_adapter_registration(registration=registration, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Provider adapter approval was not accepted")
        saved = tenant.put("provider_adapter_registrations", approved["id"], approved, actor=principal.subject, reason="provider_adapter_registration_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/sources/authorized":
        required = ("organization_id", "authorization", "tier", "kind", "captured_at", "effective_period", "citation_location")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="manage_sources", organization_id=body["organization_id"])
        if denial:
            return denial
        authorization = body["authorization"]
        if not isinstance(authorization, dict) or authorization.get("organization_id") != principal.organization_id:
            return 422, _response("invalid", None, "Authorization organization scope must match the authenticated organization")
        authorization_result = validate_source_authorization(authorization=authorization, environment="validation")
        if authorization_result["status"] != "authorized":
            return 422, _response("invalid", {"authorization": authorization_result}, "Source authorization evidence is not valid")
        try:
            source = _sources(service, organization_id=principal.organization_id, actor=principal.subject).register_source(source_id=authorization["source_id"], tier=body["tier"], kind=body["kind"], uri=authorization["uri"], captured_at=body["captured_at"], effective_period=body["effective_period"], citation_location=body["citation_location"], owner=principal.subject, allowed_domains=authorization["allowed_domains"], freshness_days=body.get("freshness_days", 7), actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        if source.get("status") != "registered":
            return 422, _response("invalid", source, "Authorized source registration failed")
        source["authorization"] = authorization
        source["authorization_status"] = "authorized"
        saved = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject).put("knowledge_sources", source["id"], source, actor=principal.subject, reason="authorized_source_registration_evidence_attached")
        return 201, _response("ok", {"source": saved, "authorization": authorization_result, "network_fetch_performed": False, "external_state_changed": False})
    if parsed.path == "/v1/sources":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "source_id", "tier", "kind", "uri", "captured_at", "effective_period", "citation_location", "allowed_domains")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="manage_sources", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            source = _sources(service, organization_id=principal.organization_id, actor=principal.subject).register_source(source_id=body["source_id"], tier=body["tier"], kind=body["kind"], uri=body["uri"], captured_at=body["captured_at"], effective_period=body["effective_period"], citation_location=body["citation_location"], owner=principal.subject, allowed_domains=body["allowed_domains"], freshness_days=body.get("freshness_days", 7), actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if source["status"] == "registered" else 422, _response("ok" if source["status"] == "registered" else "invalid", source)
    if parsed.path == "/v1/player/assignments":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "assignment_id", "player_id", "title", "assignment_type", "artifact_id", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_practice", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            assignment = _player_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_assignment(assignment_id=body["assignment_id"], player_id=body["player_id"], title=body["title"], assignment_type=body["assignment_type"], artifact_id=body["artifact_id"], due_date=body.get("due_date"), owner=principal.subject, source_refs=body["source_refs"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if assignment["status"] == "assigned" else 422, _response("ok" if assignment["status"] == "assigned" else "invalid", assignment)
    if parsed.path == "/v1/performance/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_performance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_performance_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/performance/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "season", "batch_id", "records", "source_manifest", "readiness_summaries")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_performance_support", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_performance(package_id=body["package_id"], organization_id=principal.organization_id, season=body["season"], batch_id=body["batch_id"], records=body["records"], source_manifest=body["source_manifest"], readiness_summaries=body["readiness_summaries"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization performance package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_performance_packages", package["id"], package, actor=principal.subject, reason="organization_performance_package_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/performance/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate performance packages")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_performance_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization performance package was not found")
        approved = approve_organization_performance(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization performance approval was not accepted")
        saved = tenant.put("organization_performance_packages", approved["id"], approved, actor=principal.subject, reason="organization_performance_package_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/performance/batches":
        required = ("organization_id", "provider", "batch_id", "records", "source_manifest")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_performance_support", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            result = ingest_provider_batch(organization_id=principal.organization_id, provider=body["provider"], batch_id=body["batch_id"], records=body["records"], source_manifest=body["source_manifest"], actor=principal.subject)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if result["status"] in {"accepted", "partial"} else 422, _response("ok" if result["status"] in {"accepted", "partial"} else "invalid", result)
    if parsed.path == "/v1/practice/resources/preflight":
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="draft_practice", organization_id=body["organization_id"])
        if denial:
            return denial
        required = ("integration_id", "provider", "practice_id", "schedule", "availability")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        try:
            result = plan_resource_integration(organization_id=principal.organization_id, integration_id=body["integration_id"], provider=body["provider"], practice_id=body["practice_id"], schedule=body["schedule"], availability=body["availability"])
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200 if result["status"] == "ready" else 422, _response("ok" if result["status"] == "ready" else "invalid", result)
    if parsed.path == "/v1/practice/drill-validation" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_practice", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_drill_validations"), "approval_required": True})
    if parsed.path == "/v1/practice/drill-validation" and method.upper() == "POST":
        required = ("organization_id", "validation_id", "season", "position", "selected_drill_ids", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_practice", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_drill_validation(validation_id=body["validation_id"], organization_id=principal.organization_id, season=body["season"], position=body["position"], selected_drill_ids=body["selected_drill_ids"], source_refs=body["source_refs"], validator=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization drill validation package is not valid")
        saved = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject).put("organization_drill_validations", package["id"], package, actor=principal.subject, reason="organization_drill_validation_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/practice/drill-validation/approve" and method.upper() == "POST":
        required = ("organization_id", "validation_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate an organization drill package")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_drill_validations", body["validation_id"])
        if package is None:
            return 404, _response("error", None, "Organization drill validation package was not found")
        approved = approve_organization_drill_validation(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization drill validation approval was not accepted")
        saved = tenant.put("organization_drill_validations", approved["id"], approved, actor=principal.subject, reason="organization_drill_validation_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/practice/attendance" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        practice_id = query.get("practice_id", [None])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_practice", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _practice_attendance(service, organization_id=principal.organization_id, actor=principal.subject).workspace(practice_id=practice_id))
    if parsed.path == "/v1/practice/attendance" and method.upper() == "POST":
        required = ("organization_id", "attendance_id", "practice_id", "player_id", "status", "recorded_by")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="record_practice_attendance", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            record = _practice_attendance(service, organization_id=principal.organization_id, actor=principal.subject).record(
                attendance_id=body["attendance_id"], practice_id=body["practice_id"], player_id=body["player_id"], status=body["status"],
                recorded_by=principal.subject, recorded_at=body.get("recorded_at"), period_ids=body.get("period_ids", []),
                minutes_available=body.get("minutes_available"), note=body.get("note", ""), source_refs=body.get("source_refs", []),
            )
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if record.get("status") != "invalid" else 422, _response("ok" if record.get("status") != "invalid" else "invalid", record)
    if parsed.path == "/v1/practice/plans":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "practice_id", "team_context", "season_phase", "week_context", "objective", "opponent_priorities", "periods", "staff_available", "facility_constraints", "load_controls", "restrictions")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_practice", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            plan = _practice_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_plan(practice_id=body["practice_id"], team_context=body["team_context"], season_phase=body["season_phase"], week_context=body["week_context"], objective=body["objective"], opponent_priorities=body["opponent_priorities"], periods=body["periods"], staff_available=body["staff_available"], facility_constraints=body["facility_constraints"], load_controls=body["load_controls"], restrictions=body["restrictions"], roster_ids=body.get("roster_ids", []), install_items=body.get("install_items", []), attendance_policy=body.get("attendance_policy"), practice_card_preferences=body.get("practice_card_preferences", {}), actor=principal.subject, resource_schedule=body.get("resource_schedule"), resource_availability=body.get("resource_availability"))
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if plan["status"] == "draft" else 422, _response("ok" if plan["status"] == "draft" else "invalid", plan)
    if parsed.path == "/v1/player-development/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        player_id = query.get("player_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        authorization = (headers or {}).get("Authorization", "")
        try:
            secret = resolve_auth_secret()
            principal = verify_token(authorization.removeprefix("Bearer ").strip(), secret=secret) if authorization.startswith("Bearer ") and secret else None
        except ValueError:
            principal = None
        if principal is not None and principal.role == "player":
            if player_id != principal.subject:
                return 403, _response("error", None, "Players may read only their own development record")
            principal, denial = _authenticated(headers, action="read_own_development", organization_id=organization_id)
        else:
            principal, denial = _authenticated(headers, action="read_player_development", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        packages = tenant.list("organization_player_development_packages")
        if principal.role == "player":
            packages = [{**package, "players": [player for player in package.get("players", []) if player.get("player_id") == principal.subject]} for package in packages]
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": packages, "production_implementation_allowed": False})
    if parsed.path == "/v1/player-development/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "team_context", "season", "players")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_player_development", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_player_development(package_id=body["package_id"], organization_id=principal.organization_id, team_context=body["team_context"], season=body["season"], players=body["players"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization player development package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_player_development_packages", package["id"], package, actor=principal.subject, reason="organization_player_development_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/player-development/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate player development")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_player_development_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization player development package was not found")
        approved = approve_organization_player_development(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization player development approval was not accepted")
        saved = tenant.put("organization_player_development_packages", approved["id"], approved, actor=principal.subject, reason="organization_player_development_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/staff/organization-review" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_staff", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_staff_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/staff/organization-review" and method.upper() == "POST":
        required = ("organization_id", "package_id", "team_context", "season", "staff", "evaluations")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_staff", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_staff_package(package_id=body["package_id"], organization_id=principal.organization_id, team_context=body["team_context"], season=body["season"], staff=body["staff"], evaluations=body["evaluations"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization staff package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_staff_packages", package["id"], package, actor=principal.subject, reason="organization_staff_package_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/staff/organization-review/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization staff records")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_staff_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization staff package was not found")
        approved = approve_organization_staff_package(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization staff package approval was not accepted")
        saved = tenant.put("organization_staff_packages", approved["id"], approved, actor=principal.subject, reason="organization_staff_package_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/media/organization-review" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_media_review", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_media_review_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/media/organization-review" and method.upper() == "POST":
        required = ("organization_id", "package_id", "season", "assets", "clips", "playlists", "observations", "qa_id")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_media_review", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_media_review(package_id=body["package_id"], organization_id=principal.organization_id, season=body["season"], assets=body["assets"], clips=body["clips"], playlists=body["playlists"], observations=body["observations"], qa_id=body["qa_id"], reviewer=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization media review was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_media_review_packages", package["id"], package, actor=principal.subject, reason="organization_media_review_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/media/organization-review/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization media review")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_media_review_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization media review was not found")
        approved = approve_organization_media_review(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization media review approval was not accepted")
        saved = tenant.put("organization_media_review_packages", approved["id"], approved, actor=principal.subject, reason="organization_media_review_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/special-teams/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_special_teams", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_special_teams_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/special-teams/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "team_context", "season", "assignments", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_special_teams", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_special_teams(package_id=body["package_id"], organization_id=principal.organization_id, team_context=body["team_context"], season=body["season"], assignments=body["assignments"], source_refs=body["source_refs"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization special-teams package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_special_teams_packages", package["id"], package, actor=principal.subject, reason="organization_special_teams_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/special-teams/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate special-teams personnel")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_special_teams_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization special-teams package was not found")
        approved = approve_organization_special_teams(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization special-teams approval was not accepted")
        saved = tenant.put("organization_special_teams_packages", approved["id"], approved, actor=principal.subject, reason="organization_special_teams_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/schemes/organization-doctrine" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_scheme", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_doctrine_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/schemes/organization-doctrine" and method.upper() == "POST":
        required = ("organization_id", "doctrine_id", "team_context", "season", "scheme_family_ids", "special_teams_unit_ids", "source_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_scheme", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_doctrine(doctrine_id=body["doctrine_id"], organization_id=principal.organization_id, team_context=body["team_context"], season=body["season"], scheme_family_ids=body["scheme_family_ids"], special_teams_unit_ids=body["special_teams_unit_ids"], source_refs=body["source_refs"], compiler=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization doctrine package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_doctrine_packages", package["id"], package, actor=principal.subject, reason="organization_doctrine_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/schemes/organization-doctrine/approve" and method.upper() == "POST":
        required = ("organization_id", "doctrine_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization doctrine")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_doctrine_packages", body["doctrine_id"])
        if package is None:
            return 404, _response("error", None, "Organization doctrine package was not found")
        approved = approve_organization_doctrine(doctrine=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization doctrine approval was not accepted")
        saved = tenant.put("organization_doctrine_packages", approved["id"], approved, actor=principal.subject, reason="organization_doctrine_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/schemes":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or not body.get("scheme"):
            return 400, _response("error", None, "organization_id and scheme are required")
        principal, denial = _authenticated(headers, action="draft_scheme", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            scheme = _scheme_workspace(service, organization_id=principal.organization_id, actor=principal.subject).save_scheme(scheme=body["scheme"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if scheme["status"] == "validated" else 422, _response("ok" if scheme["status"] == "validated" else "invalid", scheme)
    if parsed.path == "/v1/analytics/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_analytics", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_analytics_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/analytics/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "season", "source_refs", "observations", "reports")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_analytics", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_analytics_package(package_id=body["package_id"], organization_id=principal.organization_id, season=body["season"], source_refs=body["source_refs"], observations=body["observations"], reports=body["reports"], analyst=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization analytics package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_analytics_packages", package["id"], package, actor=principal.subject, reason="organization_analytics_package_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/analytics/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization analytics")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_analytics_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization analytics package was not found")
        approved = approve_organization_analytics_package(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization analytics approval was not accepted")
        saved = tenant.put("organization_analytics_packages", approved["id"], approved, actor=principal.subject, reason="organization_analytics_package_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/analytics/outcomes" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        intended_record_id = query.get("intended_record_id", [None])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_analytics", organization_id=organization_id)
        if denial:
            return denial
        return 200, _response("ok", _analytics_outcomes(service, organization_id=principal.organization_id, actor=principal.subject).workspace(intended_record_id=intended_record_id))
    if parsed.path == "/v1/analytics/outcomes" and method.upper() == "POST":
        required = ("organization_id", "outcome_id", "intended_record_type", "intended_record_id", "actual_result", "success_count", "sample_size", "context", "evidence_refs")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="record_outcome", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            record = _analytics_outcomes(service, organization_id=principal.organization_id, actor=principal.subject).record(
                outcome_id=body["outcome_id"], intended_record_type=body["intended_record_type"], intended_record_id=body["intended_record_id"],
                actual_result=body["actual_result"], success_count=body["success_count"], sample_size=body["sample_size"], context=body["context"],
                evidence_refs=body["evidence_refs"], recorded_by=principal.subject, linked_play_id=body.get("linked_play_id"), linked_assignment_id=body.get("linked_assignment_id"), teaching_step_id=body.get("teaching_step_id"), responsibility_phase=body.get("responsibility_phase"), practice_id=body.get("practice_id"),
                film_observation_ids=body.get("film_observation_ids", []), game_plan_id=body.get("game_plan_id"), notes=body.get("notes", ""),
            )
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if record.get("status") == "recorded" else 422, _response("ok" if record.get("status") == "recorded" else "invalid", record)
    if parsed.path == "/v1/analytics/batches":
        required = ("organization_id", "provider", "batch_id", "records", "source_manifest")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="create_metric", organization_id=body["organization_id"])
        if denial:
            return denial
        result = calculate_provider_batch(organization_id=principal.organization_id, provider=body["provider"], batch_id=body["batch_id"], records=body["records"], source_manifest=body["source_manifest"], actor=principal.subject)
        if result["status"] in {"accepted", "partial"}:
            tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
            for observation in result["accepted"]:
                tenant.put("metric_observations", observation["id"], observation, actor=principal.subject, reason="analytics_provider_batch_observation_saved")
        return 201 if result["status"] in {"accepted", "partial"} else 422, _response("ok" if result["status"] in {"accepted", "partial"} else "invalid", result)
    if parsed.path == "/v1/analytics/reports":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "report_id", "audience", "metric_observations", "context", "caveats")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_analytics", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            report = _analytics_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_report(report_id=body["report_id"], audience=body["audience"], metric_observations=body["metric_observations"], context=body["context"], caveats=body["caveats"], analyst=principal.subject, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if report["status"] == "draft" else 422, _response("ok" if report["status"] == "draft" else "invalid", report)
    if parsed.path == "/v1/scouting/organization-package" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_scouting", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"organization_id": principal.organization_id, "packages": tenant.list("organization_scouting_packages"), "production_implementation_allowed": False})
    if parsed.path == "/v1/scouting/organization-package" and method.upper() == "POST":
        required = ("organization_id", "package_id", "opponent", "season", "source_refs", "profile", "reports", "matchups", "evolutions")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="draft_scouting", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = build_organization_scouting_package(package_id=body["package_id"], organization_id=principal.organization_id, opponent=body["opponent"], season=body["season"], source_refs=body["source_refs"], profile=body["profile"], reports=body["reports"], matchups=body["matchups"], evolutions=body["evolutions"], analyst=principal.subject, owner_decision_ref=body.get("owner_decision_ref"))
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        if package["status"] != "under_review":
            return 422, _response("invalid", package, "Organization scouting package was rejected")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        saved = tenant.put("organization_scouting_packages", package["id"], package, actor=principal.subject, reason="organization_scouting_package_submitted")
        return 201, _response("ok", saved)
    if parsed.path == "/v1/scouting/organization-package/approve" and method.upper() == "POST":
        required = ("organization_id", "package_id", "decision_ref")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        if principal.role != "program_owner":
            return 403, _response("error", None, "Only a program_owner may validate organization scouting")
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        package = tenant.get("organization_scouting_packages", body["package_id"])
        if package is None:
            return 404, _response("error", None, "Organization scouting package was not found")
        approved = approve_organization_scouting_package(package=package, approver=principal.subject, approver_role=principal.role, decision_ref=body["decision_ref"])
        if approved.get("status") != "validated":
            return 422, _response("invalid", approved, "Organization scouting approval was not accepted")
        saved = tenant.put("organization_scouting_packages", approved["id"], approved, actor=principal.subject, reason="organization_scouting_package_owner_approved")
        return 200, _response("ok", saved)
    if parsed.path == "/v1/scouting/reports":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or not body.get("report"):
            return 400, _response("error", None, "organization_id and report are required")
        principal, denial = _authenticated(headers, action="draft_scouting", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            raw = body["report"]
            report = build_situational_scouting_report(report_id=raw.get("id", ""), opponent=raw.get("opponent", ""), situation=raw.get("situation", {}), claims=raw.get("claims", []), sample_size=raw.get("sample_size", 0), source_refs=raw.get("source_refs", []), analyst=principal.subject)
            report = _scouting_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_report(report=report, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if report["status"] == "under_review" else 422, _response("ok" if report["status"] == "under_review" else "invalid", report)
    if parsed.path == "/v1/playbook/visuals":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or not body.get("visual"):
            return 400, _response("error", None, "organization_id and visual are required")
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            visual = _visual_workspace(service, organization_id=principal.organization_id, actor=principal.subject).save_visual(body["visual"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if visual["status"] == "renderable" else 422, _response("ok" if visual["status"] == "renderable" else "invalid", visual)
    if parsed.path.startswith("/v1/playbook/visuals/") and parsed.path.endswith("/what-if"):
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body or not body.get("simulation_id") or not body.get("adjustment"):
            return 400, _response("error", None, "organization_id, simulation_id, and adjustment are required")
        principal, denial = _authenticated(headers, action="draft_play", organization_id=body["organization_id"])
        if denial:
            return denial
        visual_id = parsed.path.split("/")[-2]
        try:
            scenario = _visual_workspace(service, organization_id=principal.organization_id, actor=principal.subject).create_what_if(visual_id=visual_id, simulation_id=body["simulation_id"], adjustment=body["adjustment"], requester_role=principal.role, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if scenario.get("status") == "scenario_ready" else 422, _response("ok" if scenario.get("status") == "scenario_ready" else "invalid", scenario)
    if parsed.path.startswith("/v1/sources/") and parsed.path.endswith("/refresh"):
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        if "organization_id" not in body:
            return 400, _response("error", None, "organization_id is required")
        principal, denial = _authenticated(headers, action="refresh_source", organization_id=body["organization_id"])
        if denial:
            return denial
        source_id = parsed.path.split("/")[-2]
        try:
            refresh = _sources(service, organization_id=principal.organization_id, actor=principal.subject).refresh_source(source_id=source_id, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok" if refresh["status"] == "refreshed" else "failed", refresh)
    if parsed.path == "/v1/film/quizzes":
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "quiz_id", "title", "role", "clip_ids", "questions")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="draft_practice", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            quiz = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).create_quiz(quiz_id=body["quiz_id"], title=body["title"], role=body["role"], clip_ids=body["clip_ids"], questions=body["questions"], owner=principal.subject, actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if quiz["status"] != "invalid" else 422, _response("ok" if quiz["status"] != "invalid" else "invalid", quiz)
    if parsed.path.startswith("/v1/film/quizzes/") and parsed.path.endswith("/attempts"):
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("organization_id", "attempt_id", "participant", "answers")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        quiz_id = parsed.path.split("/")[-2]
        principal, denial = _authenticated(headers, action="read_film", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            attempt = _film_service(service, organization_id=principal.organization_id, actor=principal.subject).submit_quiz(attempt_id=body["attempt_id"], quiz_id=quiz_id, participant=body["participant"], answers=body["answers"], actor=principal.subject)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if attempt["status"] != "invalid" else 422, _response("ok" if attempt["status"] != "invalid" else "invalid", attempt)
    if parsed.path.startswith("/v1/workflows/core-play/") and parsed.path.endswith("/approve"):
        if service is None:
            service = FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        play_id = parsed.path.split("/")[-2]
        if "decision_ref" not in body or "organization_id" not in body:
            return 400, _response("error", None, "decision_ref and organization_id are required")
        principal, denial = _authenticated(headers, action="approve_high_impact", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = service.approve_core_play_slice(play_id=play_id, approver=principal.subject, decision_ref=body["decision_ref"], organization_id=principal.organization_id)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200 if package["status"] == "approved" else 422, _response("ok" if package["status"] == "approved" else "rejected", package)
    if parsed.path == "/v1/workflows/evidence-intelligence":
        if service is None:
            service = FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("asset", "clip", "observation", "scouting_report", "metric_observation", "analyst", "qa_reviewer", "organization_id")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="create_scouting_claim", organization_id=body["organization_id"])
        if denial:
            return denial
        try:
            package = service.create_evidence_intelligence_slice(asset=body["asset"], clip=body["clip"], observation=body["observation"], scouting_report=body["scouting_report"], metric_observation=body["metric_observation"], analyst=principal.subject, qa_reviewer=body["qa_reviewer"], organization_id=principal.organization_id)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201, _response("ok", package)
    if parsed.path == "/v1/workflows/weekly-delivery":
        if service is None:
            service = FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        required = ("game_plan", "rule_recommendation", "eval_result", "capability_ids", "feature_gates", "actor", "organization_id")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        principal, denial = _authenticated(headers, action="review_recommendation", organization_id=body["organization_id"])
        if denial:
            return denial
        approval = principal.subject if principal.role == "program_owner" and body.get("human_approval") else None
        try:
            package = service.create_weekly_delivery_package(game_plan=body["game_plan"], rule_recommendation=body["rule_recommendation"], eval_result=body["eval_result"], capability_ids=body["capability_ids"], feature_gates=body["feature_gates"], actor=principal.subject, human_approval=approval, organization_id=principal.organization_id)
        except (TypeError, ValueError, KeyError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if package["status"] == "approved" else 202, _response("ok" if package["status"] == "approved" else "blocked", package)
    if parsed.path == "/v1/agents/runs" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        if not organization_id:
            return 400, _response("error", None, "organization_id query parameter is required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        return 200, _response("ok", {"runs": tenant.list("agent_runs"), "production_implementation_allowed": False, "external_provider_called": False})
    if parsed.path == "/v1/organizations/population-readiness" and method.upper() == "GET":
        organization_id = query.get("organization_id", [""])[0]
        season = query.get("season", [""])[0]
        if not organization_id or not season:
            return 400, _response("error", None, "organization_id and season query parameters are required")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="read_governance", organization_id=organization_id)
        if denial:
            return denial
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            readiness = build_organization_population_readiness(tenant=tenant, organization_id=principal.organization_id, season=season)
        except (TypeError, ValueError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 200, _response("ok", readiness)
    if parsed.path == "/v1/agents/runs" and method.upper() == "POST":
        required = ("organization_id", "run_id", "agent_id", "family", "capability", "workflow_id", "payload", "local_validation")
        missing = [field for field in required if field not in body]
        if missing:
            return 400, _response("error", None, f"Missing required fields: {', '.join(missing)}")
        if body.get("local_validation") is not True:
            return 403, _response("error", None, "Agent API dispatch is restricted to explicit local_validation=true")
        service = service or FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "core-slice-state.json"))
        principal, denial = _authenticated(headers, action="run_agent_validation", organization_id=body["organization_id"])
        if denial:
            return denial
        root = Path(__file__).resolve().parents[2]
        tenant = TenantRepository(service.repository, organization_id=principal.organization_id, actor=principal.subject)
        try:
            bible = load_agent_bible(root / "agents" / "agent-organization-bible.json")
            runtime = AgentRuntime(tenant)
            runtime.register_bible(bible)
            register_local_validation_adapters(runtime, bible, activate=True)
            active = runtime.activate(agent_id=body["agent_id"], capability=body["capability"])
            if active.get("status") != "active":
                return 422, _response("invalid", active, "Requested agent capability could not be activated for local validation")
            result = runtime.dispatch(run_id=body["run_id"], from_agent="AGT-001", family=body["family"], capability=body["capability"], workflow_id=body["workflow_id"], payload=body["payload"], requested_permissions=set(body.get("requested_permissions", [])), human_review_required=True)
        except (TypeError, ValueError, KeyError, PermissionError) as exc:
            return 422, _response("invalid", None, str(exc))
        return 201 if result.get("status") == "completed" else 422, _response("ok" if result.get("status") == "completed" else "blocked", {"run": result, "local_validation_only": True, "external_provider_called": False, "canonical_write_performed": False, "production_implementation_allowed": False})
    return 404, _response("error", None, "Route not found")
