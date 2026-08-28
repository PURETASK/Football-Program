"""NFL Football Intelligence & Development OS foundation package."""

from .play_compiler import CompileIssue, CompileResult, compile_play
from .player_learning import build_player_lesson
from .evidence import qualify_claim, validate_evidence
from .game_plan import build_game_plan_options
from .practice import build_practice_plan
from .scouting import build_tendency_record
from .agent_contracts import create_handoff
from .analytics import build_metric_observation
from .performance import build_performance_note
from .rules import answer_rule_request, validate_rule_source
from .film import build_film_tag, build_self_scout_report
from .playbook_view import build_playbook_view
from .repository import JsonRepository
from .service import FootballIntelligenceService
from .scheme import build_countermeasure, build_scheme, validate_scheme
from .compatibility import build_red_team_matrix, check_play_scheme_compatibility
from .ontology import OntologyResolver
from .ontology_bible import validate_ontology_bible
from .team_context import TeamContextRegistry
from .evals import run_minimum_eval_suite
from .access import authorize
from .media import create_film_clip, register_film_asset
from .sqlite_repository import SqliteRepository
from .database_operations import fingerprint_sqlite_database
from .workflows import run_player_development_loop, run_scheme_selection, run_weekly_team_loop
from .development import build_coach_mastery_plan, build_development_plan, build_mastery_record
from .knowledge import build_knowledge_claim, validate_source
from .game_management import build_game_decision, build_game_situation
from .special_teams import build_special_teams_plan
from .athlete_performance import build_performance_observation, build_readiness_summary
from .organization import build_organization_context, resolve_person
from .organization_terminology import resolve_organization_term, validate_organization_terminology
from .api import handle_request
from .change_control import approve_change_request, build_change_request, build_decision_record
from .agent_registry import AgentRegistry
from .completion import build_completion_gate, close_completion_gate
from .delivery import build_release_candidate, evaluate_delivery_wave
from .stage0 import evaluate_stage0_exit
from .architecture import validate_system_architecture
from .coach_development import build_coaching_staff_architecture, build_coach_development_pathway, evaluate_coach_performance
from .scheme_bible import validate_scheme_bible, validate_scheme_dossier
from .special_teams_bible import validate_special_teams_bible, validate_special_teams_unit
from .playbook_architecture import approve_play, build_extended_play, build_play_family, extract_role_play_spec, request_play_approval, validate_play_spec
from .visual_playbook import build_animation_timeline, build_visual_play, simulate_what_if, validate_visual_play
from .drill_library import build_drill, evaluate_drill, validate_drill
from .practice_architecture import build_practice_architecture, validate_practice_architecture
from .performance_bible import build_performance_support_plan, validate_performance_bible
from .film_intelligence import build_assignment_grade, build_film_observation, build_film_playlist, correct_film_observation, normalize_film_links, validate_film_qa
from .scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report, validate_opponent_profile
from .analytics_dictionary import build_analytics_report, calculate_metric, validate_metric_definition, validate_metrics_dictionary
from .analytics_corpus import validate_analytics_corpus
from .backup_scheduler import BackupScheduler
from .secret_source import inspect_secret_source
from .deployment_preflight import run_deployment_preflight
from .rule_source_scheduler import RuleSourceScheduler
from .scheme_lineage import validate_scheme_lineage_corpus
from .evaluation_scenarios import validate_evaluation_scenario_corpus
from .practice_resources import plan_practice_resources
from .play_family_corpus import validate_play_family_corpus
from .performance_ingestion import ingest_performance_batch
from .performance_integration import ingest_provider_batch
from .game_plan_architecture import build_countermeasure as build_game_plan_countermeasure, build_weekly_game_plan, validate_game_plan
from .game_plan_collaboration import GamePlanCollaborationService
from .analytics_integration import calculate_provider_batch
from .rules_knowledge import build_rule_aware_recommendation, validate_rule_knowledge_entry, validate_rules_knowledge_model
from .rule_sources import load_authoritative_rule_sources, validate_rule_source_registry
from .research_protocol import build_research_packet, ingest_knowledge_item, register_research_source, resolve_claim_conflict
from .governance_audit import run_governance_audit, validate_eval_bible
from .data_architecture import validate_data_architecture, validate_record_tenancy
from .ux_architecture import validate_ux_architecture
from .engineering_architecture import validate_engineering_architecture
from .mvp_strategy import evaluate_mvp_wave, validate_mvp_strategy
from .pilot_readiness import evaluate_pilot_readiness
from .pilot_selection import build_pilot_selection
from .pilot_delivery import build_pilot_delivery_package
from .deployment_release_preflight import compose_deployment_release_preflight
from .stage0_approval import build_stage0_owner_approval, validate_stage0_owner_approval
from .organization_onboarding import approve_onboarding_package, build_onboarding_package
from .position_drill_library import load_position_drill_library, validate_position_drill_library
from .scheme_family_corpus import load_scheme_family_corpus, validate_scheme_family_corpus
from .rule_refresh import approve_rule_source_refresh, plan_rule_source_refresh
from .master_spec import validate_master_spec
from .auth import Principal, authorize_principal, issue_token, verify_token
from .tenant_repository import TenantRepository
from .team_ontology import TeamOntologyService, validate_team_alias_record
from .terminology_usage import validate_team_usage_corpus
from .media_ingestion import ingest_media_file
from .observability import ObservabilityRecorder
from .film_room import FilmRoomIndex, append_annotation, build_annotation_session, build_film_quiz, submit_film_quiz
from .agent_bible import validate_agent_bible
from .player_development_bible import validate_player_development_bible
from .staff_bible import validate_staff_bible
from .scheme_architecture import validate_scheme_architecture
from .visual_render import render_visual_svg
from .knowledge_graph import KnowledgeGraph
from .film_room_service import FilmRoomService
from .film_search import FilmSearchIndex
from .media_service import MediaCatalogService
from .media_jobs import MediaProcessingJobService
from .source_connectors import SourceConnectorService
from .source_scheduler import SourceRefreshScheduler
from .operator_summary import build_operator_summary
from .approval_inbox import build_approval_inbox
from .player_workspace import PlayerWorkspaceService
from .game_plan_workspace import build_game_plan_workspace
from .practice_workspace import PracticeWorkspaceService
from .practice_attendance import PracticeAttendanceService, build_attendance_record
from .playbook_workspace import PlaybookWorkspaceService
from .scheme_workspace import SchemeWorkspaceService
from .analytics_workspace import AnalyticsWorkspaceService
from .analytics_outcomes import AnalyticsOutcomeService, build_outcome_observation
from .scouting_workspace import ScoutingWorkspaceService, build_tendency_explorer
from .agent_runtime import AgentRuntime, load_agent_bible
from .local_agent_adapters import build_local_validation_adapter, register_local_validation_adapters
from .operational_readiness import run_operational_readiness
from .http_server import create_server
from .media_worker import index_media_file, probe_media_file, process_media_job
from .media_worker_runner import MediaWorkerRunner
from .media_transform import build_transform_command, run_transform
from .media_storage import copy_authorized_media
from .media_retention import plan_media_retention
from .media_retention_scheduler import MediaRetentionScheduler
from .media_retention_executor import execute_media_retention
from .media_transform_orchestrator import MediaTransformOrchestrator
from .knowledge_search import KnowledgeRetrievalService, KnowledgeSearchIndex
from .scheduled_operations import ScheduledOperationsService
from .release_validation import validate_release_artifacts
from .deployment_contract import validate_deployment_contract
from .monitoring_contract import load_monitoring_contract, validate_monitoring_contract
from .monitoring_registration import validate_monitoring_registration
from .scheduler_registration import load_scheduler_registration, validate_scheduler_registration
from .deployment_environment_readiness import run_deployment_environment_readiness
from .deployment_infrastructure import validate_deployment_infrastructure
from .browser_evidence import validate_browser_evidence
from .external_handoff import build_external_action_handoff
from .source_authorization import load_source_authorization, validate_source_authorization
from .master_spec_acceptance import build_stage25_spec_acceptance, load_master_spec, validate_stage25_spec_acceptance
from .seasonal_role_drill_variants import load_seasonal_role_variants, validate_seasonal_role_variants
from .usability_feedback import build_usability_feedback, validate_usability_feedback
from .organization_drill_validation import approve_organization_drill_validation, build_organization_drill_validation, validate_organization_drill_selection
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
from .organization_population_readiness import build_organization_population_readiness
from .provider_adapter_registration import approve_provider_adapter_registration, build_provider_adapter_registration
from .visual_workspace import VisualWorkspaceService
from .traceability import validate_traceability_ledger
from .demo_data import DEMO_ORGANIZATION_ID, DEMO_SEED_ID, default_database_path, find_demo_records, open_repository, purge_demo_data, seed_demo_data

__all__ = [
    "CompileIssue", "CompileResult", "compile_play", "build_player_lesson",
    "qualify_claim", "validate_evidence", "build_game_plan_options",
    "build_practice_plan", "build_tendency_record", "create_handoff",
    "build_metric_observation", "build_performance_note", "answer_rule_request", "validate_rule_source",
    "build_film_tag", "build_self_scout_report", "build_playbook_view",
    "JsonRepository", "FootballIntelligenceService",
    "build_countermeasure", "build_scheme", "validate_scheme",
    "build_red_team_matrix", "check_play_scheme_compatibility",
    "OntologyResolver", "validate_ontology_bible", "TeamContextRegistry",
    "run_minimum_eval_suite",
    "authorize",
    "create_film_clip", "register_film_asset",
    "SqliteRepository", "fingerprint_sqlite_database",
    "run_player_development_loop", "run_scheme_selection", "run_weekly_team_loop",
    "build_coach_mastery_plan", "build_development_plan", "build_mastery_record",
    "build_knowledge_claim", "validate_source",
    "build_game_decision", "build_game_situation",
    "build_special_teams_plan",
    "build_performance_observation", "build_readiness_summary",
    "build_organization_context", "resolve_person", "resolve_organization_term", "validate_organization_terminology",
    "handle_request",
    "approve_change_request", "build_change_request", "build_decision_record",
    "AgentRegistry",
    "build_completion_gate", "close_completion_gate",
    "build_release_candidate", "evaluate_delivery_wave",
    "evaluate_stage0_exit",
    "validate_system_architecture",
    "build_coaching_staff_architecture", "build_coach_development_pathway", "evaluate_coach_performance",
    "validate_scheme_bible", "validate_scheme_dossier",
    "validate_special_teams_bible", "validate_special_teams_unit",
    "approve_play", "build_extended_play", "build_play_family", "extract_role_play_spec", "request_play_approval", "validate_play_spec",
    "build_animation_timeline", "build_visual_play", "simulate_what_if", "validate_visual_play",
    "build_drill", "evaluate_drill", "validate_drill", "build_practice_architecture", "validate_practice_architecture",
    "build_performance_support_plan", "validate_performance_bible",
    "build_assignment_grade", "build_film_observation", "build_film_playlist", "correct_film_observation", "normalize_film_links", "validate_film_qa",
    "build_matchup_model", "build_opponent_evolution", "build_opponent_profile", "build_situational_scouting_report", "validate_opponent_profile", "build_pilot_selection", "build_pilot_delivery_package", "compose_deployment_release_preflight",
    "build_analytics_report", "calculate_metric", "validate_metric_definition", "validate_metrics_dictionary", "validate_analytics_corpus", "BackupScheduler", "inspect_secret_source", "run_deployment_preflight", "RuleSourceScheduler", "validate_scheme_lineage_corpus", "validate_evaluation_scenario_corpus", "plan_practice_resources", "validate_play_family_corpus", "ingest_performance_batch", "ingest_provider_batch",
    "build_game_plan_countermeasure", "build_weekly_game_plan", "validate_game_plan", "GamePlanCollaborationService", "calculate_provider_batch",
    "build_rule_aware_recommendation", "validate_rule_knowledge_entry", "validate_rules_knowledge_model", "load_authoritative_rule_sources", "validate_rule_source_registry",
    "build_research_packet", "ingest_knowledge_item", "register_research_source", "resolve_claim_conflict",
    "run_governance_audit", "validate_eval_bible",
    "validate_data_architecture", "validate_record_tenancy",
    "validate_ux_architecture",
    "validate_engineering_architecture",
    "evaluate_mvp_wave", "validate_mvp_strategy", "evaluate_pilot_readiness",
    "validate_master_spec",
    "Principal", "authorize_principal", "issue_token", "verify_token", "TenantRepository", "TeamOntologyService", "validate_team_alias_record", "validate_team_usage_corpus",
    "ingest_media_file", "ObservabilityRecorder",
    "FilmRoomIndex", "append_annotation", "build_annotation_session", "build_film_quiz", "submit_film_quiz",
    "validate_agent_bible",
    "validate_player_development_bible",
    "validate_staff_bible",
    "validate_scheme_architecture",
    "render_visual_svg",
    "KnowledgeGraph",
    "FilmRoomService",
    "FilmSearchIndex",
    "MediaCatalogService",
    "MediaProcessingJobService",
    "SourceConnectorService",
    "build_operator_summary",
    "build_approval_inbox",
    "PlayerWorkspaceService",
    "build_game_plan_workspace",
    "PracticeWorkspaceService",
    "PracticeAttendanceService", "build_attendance_record",
    "PlaybookWorkspaceService",
    "SchemeWorkspaceService",
    "AnalyticsWorkspaceService",
    "AnalyticsOutcomeService", "build_outcome_observation",
    "ScoutingWorkspaceService", "build_tendency_explorer",
    "AgentRuntime", "load_agent_bible",
    "build_local_validation_adapter", "register_local_validation_adapters",
    "run_operational_readiness",
    "create_server",
    "index_media_file", "probe_media_file", "process_media_job", "MediaWorkerRunner",
    "build_transform_command", "run_transform",
    "copy_authorized_media",
    "plan_media_retention",
    "execute_media_retention",
    "VisualWorkspaceService",
    "validate_traceability_ledger",
    "load_monitoring_contract", "validate_monitoring_contract", "validate_monitoring_registration", "load_scheduler_registration", "validate_scheduler_registration", "run_deployment_environment_readiness", "load_source_authorization", "validate_source_authorization", "build_stage25_spec_acceptance", "load_master_spec", "validate_stage25_spec_acceptance", "load_seasonal_role_variants", "validate_seasonal_role_variants", "build_usability_feedback", "validate_usability_feedback", "approve_organization_drill_validation", "build_organization_drill_validation", "validate_organization_drill_selection", "approve_organization_play_corpus", "build_organization_play_corpus", "approve_organization_doctrine", "build_organization_doctrine", "approve_organization_staff_package", "build_organization_staff_package", "approve_organization_player_development", "build_organization_player_development", "approve_organization_scouting_package", "build_organization_scouting_package", "approve_organization_analytics_package", "build_organization_analytics_package", "approve_organization_game_plan", "build_organization_game_plan", "approve_organization_special_teams", "build_organization_special_teams", "approve_organization_performance", "build_organization_performance", "approve_organization_operating_bundle", "build_organization_operating_bundle",
    "load_persisted_organization_components",
    "validate_deployment_infrastructure",
    "validate_browser_evidence",
    "build_external_action_handoff",
]
