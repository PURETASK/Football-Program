"""Named minimum evaluation families required by the Master Plan."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from .agent_contracts import create_handoff
from .access import authorize
from .auth import issue_token
from .repository import JsonRepository
from .service import FootballIntelligenceService
from .agent_runtime import AgentRuntime
from .tenant_repository import TenantRepository
from .operational_readiness import run_operational_readiness
from .migrations import apply_migrations
from .sqlite_repository import SqliteRepository
from .media_jobs import MediaProcessingJobService
from .media_worker import process_media_job, probe_media_file
from .media_transform import build_transform_command, run_transform
from .source_scheduler import SourceRefreshScheduler
from .media_retention_scheduler import MediaRetentionScheduler
from .media_transform_orchestrator import MediaTransformOrchestrator
from .knowledge_search import KnowledgeRetrievalService
from .scheduled_operations import ScheduledOperationsService
from .release_validation import validate_release_artifacts
from .deployment_contract import validate_deployment_contract
from .compatibility import check_play_scheme_compatibility
from .evidence import qualify_claim
from .ontology import OntologyResolver
from .performance import build_performance_note
from .media import create_film_clip, register_film_asset
from .workflows import run_player_development_loop, run_scheme_selection
from .knowledge import build_knowledge_claim
from .game_management import build_game_decision, build_game_situation
from .special_teams import build_special_teams_plan
from .athlete_performance import build_performance_observation, build_readiness_summary
from .organization import build_organization_context, resolve_person
from .play_compiler import compile_play
from .rules import answer_rule_request
from .scheme import build_scheme
from .change_control import approve_change_request, build_change_request, build_decision_record
from .agent_registry import AgentRegistry
from .completion import build_completion_gate, close_completion_gate
from .delivery import build_release_candidate, evaluate_delivery_wave
from .stage0 import evaluate_stage0_exit
from .stage0_approval import build_stage0_owner_approval, validate_stage0_owner_approval
from .architecture import validate_system_architecture
from .coach_development import COACH_ROLES, build_coach_development_pathway, build_coaching_staff_architecture, evaluate_coach_performance
from .scheme_bible import validate_scheme_bible
from .special_teams_bible import validate_special_teams_bible
from .playbook_architecture import approve_play, build_extended_play, extract_role_play_spec, request_play_approval, validate_play_spec
from .visual_playbook import build_animation_timeline, build_visual_play, simulate_what_if
from .drill_library import build_drill, evaluate_drill
from .practice_architecture import build_practice_architecture
from .performance_bible import build_performance_support_plan, validate_performance_bible
from .film_intelligence import build_assignment_grade, build_film_observation, build_film_playlist, correct_film_observation, validate_film_qa
from .scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report
from .analytics_dictionary import build_analytics_report, calculate_metric, validate_metrics_dictionary
from .game_plan_architecture import build_countermeasure as build_game_plan_countermeasure, build_weekly_game_plan
from .rules_knowledge import build_rule_aware_recommendation, validate_rules_knowledge_model
from .research_protocol import build_research_packet, ingest_knowledge_item, register_research_source, resolve_claim_conflict
from .governance_audit import run_governance_audit, validate_eval_bible
from .data_architecture import validate_data_architecture, validate_record_tenancy
from .ux_architecture import validate_ux_architecture
from .engineering_architecture import validate_engineering_architecture
from .mvp_strategy import evaluate_mvp_wave, validate_mvp_strategy
from .master_spec import validate_master_spec
from .repository import JsonRepository
from .service import FootballIntelligenceService
from .auth import authorize_principal, issue_token, verify_token
from .tenant_repository import TenantRepository
from .media_ingestion import ingest_media_file
from .observability import ObservabilityRecorder
from .migrations import apply_migrations, inspect_migrations
from .film_room import FilmRoomIndex, append_annotation, build_annotation_session, build_film_quiz, submit_film_quiz
from .config import load_config
from .agent_bible import validate_agent_bible
from .player_development_bible import validate_player_development_bible
from .staff_bible import validate_staff_bible
from .scheme_architecture import validate_scheme_architecture
from .visual_render import render_visual_svg
from .knowledge_graph import KnowledgeGraph
from .film_room_service import FilmRoomService
from .film_intelligence import build_film_observation
from .traceability import validate_traceability_ledger


@dataclass(frozen=True)
class EvalCaseResult:
    family_id: str
    name: str
    passed: bool
    checks: list[str]
    failures: list[str]


def _play() -> dict[str, Any]:
    return {
        "id": "PLAY-EVAL-001", "version": "0.1.0", "team_context": "TEAM-EVAL",
        "situation": {"down": 3, "distance": 6, "field_zone": "open_field"},
        "personnel": "11", "formation": "shotgun", "motion": None,
        "assignments": [{"role": "QB", "assignment": "execute"}, {"role": "C", "assignment": "communicate"}],
        "source": {"kind": "team_playbook", "ref": "EVAL-PB-001"}, "status": "draft",
    }


def _scheme() -> dict[str, Any]:
    return {
        "id": "SCHEME-EVAL-001", "version": "0.1.0", "unit": "offense", "name": "Eval scheme",
        "components": [
            {"id": "C-1", "kind": "personnel", "label": "11 personnel"},
            {"id": "C-2", "kind": "formation", "label": "shotgun"},
            {"id": "C-3", "kind": "concept", "label": "concept"},
        ],
        "assignments": [{"role": "QB", "responsibility": "execute"}], "constraints": [],
        "source": {"kind": "team_playbook", "ref": "EVAL-PB-001"},
    }


def _evidence() -> dict[str, Any]:
    return {
        "id": "EVD-EVAL-001", "claim": "Observed contextual tendency", "classification": "observed_tendency",
        "source": {"kind": "film", "ref": "EVAL-FILM-001", "captured_at": "2026-08-23"},
        "context": {"team": "TEAM-EVAL", "opponent": "OPP-EVAL", "situations": ["third_and_medium"]},
        "sample_size": 3, "confidence": "low",
    }


def _rule() -> dict[str, Any]:
    return {
        "id": "RULE-EVAL-001", "jurisdiction": "NFL", "rule_text": "Registered authoritative rule text.",
        "source": {"kind": "official_rulebook", "ref": "EVAL-RULE-001", "retrieved_at": "2026-08-23"},
        "effective_date": "2026-01-01", "authority_level": "authoritative",
    }


def _run(family_id: str, name: str, checks: list[tuple[str, bool]]) -> EvalCaseResult:
    return EvalCaseResult(family_id, name, all(passed for _, passed in checks), [label for label, passed in checks if passed], [label for label, passed in checks if not passed])


def run_minimum_eval_suite(*, suite_id: str = "EVAL-SUITE-001") -> dict[str, Any]:
    # Imported lazily because the API surface itself exposes this eval suite.
    from .api import handle_request
    resolver = OntologyResolver()
    play = _play()
    scheme = _scheme()
    evidence = _evidence()
    cases = [
        _run("EVAL-FAM-001", "NFL rule correctness and authority", [
            ("authoritative rule is answered with source", answer_rule_request(request_id="RULE-REQUEST-EVAL", question="rule?", rule=_rule(), requester_role="coach")["status"] == "answered"),
        ]),
        _run("EVAL-FAM-002", "Ontology and terminology resolution", [
            ("canonical term resolves", resolver.resolve("shotgun")["status"] == "resolved"),
            ("unknown term requires review", resolver.resolve("unknown")["requires_review"] is True),
        ]),
        _run("EVAL-FAM-003", "Play compiler validity", [
            ("valid draft compiles", compile_play(play).valid is True),
            ("invalid play rejects", compile_play({**play, "assignments": []}).valid is False),
        ]),
        _run("EVAL-FAM-004", "Scheme compatibility and red team", [
            ("compatible play passes", check_play_scheme_compatibility(play=play, scheme=scheme, result_id="COMPAT-EVAL")["compatible"] is True),
            ("scheme validates", build_scheme(scheme)["status"] == "validated"),
        ]),
        _run("EVAL-FAM-005", "Evidence provenance, sample, and confidence", [
            ("evidence is valid", qualify_claim(evidence)["valid"] is True),
            ("small sample is not generalized", qualify_claim(evidence)["generalization_allowed"] is False),
        ]),
        _run("EVAL-FAM-006", "Agent handoff and permission boundaries", [
            ("allowed validation handoff is ready", create_handoff(handoff_id="HANDOFF-EVAL-1", from_agent="AGT-001", to_agent="AGT-007", workflow_id="WF-004", payload={"play": play}, requested_permissions={"validate"})["status"] == "ready"),
            ("unauthorized lock is rejected", create_handoff(handoff_id="HANDOFF-EVAL-2", from_agent="AGT-001", to_agent="AGT-007", workflow_id="WF-004", payload={"play": play}, requested_permissions={"lock_playbook"})["status"] == "rejected"),
        ]),
        _run("EVAL-FAM-007", "Performance safety escalation", [
            ("health signal escalates", build_performance_note(note_id="PERF-EVAL-1", athlete_context="practice", observations=["signal"], recommendations=["staff review"], health_signal_present=True)["escalation_required"] is True),
        ]),
        _run("EVAL-FAM-008", "Role/resource access and locked artifacts", [
            ("player can read assigned playbook", authorize(decision_id="ACCESS-EVAL-1", requester_role="player", action="read_assigned_playbook", resource="PLAY-EVAL-001")["allowed"] is True),
            ("locked artifact requires approval", authorize(decision_id="ACCESS-EVAL-2", requester_role="coach_staff", action="draft_play", resource="PLAY-EVAL-001", locked=True)["status"] == "pending_human_approval"),
        ]),
        _run("EVAL-FAM-009", "Film asset and clip provenance", [
            ("film asset registers", register_film_asset(asset_id="FILM-EVAL-1", uri="s3://eval/game.mp4", duration_seconds=60, source={"kind":"licensed_video","ref":"EVAL-GAME"}, captured_at="2026-08-23", team_context="TEAM-EVAL")["status"] == "registered"),
            ("clip range is bounded", create_film_clip(clip_id="CLIP-EVAL-1", asset=register_film_asset(asset_id="FILM-EVAL-2", uri="s3://eval/game.mp4", duration_seconds=60, source={"kind":"licensed_video","ref":"EVAL-GAME"}, captured_at="2026-08-23", team_context="TEAM-EVAL"), start_seconds=1, end_seconds=5, team="TEAM-EVAL", opponent="OPP-EVAL", situation="third_and_medium")["status"] == "ready"),
        ]),
        _run("EVAL-FAM-010", "Core workflow composition and handoffs", [
            ("player loop reaches review", run_player_development_loop(run_id="RUN-EVAL-1", play=play, learner_role="QB", drills=[{"id":"DRILL-EVAL", "skill":"read", "evaluation":"4 of 5"}], assessment={"baseline":"x"})["status"] == "ready_for_review"),
            ("scheme selection keeps human review", run_scheme_selection(run_id="RUN-EVAL-2", candidate_schemes=[scheme], problem="problem", evidence_refs=["EVD-EVAL-001"])["review_required"] is True),
        ]),
        _run("EVAL-FAM-011", "Knowledge source hierarchy and claim provenance", [
            ("contextual claim preserves source", build_knowledge_claim(claim_id="CLAIM-EVAL-1", claim="claim", classification="observed_tendency", sources=[{"id":"SOURCE-EVAL-1", "tier":"tier_3_primary_observation", "kind":"film", "ref":"FILM-EVAL", "captured_at":"2026-08-23"}], team="TEAM-EVAL", situations=["third_and_medium"], confidence="moderate", uncertainty=["small sample"])["status"] == "draft"),
            ("high-impact weak-source claim rejects", build_knowledge_claim(claim_id="CLAIM-EVAL-2", claim="claim", classification="hypothesis", sources=[{"id":"SOURCE-EVAL-2", "tier":"tier_5_secondary_commentary", "kind":"commentary", "ref":"COMMENT-EVAL", "captured_at":"2026-08-23"}], team="TEAM-EVAL", situations=["game_plan"], confidence="high", uncertainty=["requires authority"], high_impact=True)["status"] == "rejected"),
        ]),
        _run("EVAL-FAM-012", "Situation-aware game management", [
            ("situation retains rule context", build_game_situation(situation_id="SITUATION-EVAL-1", quarter=4, clock_seconds=120, score_differential=-3, down=4, distance=2, timeouts={"TEAM-EVAL": 1}, field_zone="opponent_territory", possession="TEAM-EVAL", rule_refs=["RULE-EVAL-001"])["status"] == "ready"),
            ("decision requires human review", build_game_decision(decision_id="DECISION-EVAL-1", situation=build_game_situation(situation_id="SITUATION-EVAL-2", quarter=4, clock_seconds=120, score_differential=-3, down=4, distance=2, timeouts={"TEAM-EVAL": 1}, field_zone="opponent_territory", possession="TEAM-EVAL", rule_refs=["RULE-EVAL-001"]), options=[{"id":"OPTION-EVAL", "action":"choose", "rationale":"context", "risk":"risk"}], rule_refs=["RULE-EVAL-001"], evidence_refs=[])["human_review_required"] is True),
        ]),
        _run("EVAL-FAM-013", "Special-teams unit and phase modeling", [
            ("special-teams plan retains phase and roles", build_special_teams_plan(plan_id="ST-EVAL-1", unit="punt", phase="coverage", operation="cover", roles=[{"role":"gunner", "responsibility":"cover"}], situations=["normal_punt"], constraints=[], source={"kind":"team_playbook", "ref":"ST-EVAL"})["status"] == "draft"),
        ]),
        _run("EVAL-FAM-014", "Athlete performance and safety escalation", [
            ("performance observation validates", build_performance_observation(observation_id="PERF-OBS-EVAL-1", athlete_id="PLAYER-EVAL", session_type="practice", duration_minutes=60, repetitions=40, quality_score=0.8, season_phase="regular_season", position="QB", source={"kind":"performance_log", "ref":"PERF-EVAL"})["status"] == "valid"),
            ("sparse readiness requires staff review", build_readiness_summary(summary_id="READINESS-EVAL-1", athlete_id="PLAYER-EVAL", observations=[build_performance_observation(observation_id="PERF-OBS-EVAL-2", athlete_id="PLAYER-EVAL", session_type="practice", duration_minutes=60, repetitions=40, quality_score=0.8, season_phase="regular_season", position="QB", source={"kind":"performance_log", "ref":"PERF-EVAL"})], signals=[])["staff_review_required"] is True),
        ]),
        _run("EVAL-FAM-015", "NFL organization and season context", [
            ("organization context is NFL-scoped", build_organization_context(organization_id="ORG-EVAL", name="Eval Org", season="2026", people=[{"id":"PLAYER-EVAL", "name":"Player", "type":"player", "position":"QB"}], terminology_version="TERM-EVAL", owner="owner", source={"kind":"team_system", "ref":"ORG-EVAL"})["league"] == "NFL"),
            ("person resolves within season", resolve_person(build_organization_context(organization_id="ORG-EVAL-2", name="Eval Org", season="2026", people=[{"id":"PLAYER-EVAL-2", "name":"Player", "type":"player", "position":"QB"}], terminology_version="TERM-EVAL", owner="owner", source={"kind":"team_system", "ref":"ORG-EVAL"}), "PLAYER-EVAL-2")["status"] == "resolved"),
        ]),
        _run("EVAL-FAM-016", "API contract and interface errors", [
            ("health route returns ok", handle_request(method="GET", path="/health")[0] == 200),
            ("unknown route returns explicit error", handle_request(method="GET", path="/unknown")[0] == 404),
        ]),
        _run("EVAL-FAM-017", "Decision ledger and controlled change requests", [
            ("decision preserves alternatives", build_decision_record(decision_id="DEC-EVAL-1", title="decision", decision="choose", owner="owner", rationale="reason", alternatives=["other"], affected_ids=["CAP-001"])["status"] == "proposed"),
            ("approved change links decision", approve_change_request(build_change_request(request_id="CR-EVAL-1", title="change", requester="owner", change_type="workflow", description="description", impact_scope="workflow", dependencies=["WF-001"], risks=["RISK-012"], roadmap_effect="roadmap", affected_ids=["WF-001"]), approver="program-owner", decision_id="DEC-EVAL-2")["status"] == "approved"),
        ]),
        _run("EVAL-FAM-018", "Callable agent lifecycle and capability resolution", [
            ("agent starts callable but inactive", AgentRegistry().register(agent_id="AGT-EVAL-1", name="agent", family="film", capabilities=["tag"], permissions=[])["lifecycle"] == "callable"),
            ("agent activates only for declared capability", (lambda registry: registry.activate("AGT-EVAL-2", requested_capability="tag")["status"])(AgentRegistry()) == "rejected"),
        ]),
        _run("EVAL-FAM-019", "Feature Definition of Done and acceptance evidence", [
            ("complete gate requires all checks", (lambda gate: gate["status"])(build_completion_gate(gate_id="DONE-EVAL-1", capability_id="CAP-021", owner="owner", checks={name: True for name in ("requirement_id", "owner", "inputs_outputs", "ontology_review", "nfl_rule_review", "context_rules", "nuance_cases", "data_model", "permissions", "agent_contracts", "deterministic_validation", "tests_evals", "observability", "documentation", "acceptance_evidence")})) == "complete"),
            ("closure requires evidence and approver", close_completion_gate(build_completion_gate(gate_id="DONE-EVAL-2", capability_id="CAP-021", owner="owner", checks={name: True for name in ("requirement_id", "owner", "inputs_outputs", "ontology_review", "nfl_rule_review", "context_rules", "nuance_cases", "data_model", "permissions", "agent_contracts", "deterministic_validation", "tests_evals", "observability", "documentation", "acceptance_evidence")}), acceptance_evidence=["TEST-EVAL"], approver="owner")["status"] == "complete"),
        ]),
        _run("EVAL-FAM-020", "Progressive delivery wave and release readiness", [
            ("ready wave has complete gates", evaluate_delivery_wave(wave_id="WAVE-EVAL", number=1, outcome="slice", capability_ids=["CAP-001"], feature_gates=[{"capability_id":"CAP-001", "status":"complete"}], eval_result={"status":"passed"})["status"] == "ready"),
            ("approved release requires approver", build_release_candidate(release_id="RC-EVAL", wave={"id":"WAVE-EVAL", "status":"ready"}, feature_gate_ids=["DONE-EVAL"], eval_result={"status":"passed"}, approver="owner")["status"] == "approved"),
        ]),
        _run("EVAL-FAM-021", "Stage 0 discovery exit-gate integrity", [
            ("current discovery registry is structurally valid", (lambda result: all(check["status"] == "passed" for check in result["checks"][:5]))(evaluate_stage0_exit(_stage0_registry()))),
            ("approval cannot be inferred", evaluate_stage0_exit(_stage0_registry())["eligible_to_advance"] is False),
        ]),
        _run("EVAL-FAM-022", "Stage 1 system architecture integrity", [
            ("architecture has structural homes and flows", validate_system_architecture(_system_architecture())["status"] == "valid"),
            ("architecture preserves human authority points", len(_system_architecture().get("human_authority_points", [])) >= 6),
        ]),
        _run("EVAL-FAM-023", "Coach development and staff collaboration", [
            ("staff architecture maps coaching interfaces", build_coaching_staff_architecture(architecture_id="STAFF-EVAL", season="2026", team_context="TEAM-EVAL", staff=[{"person_id":"COACH-EVAL", "role":"head_coach", "review_owner":"OWNER"}])["status"] == "draft"),
            ("coach evaluation is evidence-bound", evaluate_coach_performance(evaluation_id="EVAL-COACH-EVAL", coach_id="COACH-EVAL", role="head_coach", ratings={dimension: 4 for dimension in COACH_ROLES["head_coach"]}, evidence=[{"source":"OBS-EVAL"}], evaluator="OWNER")["status"] == "under_review"),
            ("pathway exposes review stages", "diagnose" in build_coach_development_pathway(pathway_id="PATH-COACH-EVAL", coach_id="COACH-EVAL", role="head_coach", mentor_id="MENTOR-EVAL", objectives=[{"dimension": dimension, "measure":"review", "evidence_source":"film"} for dimension in COACH_ROLES["head_coach"]])["stages"]),
        ]),
        _run("EVAL-FAM-024", "Offensive and defensive scheme-family dossiers", [
            ("scheme bible covers both units", validate_scheme_bible(_scheme_bible())["status"] == "valid"),
            ("scheme families retain counter-counter logic", all(family.get("counter_counters") for family in _scheme_bible()["families"])),
        ]),
        _run("EVAL-FAM-025", "Special-teams bible completeness", [
            ("all special-teams units have responsibility and practice controls", validate_special_teams_bible(_special_teams_bible())["status"] == "valid"),
            ("special-teams units retain opponent scouting requirements", all(unit.get("scouting_requirements") for unit in _special_teams_bible()["units"])),
        ]),
        _run("EVAL-FAM-026", "Extended playbook specification and approval", [
            ("extended play metadata validates", validate_play_spec(_extended_eval_play())[0:1] == []),
            ("role extraction preserves assignment responsibility", extract_role_play_spec(_extended_eval_play(), role="QB")["assignment"].get("responsibility") == "read safety"),
            ("locked publication requires approval evidence", approve_play(request_play_approval(_extended_eval_play(), requester="COACH", decision_ref="DEC-EVAL-PLAY"), approver="OWNER", decision_ref="DEC-EVAL-PLAY")["status"] == "locked"),
        ]),
        _run("EVAL-FAM-027", "Visual playbook, animation, and what-if safety", [
            ("visual model renders with coordinate and accessibility controls", _visual_eval_play()["status"] == "renderable"),
            ("animation timeline is seek-safe when ordered", build_animation_timeline(timeline_id="TIMELINE-EVAL", events=[{"time_ms":0},{"time_ms":250}])["seek_safe"] is True),
            ("what-if scenario cannot replace canonical visual", simulate_what_if(simulation_id="SIM-EVAL", canonical_visual=_visual_eval_play(), adjustment={"type":"rotate_coverage"}, requester_role="coach_staff")["canonical_unchanged"] is True),
        ]),
        _run("EVAL-FAM-028", "Drill competency and evaluation library", [
            ("drill has competency, KPI, progression, and safety context", _eval_drill()["status"] == "draft"),
            ("drill evaluation remains human-reviewed", evaluate_drill(evaluation_id="EVAL-DRILL-EVAL", drill=_eval_drill(), athlete_id="PLAYER-EVAL", observations=[{"kpi":"correct_read_rate","value":0.8}], evaluator="COACH-EVAL")["human_review_required"] is True),
        ]),
        _run("EVAL-FAM-029", "Practice period and load architecture", [
            ("practice maps objective to accountable periods", _eval_practice()["status"] == "draft" and bool(_eval_practice()["objective_to_period"])),
            ("practice reports total load", _eval_practice()["total_minutes"] == 10),
        ]),
        _run("EVAL-FAM-030", "Athlete performance boundaries and escalation", [
            ("performance bible covers position demands and domains", validate_performance_bible(_performance_bible())["status"] == "valid"),
            ("health signals escalate to qualified staff", build_performance_support_plan(plan_id="PERF-PLAN-EVAL", athlete_id="PLAYER-EVAL", position="DB", season_phase="regular_season", week_context="week_1", objectives=[{"type":"conditioning","measure":"repeat efforts"}], load_context={"practice_reps":20}, recovery_context={"health_signal":True}, source={"kind":"performance_log","ref":"LOG-EVAL"}, reviewer="PERF-STAFF")["staff_escalation_required"] is True),
            ("medical decisions are rejected", build_performance_support_plan(plan_id="PERF-PLAN-EVAL-2", athlete_id="PLAYER-EVAL", position="QB", season_phase="regular_season", week_context="week_1", objectives=[{"type":"diagnose"}], load_context={"practice_reps":1}, recovery_context={}, source={"kind":"note","ref":"NOTE-EVAL"}, reviewer="PERF-STAFF")["status"] == "rejected"),
        ]),
        _run("EVAL-FAM-031", "Film observation, grading, correction, and QA", [
            ("film observation retains clip and asset provenance", _film_observation()["status"] == "ready_for_review"),
            ("low-confidence inference is blocked from definitive grading", build_assignment_grade(grade_id="GRADE-EVAL", observation=_film_observation(), player_id="PLAYER-EVAL", assignment="carry seam", grade="plus", assignment_basis="inferred", confidence="low", evidence_refs=["FILM-OBS-EVAL"], grader="COACH-EVAL")["status"] == "needs_review"),
            ("film correction and QA are explicit", correct_film_observation(observation=_film_observation(), corrected_label="quarters", corrected_by="COACH-EVAL", reason="angle review")["status"] == "corrected" and validate_film_qa(qa_id="FILM-QA-EVAL", clips=[{"id":"CLIP-EVAL","status":"ready"}], observations=[_film_observation()], reviewer="QA-EVAL")["status"] == "passed"),
        ]),
        _run("EVAL-FAM-032", "Authorized opponent scouting and matchup intelligence", [
            ("opponent profile rejects unauthorized sources", _scout_profile_eval()["status"] == "draft" and _scout_profile_eval("unauthorized")["status"] == "invalid"),
            ("situational scouting retains evidence labels", _scout_report_eval()["status"] == "under_review"),
            ("matchup and evolution outputs remain reviewable", build_matchup_model(model_id="MATCHUP-EVAL", opponent="OPP-EVAL", matchups=[{"our_role":"WR1","opponent_role":"CB1","advantage_hypothesis":"release","counter":"stack","uncertainty":"small sample"}], evidence_refs=["FILM-EVAL"], context={"situation":"third_down"}, analyst="SCOUT-EVAL")["human_review_required"] is True and build_opponent_evolution(evolution_id="EVOLUTION-EVAL", opponent="OPP-EVAL", historical_claims=[{"claim":"A"}], current_claims=[{"claim":"B"}], evidence_refs=["FILM-EVAL"], analyst="SCOUT-EVAL")["status"] == "under_review"),
        ]),
        _run("EVAL-FAM-033", "Analytics dictionary, lineage, and statistical nuance", [
            ("metric dictionary contains definitions, formulas, and consumers", validate_metrics_dictionary(_analytics_dictionary())["status"] == "valid"),
            ("metric output retains uncertainty and lineage", _analytics_observation()["status"] == "valid" and "interval" in _analytics_observation()["uncertainty"]),
            ("analytics report requires valid observations and caveats", build_analytics_report(report_id="ANALYTICS-REPORT-EVAL", audience="coach_staff", metric_observations=[_analytics_observation()], context={"season":"2026"}, caveats=["sample"], analyst="ANALYST-EVAL")["status"] == "draft"),
        ]),
        _run("EVAL-FAM-034", "Weekly game plan, triggers, and counter-counter logic", [
            ("weekly plan includes offense, defense, special teams, situations, and teaching", _game_plan_eval()["status"] == "under_review"),
            ("countermeasure retains counter-counter and trigger", build_game_plan_countermeasure(countermeasure_id="COUNTERMEASURE-EVAL", threat="pressure", primary_response="hot", opponent_counter="drop", counter_counter="screen", trigger="pressure look", evidence_refs=["FILM-EVAL"], owner="OC-EVAL")["status"] == "draft"),
            ("plan remains human-decision controlled", _game_plan_eval()["human_decision_required"] is True),
        ]),
        _run("EVAL-FAM-035", "Versioned NFL rules knowledge and fact-strategy separation", [
            ("NFL rule model has versioned authoritative entries", validate_rules_knowledge_model(_rules_model_eval())["status"] == "valid"),
            ("rule facts are separated from strategy recommendations", build_rule_aware_recommendation(recommendation_id="RULE-REC-EVAL", question="fourth down", rule_facts=[{"id":"RULE-KB-005","authority":"authoritative","fact":"rule fact"}], strategy_recommendation="compare options", situation={"down":4,"distance":2,"clock":90}, requester_role="coach_staff", rule_refs=["RULE-KB-005"], evidence_refs=["DATA-EVAL"]) ["facts_and_strategy_separated"] is True),
            ("non-authoritative rule facts escalate", build_rule_aware_recommendation(recommendation_id="RULE-REC-EVAL-2", question="x", rule_facts=[{"id":"RULE-KB-1","authority":"secondary","fact":"x"}], strategy_recommendation="x", situation={"down":1}, requester_role="coach", rule_refs=["RULE-KB-1"], evidence_refs=[])["status"] == "rejected"),
        ]),
        _run("EVAL-FAM-036", "Research ingestion, citations, freshness, and conflict handling", [
            ("knowledge ingestion preserves citation and canonical eligibility", _research_item_eval()["canonical_eligible"] is True),
            ("same-tier contradictions remain unresolved", resolve_claim_conflict(conflict_id="CONFLICT-EVAL", claims=[{"id":"CLAIM-1","source_tier":"tier_3_primary_observation"},{"id":"CLAIM-2","source_tier":"tier_3_primary_observation"}], conflict_type="contradiction")["canonical_publish_allowed"] is False),
            ("research packet retains methodology and gaps", build_research_packet(packet_id="RESEARCH-PACKET-EVAL", question="q", source_ids=["SOURCE-EVAL"], knowledge_items=[_research_item_eval()], methodology=["compare sources"], gaps=["sample"], reviewer="OWNER-EVAL")["status"] == "under_review"),
        ]),
        _run("EVAL-FAM-037", "Quality, safety, permission, and promotion governance", [
            ("eval bible covers critical risk domains", validate_eval_bible(_eval_bible())["status"] == "valid"),
            ("failed suite blocks promotion", run_governance_audit(audit_id="AUDIT-EVAL-1", eval_result={"status":"failed"}, critical_failures=[], safety_failures=[], permission_failures=[], audit_event_id="EVENT-EVAL-1", observability_evidence=["TRACE-EVAL-1"], human_approval="APPROVAL-EVAL-1")["promotion_blocked"] is True),
            ("complete evidence permits promotion eligibility", run_governance_audit(audit_id="AUDIT-EVAL-2", eval_result={"status":"passed"}, critical_failures=[], safety_failures=[], permission_failures=[], audit_event_id="EVENT-EVAL-2", observability_evidence=["TRACE-EVAL-2"], human_approval="APPROVAL-EVAL-2")["status"] == "eligible_for_promotion"),
        ]),
        _run("EVAL-FAM-038", "Canonical data architecture, history, and tenancy", [
            ("data architecture covers entities and relationships", validate_data_architecture(_data_architecture_eval())["status"] == "valid"),
            ("cross-organization access is denied by default", validate_record_tenancy(record={"organization_id":"ORG-1"}, requester_organization="ORG-2")["allowed"] is False),
            ("approved cross-organization scope is auditable", validate_record_tenancy(record={"organization_id":"ORG-1"}, requester_organization="ORG-2", cross_organization_scope=True)["audit_required"] is True),
        ]),
        _run("EVAL-FAM-039", "Role-based UX architecture and accessibility", [
            ("UX architecture covers core role journeys and screens", validate_ux_architecture(_ux_architecture_eval())["status"] == "valid"),
            ("permission mappings point to known UI surfaces", all(mapping.get("ui_surfaces") for mapping in _ux_architecture_eval()["permissions_to_ui"])),
            ("accessibility and restricted states are explicit", bool(_ux_architecture_eval().get("accessibility")) and "restricted" in _ux_architecture_eval().get("interaction_states", [])),
        ]),
        _run("EVAL-FAM-040", "Engineering architecture, CI, and observability", [
            ("engineering architecture covers repo and runtime boundaries", validate_engineering_architecture(_engineering_architecture_eval())["status"] == "valid"),
            ("CI requires governance before promotion", any("require governance audit" in command for command in _engineering_architecture_eval()["ci_cd"])),
            ("observability includes audit and permission signals", all(signal in _engineering_architecture_eval()["observability"]["signals"] for signal in ("audit_events", "permission_denials"))),
        ]),
        _run("EVAL-FAM-041", "MVP waves, priorities, and progressive delivery", [
            ("MVP strategy has sequential vertical slices and risks", validate_mvp_strategy(_mvp_strategy_eval())["status"] == "valid"),
            ("wave blocks without acceptance or approval", evaluate_mvp_wave(wave=_mvp_strategy_eval()["waves"][0], completed_capabilities=set(_mvp_strategy_eval()["waves"][0]["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=[], feature_flags={"production_recommendations":False}, approval=None)["status"] == "blocked"),
            ("wave can become ready with evidence and flags controlled", evaluate_mvp_wave(wave=_mvp_strategy_eval()["waves"][0], completed_capabilities=set(_mvp_strategy_eval()["waves"][0]["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=["TEST-EVAL","AUDIT-EVAL"], feature_flags={"production_recommendations":False}, approval="OWNER-EVAL")["status"] == "ready"),
        ]),
        _run("EVAL-FAM-042", "Master Codex implementation specification integrity", [
            ("master spec covers all 26 stages", validate_master_spec(_master_spec_eval())["status"] == "valid" and validate_master_spec(_master_spec_eval())["stage_count"] == 26),
            ("master spec contains reproducible quality commands", any("unittest" in command for command in _master_spec_eval()["quality_commands"]) and any("run_evals" in command for command in _master_spec_eval()["quality_commands"])),
            ("master spec prohibits unsafe and unauthorized changes", any("unsupported" in rule for rule in _master_spec_eval()["prohibited_changes"]) and any("cross-organization" in rule for rule in _master_spec_eval()["prohibited_changes"])),
        ]),
        _run("EVAL-FAM-043", "Wave 1 core play-to-teaching-to-practice vertical slice", [
            ("slice creates a pending approval package", _core_slice_eval()["package"]["status"] == "pending_approval"),
            ("slice persists role view and measurable drill", _core_slice_eval()["view_status"] == "renderable" and _core_slice_eval()["drill_has_kpi"]),
            ("approval publishes a locked play with audit history", _core_slice_eval()["approved"]["status"] == "approved" and _core_slice_eval()["play_status"] == "locked" and _core_slice_eval()["play_events"] >= 1),
        ]),
        _run("EVAL-FAM-044", "Wave 2 source-linked film, scouting, and analytics slice", [
            ("film asset and bounded clip persist", _evidence_slice_eval()["package"]["status"] == "under_review" and _evidence_slice_eval()["clip_asset_linked"]),
            ("scouting and metric outputs retain evidence lineage", _evidence_slice_eval()["scouting_status"] == "under_review" and _evidence_slice_eval()["metric_status"] == "valid"),
            ("film QA and analytics report remain reviewable", _evidence_slice_eval()["qa_status"] == "passed" and _evidence_slice_eval()["analytics_status"] == "draft"),
        ]),
        _run("EVAL-FAM-045", "Wave 3 weekly planning, governance, and release gates", [
            ("weekly game plan and rule recommendation persist", _weekly_delivery_eval()["plan_status"] == "under_review" and _weekly_delivery_eval()["rule_status"] == "under_review"),
            ("release blocks without human approval", _weekly_delivery_eval()["blocked_status"] == "blocked"),
            ("release approves only with complete gates and approval", _weekly_delivery_eval()["approved_status"] == "approved"),
        ]),
        _run("EVAL-FAM-046", "Authenticated role and organization tenancy boundaries", [
            ("signed principal round trips", _auth_eval()["principal_org"] == "ORG-EVAL"),
            ("role permission is enforced", _auth_eval()["can_scout"] and not _auth_eval()["can_lock"]),
            ("cross-organization access is denied", not _auth_eval()["cross_org_allowed"]),
        ]),
        _run("EVAL-FAM-047", "Tenant-scoped canonical repository enforcement", [
            ("tenant writes require matching organization", _tenant_eval()["mismatch_rejected"]),
            ("tenant reads do not expose another organization", _tenant_eval()["hidden"]),
            ("tenant history remains scoped", _tenant_eval()["history_scoped"]),
        ]),
        _run("EVAL-FAM-048", "Accessible operator dashboard and control visibility", [
            ("dashboard exposes control and eval routes", _ui_eval()["routes"]),
            ("dashboard exposes human approval state", _ui_eval()["approval"]),
            ("dashboard includes accessible navigation", _ui_eval()["accessible"]),
        ]),
        _run("EVAL-FAM-049", "Authorized media ingestion and integrity catalog", [
            ("authorized media registers with tenant and digest", _media_eval()["registered"]),
            ("unsupported or unauthorized media is rejected", _media_eval()["rejected"]),
            ("media integrity digest is reproducible", _media_eval()["digest"]),
        ]),
        _run("EVAL-FAM-050", "Structured observability and operational evidence", [
            ("successful operation emits required evidence", _observability_eval()["success"]),
            ("failed operation emits error status", _observability_eval()["failure"]),
            ("runtime event contains organization and request identity", _observability_eval()["identity"]),
        ]),
        _run("EVAL-FAM-051", "SQLite migration, snapshot, and history preservation", [
            ("migration dry-run reports pending work", _migration_eval()["planned"]),
            ("migration reaches current schema", _migration_eval()["current"]),
            ("migration preserves canonical history", _migration_eval()["history"]),
        ]),
        _run("EVAL-FAM-052", "Searchable film room, annotation correction, and quiz mode", [
            ("film search retains organization and situation filters", _film_room_eval()["search"]),
            ("annotation session flags low-confidence correction", _film_room_eval()["correction"]),
            ("quiz submission retains clip evidence and review state", _film_room_eval()["quiz"]),
        ]),
        _run("EVAL-FAM-053", "Reproducible runtime configuration and deployment contract", [
            ("local runtime configuration resolves", _runtime_eval()["local"]),
            ("production requires a strong secret", _runtime_eval()["production"]),
            ("missing authentication configuration is rejected", _runtime_eval()["missing_secret"]),
        ]),
        _run("EVAL-FAM-054", "NFL ontology depth and canonical alias integrity", [
            ("ontology covers core football domains", _ontology_depth_eval()["domains"]),
            ("expanded position and scheme terms resolve", _ontology_depth_eval()["terms"]),
            ("expanded ontology has no alias ambiguity", _ontology_depth_eval()["valid"]),
        ]),
        _run("EVAL-FAM-055", "Agent Organization Bible and bounded handoffs", [
            ("all callable agents have structured mission boundaries", _agent_bible_eval()["valid"]),
            ("handoff matrix includes validation and human escalation", _agent_bible_eval()["handoffs"]),
            ("prompt and eval requirements preserve evidence and authority", _agent_bible_eval()["requirements"]),
        ]),
        _run("EVAL-FAM-056", "NFL player development position coverage and mastery controls", [
            ("position families cover core NFL roles", _player_development_eval()["coverage"]),
            ("each position has evidence and assessment methods", _player_development_eval()["evidence"]),
            ("IDP, mastery, learning path, and safety controls are explicit", _player_development_eval()["controls"]),
        ]),
        _run("EVAL-FAM-057", "Coaching staff mastery, collaboration, and evaluation bible", [
            ("all major staff roles have mastery dimensions", _staff_bible_eval()["roles"]),
            ("staff pathway preserves observable review stages", _staff_bible_eval()["pathway"]),
            ("collaboration and professional boundaries are explicit", _staff_bible_eval()["boundaries"]),
        ]),
        _run("EVAL-FAM-058", "Compositional offensive and defensive scheme architecture", [
            ("offensive taxonomy and concept graph are explicit", _scheme_architecture_eval()["offense"]),
            ("defensive front-fit-coverage-pressure taxonomy is explicit", _scheme_architecture_eval()["defense"]),
            ("counters retain triggers, evidence, and counter-counters", _scheme_architecture_eval()["counters"]),
        ]),
        _run("EVAL-FAM-059", "Accessible visual playbook SVG and isolated what-if rendering", [
            ("canonical visual renders with role labels", _visual_render_eval()["canonical"]),
            ("what-if rendering is explicitly separated", _visual_render_eval()["what_if"]),
            ("render includes accessibility semantics", _visual_render_eval()["accessibility"]),
        ]),
        _run("EVAL-FAM-060", "Versioned provenance-bearing football knowledge graph", [
            ("graph nodes retain organization, source, and classification", _knowledge_graph_eval()["nodes"]),
            ("graph edges require existing endpoints and preserve context", _knowledge_graph_eval()["edges"]),
            ("hypotheses and weak claims cannot become canonical silently", _knowledge_graph_eval()["review"]),
        ]),
        _run("EVAL-FAM-061", "Repository-backed tenant-scoped film search and quiz persistence", [
            ("film observations survive service recreation", _film_room_service_eval()["search"]),
            ("quiz attempts persist with review state", _film_room_service_eval()["quiz"]),
            ("film service is organization-scoped", _film_room_service_eval()["scope"]),
        ]),
        _run("EVAL-FAM-062", "26-stage requirements traceability ledger", [
            ("ledger covers every master-plan stage", _traceability_eval()["valid"]),
            ("remaining production work is explicit", _traceability_eval()["remaining"]),
        ]),
        _run("EVAL-FAM-063", "Authenticated organization-scoped film-room API", [
            ("observation save and search are wired", _film_room_api_eval()["search"]),
            ("quiz attempts persist through the API", _film_room_api_eval()["quiz"]),
            ("cross-organization access is denied", _film_room_api_eval()["scope"]),
        ]),
        _run("EVAL-FAM-064", "Authorized media catalog and bounded clip API", [
            ("authorized media assets retain integrity metadata", _media_api_eval()["asset"]),
            ("clips are bounded by registered asset duration", _media_api_eval()["clip"]),
            ("media listings retain organization scope", _media_api_eval()["scope"]),
        ]),
        _run("EVAL-FAM-065", "Durable media processing worker lifecycle", [
            ("jobs are queued and claimed by a worker", _media_job_api_eval()["claim"]),
            ("jobs complete with output references", _media_job_api_eval()["complete"]),
            ("job state remains organization-scoped", _media_job_api_eval()["scope"]),
        ]),
        _run("EVAL-FAM-066", "Authorized source registration and freshness visibility", [
            ("only an owner can register a source", _source_api_eval()["register"]),
            ("analysts can inspect freshness state", _source_api_eval()["freshness"]),
            ("source listings remain organization-scoped", _source_api_eval()["scope"]),
        ]),
        _run("EVAL-FAM-067", "Role-aware organization operator summary", [
            ("summary is authenticated and organization-scoped", _operator_summary_api_eval()["scope"]),
            ("role controls visible workspace sections", _operator_summary_api_eval()["role"]),
            ("pending review and media state are surfaced", _operator_summary_api_eval()["counts"]),
        ]),
        _run("EVAL-FAM-068", "Organization-scoped approval inbox and governance visibility", [
            ("governance roles can see pending records", _approval_inbox_api_eval()["visible"]),
            ("non-governance roles are denied the inbox", _approval_inbox_api_eval()["denied"]),
            ("inbox retains evidence and approval boundaries", _approval_inbox_api_eval()["boundary"]),
        ]),
        _run("EVAL-FAM-069", "Privacy-scoped player Today workspace", [
            ("coaches can create player assignments", _player_api_eval()["assignment"]),
            ("players can read their own Today workspace", _player_api_eval()["today"]),
            ("players cannot read another player's workspace", _player_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-070", "Organization-scoped game-plan review workspace", [
            ("coaches can review weekly plan evidence", _game_plan_api_eval()["visible"]),
            ("game-plan workspace surfaces review state", _game_plan_api_eval()["review"]),
            ("players cannot access staff planning data", _game_plan_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-071", "Coach practice builder and load-control workspace", [
            ("coaches can create a practice plan", _practice_api_eval()["create"]),
            ("practice workspace exposes load and review state", _practice_api_eval()["workspace"]),
            ("players cannot access staff practice plans", _practice_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-072", "Compositional scheme workspace and review boundary", [
            ("coaches can save validated compositional schemes", _scheme_api_eval()["save"]),
            ("scheme workspace exposes unit-filtered review", _scheme_api_eval()["workspace"]),
            ("players cannot access scheme design data", _scheme_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-073", "Analyst metric lineage and uncertainty workspace", [
            ("analysts can create reviewable reports", _analytics_api_eval()["create"]),
            ("workspace surfaces lineage and uncertainty", _analytics_api_eval()["workspace"]),
            ("players cannot access analytical team data", _analytics_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-074", "Opponent scouting workspace and adaptation warnings", [
            ("analysts can create reviewable scouting reports", _scouting_api_eval()["create"]),
            ("workspace surfaces sample and adaptation warnings", _scouting_api_eval()["workspace"]),
            ("players cannot access opponent scouting data", _scouting_api_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-075", "Bounded specialist-agent runtime and auditable handoffs", [
            ("active specialist dispatch completes through a registered adapter", _agent_runtime_eval()["completed"]),
            ("inactive or unadapted agents remain safely bounded", _agent_runtime_eval()["bounded"]),
            ("agent run retains organization-scoped audit state", _agent_runtime_eval()["audit"]),
        ]),
        _run("EVAL-FAM-076", "Deployment readiness and operational blocker checks", [
            ("migrated validation runtime reports ready", _operational_readiness_eval()["ready"]),
            ("missing database reports explicit blockers", _operational_readiness_eval()["database_blocked"]),
            ("invalid production secret is rejected", _operational_readiness_eval()["secret_blocked"]),
            ("missing production media tooling is rejected", _operational_readiness_eval()["media_tooling_blocked"]),
        ]),
        _run("EVAL-FAM-077", "Authenticated deterministic visual playbook workspace", [
            ("coach can persist a renderable visual play", _visual_workspace_eval()["create"]),
            ("authorized role view returns SVG", _visual_workspace_eval()["render"]),
            ("cross-organization visual access is denied", _visual_workspace_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-078", "Human-reviewed visual what-if isolation", [
            ("what-if scenario is created for review", _visual_what_if_eval()["created"]),
            ("canonical visual remains unchanged", _visual_what_if_eval()["isolated"]),
            ("players cannot create what-if scenarios", _visual_what_if_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-079", "Persisted film annotation and correction workflow", [
            ("analyst can open an annotation session", _film_annotation_eval()["open"]),
            ("low-confidence observations require correction", _film_annotation_eval()["correction"]),
            ("annotation state remains organization-scoped", _film_annotation_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-080", "Persistent organization-scoped film search index", [
            ("SQLite film search survives service recreation", _film_search_eval()["persistent"]),
            ("search applies context filters", _film_search_eval()["filters"]),
            ("other organizations cannot retrieve indexed records", _film_search_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-081", "HTTP adapter runtime and structured request errors", [
            ("health is reachable over the configured HTTP adapter", _http_server_eval()["health"]),
            ("control route is served over HTTP", _http_server_eval()["control"]),
            ("malformed JSON returns a structured 400", _http_server_eval()["bad_json"]),
        ]),
        _run("EVAL-FAM-082", "Bounded media probe worker and metadata fallback", [
            ("authorized probe job completes with output evidence", _media_worker_eval()["completed"]),
            ("worker preserves safe metadata-only fallback", _media_worker_eval()["fallback"]),
            ("unapproved media path is blocked", _media_worker_eval()["path_blocked"]),
        ]),
        _run("EVAL-FAM-083", "Authenticated media content streaming and range safety", [
            ("authorized users receive full media bytes", _media_stream_eval()["full"]),
            ("valid byte ranges return partial content", _media_stream_eval()["range"]),
            ("cross-organization content access is denied", _media_stream_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-084", "Bounded media transform lifecycle", [
            ("transforms use bounded non-shell commands", _media_transform_eval()["command"]),
            ("worker completes transformed output evidence", _media_transform_eval()["completed"]),
            ("path escapes and missing tools fail explicitly", _media_transform_eval()["safety"]),
        ]),
        _run("EVAL-FAM-085", "Atomic managed media storage and retention safety", [
            ("authorized media is copied with digest evidence", _media_storage_eval()["stored"]),
            ("duplicate storage does not overwrite", _media_storage_eval()["duplicate"]),
            ("source boundary violations are rejected", _media_storage_eval()["boundary"]),
        ]),
        _run("EVAL-FAM-086", "Owner-scoped non-destructive media retention planning", [
            ("retention planner identifies expired review candidates", _media_retention_eval()["candidate"]),
            ("planner never deletes records", _media_retention_eval()["non_destructive"]),
            ("non-owner retention access is denied", _media_retention_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-087", "Bounded authorized source refresh operations", [
            ("stale sources are refreshed in a bounded batch", _source_refresh_batch_eval()["selected"]),
            ("partial source failures remain explicit", _source_refresh_batch_eval()["partial"]),
            ("analyst refresh remains organization-scoped", _source_refresh_batch_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-088", "Scheduler-ready source freshness planning and persisted execution", [
            ("due sources are selected within a hard bound", _source_scheduler_eval()["bounded"]),
            ("scheduled execution persists a batch report", _source_scheduler_eval()["persisted"]),
            ("current schedules remain non-destructive", _source_scheduler_eval()["safe"]),
        ]),
        _run("EVAL-FAM-089", "Persisted organization-scoped film playlists", [
            ("authorized coaching staff can persist a clip playlist", _film_playlist_eval()["created"]),
            ("playlist reads remain role-filtered and organization-scoped", _film_playlist_eval()["scoped"]),
            ("unknown clips cannot enter a playlist", _film_playlist_eval()["validated"]),
        ]),
        _run("EVAL-FAM-090", "Persisted non-destructive media retention scans", [
            ("retention scans persist review evidence", _retention_scheduler_eval()["persisted"]),
            ("retention scans never delete assets", _retention_scheduler_eval()["safe"]),
            ("retention scans require owner governance scope", _retention_scheduler_eval()["privacy"]),
        ]),
        _run("EVAL-FAM-091", "Bounded persisted media transform orchestration", [
            ("transform execution respects a hard job bound", _transform_orchestrator_eval()["bounded"]),
            ("transform results are persisted with batch evidence", _transform_orchestrator_eval()["persisted"]),
            ("invalid transforms fail without invoking an unsafe runner", _transform_orchestrator_eval()["safe"]),
        ]),
        _run("EVAL-FAM-092", "Authorized HTTPS source fetcher redirect and provenance safety", [
            ("source redirects outside the allowlist are rejected", _source_fetcher_safety_eval()),
        ]),
        _run("EVAL-FAM-093", "Organization-scoped provenance-aware knowledge retrieval", [
            ("knowledge search returns citation-bearing records", _knowledge_search_eval()["retrieved"]),
            ("knowledge search remains organization-scoped", _knowledge_search_eval()["scoped"]),
            ("knowledge search enforces a bounded result limit", _knowledge_search_eval()["bounded"]),
        ]),
        _run("EVAL-FAM-094", "Safe external scheduled-operations contract", [
            ("scheduled operations default to bounded dry-run planning", _scheduled_operations_eval()["dry_run"]),
            ("production execution remains blocked by the Stage 0 gate", _scheduled_operations_eval()["blocked"]),
        ]),
        _run("EVAL-FAM-095", "Non-deploying release artifact validation", [
            ("required release artifacts are present", _release_validation_eval()["artifacts"]),
            ("release validation preserves the Stage 0 approval blocker", _release_validation_eval()["approval"]),
            ("release validation never deploys", _release_validation_eval()["non_deploying"]),
        ]),
        _run("EVAL-FAM-096", "Design-only deployment topology contract", [
            ("deployment topology contains required services", _deployment_contract_eval()["valid"]),
            ("deployment topology cannot enable production", _deployment_contract_eval()["safe"]),
        ]),
        _run("EVAL-FAM-097", "Explicit non-activating Stage 0 owner approval evidence", [
            ("unready Stage 0 gate rejects approval", _stage0_approval_eval()["unready_rejected"]),
            ("owner approval remains non-activating", _stage0_approval_eval()["non_activating"]),
        ]),
    ]
    passed = sum(1 for case in cases if case.passed)
    failed = len(cases) - passed
    return {
        "suite_id": suite_id,
        "version": "0.1.0",
        "status": "passed" if failed == 0 else "failed",
        "families": [asdict(case) for case in cases],
        "passed": passed,
        "failed": failed,
        "coverage": [case.family_id for case in cases],
    }


def _traceability_eval() -> dict[str, bool]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "control" / "requirements-traceability.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    result = validate_traceability_ledger(ledger)
    return {
        "valid": result["status"] == "valid" and result["stage_count"] == 26,
        "remaining": any("production" in item for item in ledger.get("global_remaining_work", [])),
    }


def _stage0_approval_eval() -> dict[str, bool]:
    import json
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root / "control" / "stage-0a-registry.json").read_text(encoding="utf-8"))
    blocked_gate = evaluate_stage0_exit(registry)
    ready_gate = evaluate_stage0_exit(registry, gap_audit_complete=True)
    rejected = build_stage0_owner_approval(
        approval_id="APPROVAL-STAGE0-EVAL-BLOCKED", gate_result=blocked_gate,
        registry_id=registry["registry_id"], approver="OWNER-EVAL", rationale="premature", evidence_refs=["GATE-EVAL"],
        approved_at="2026-08-23T12:00:00Z",
    )
    approved = build_stage0_owner_approval(
        approval_id="APPROVAL-STAGE0-EVAL-READY", gate_result=ready_gate,
        registry_id=registry["registry_id"], approver="OWNER-EVAL", rationale="Reviewed Stage 0 evidence", evidence_refs=["GATE-EVAL"],
        approved_at="2026-08-23T12:00:00Z",
    )
    checked = validate_stage0_owner_approval(approved, gate_result=ready_gate)
    return {"unready_rejected": rejected["decision"] == "rejected", "non_activating": checked["status"] == "valid" and approved["production_implementation_allowed"] is False and approved["stage_advance_authorized"] is False}




def _film_room_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "film-room-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            token = issue_token(subject="COACH-EVAL", role="coach_staff", organization_id="ORG-FILM-EVAL", secret=secret)
            analyst_token = issue_token(subject="ANALYST-EVAL", role="analyst", organization_id="ORG-FILM-EVAL", secret=secret)
            headers = {"Authorization": f"Bearer {token}"}
            analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            observation = build_film_observation(observation_id="FILM-OBS-EVAL-API", clip_id="CLIP-EVAL-API", asset_id="FILM-EVAL-API", domain="coverage", label="two_high", team="TEAM-EVAL", opponent="OPP-EVAL", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="COACH-EVAL", evidence="rotation visible")
            observation["organization_id"] = "ORG-FILM-EVAL"
            saved = handle_request(method="POST", path="/v1/film/observations", body={"organization_id":"ORG-FILM-EVAL", "observation":observation}, headers=analyst_headers, service=service)[0] == 201
            found = handle_request(method="GET", path="/v1/film/search?organization_id=ORG-FILM-EVAL&opponent=OPP-EVAL", headers=analyst_headers, service=service)
            quiz_body = {"organization_id":"ORG-FILM-EVAL", "quiz_id":"QUIZ-EVAL-API", "title":"Coverage", "role":"QB", "clip_ids":["CLIP-EVAL-API"], "questions":[{"id":"Q-1", "prompt":"shell", "expected_answer":"two_high", "evidence_refs":["CLIP-EVAL-API"]}]}
            quiz = handle_request(method="POST", path="/v1/film/quizzes", body=quiz_body, headers=headers, service=service)[0] == 201
            attempt = handle_request(method="POST", path="/v1/film/quizzes/QUIZ-EVAL-API/attempts", body={"organization_id":"ORG-FILM-EVAL", "attempt_id":"QUIZ-ATTEMPT-EVAL-API", "participant":"PLAYER-EVAL", "answers":{"Q-1":"two_high"}}, headers=headers, service=service)[0] == 201
            denied = handle_request(method="GET", path="/v1/film/search?organization_id=ORG-OTHER", headers=headers, service=service)[0] == 403
            return {"search": saved and found[0] == 200 and len(found[1]["data"]["results"]) == 1, "quiz": quiz and attempt, "scope": denied}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _media_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "media-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            token = issue_token(subject="ANALYST-MEDIA-EVAL", role="analyst", organization_id="ORG-MEDIA-EVAL", secret=secret)
            headers = {"Authorization": "Bearer " + token}
            root = Path(directory)
            media = root / "eval.mp4"
            media.write_bytes(b"media eval fixture")
            service = FootballIntelligenceService(JsonRepository(root / "state.json"))
            asset_body = {"organization_id":"ORG-MEDIA-EVAL", "file_path":str(media), "asset_id":"FILM-EVAL-MEDIA-001", "duration_seconds":90.0, "source":{"kind":"licensed_film", "ref":"LICENSE-EVAL-001"}, "captured_at":"2026-08-23", "team_context":"TEAM-EVAL", "allowed_roots":[str(root)]}
            asset_status, asset_payload = handle_request(method="POST", path="/v1/media/assets", body=asset_body, headers=headers, service=service)
            clip_body = {"organization_id":"ORG-MEDIA-EVAL", "clip_id":"CLIP-EVAL-MEDIA-001", "asset_id":"FILM-EVAL-MEDIA-001", "start_seconds":5.0, "end_seconds":15.0, "team":"TEAM-EVAL", "opponent":"OPP-EVAL", "situation":"third_down"}
            clip_status, clip_payload = handle_request(method="POST", path="/v1/media/clips", body=clip_body, headers=headers, service=service)
            listing = handle_request(method="GET", path="/v1/media/clips?organization_id=ORG-MEDIA-EVAL&opponent=OPP-EVAL", headers=headers, service=service)
            denied = handle_request(method="GET", path="/v1/media/assets?organization_id=ORG-OTHER", headers=headers, service=service)[0] == 403
            return {"asset": asset_status == 201 and asset_payload["data"].get("sha256"), "clip": clip_status == 201 and clip_payload["data"]["status"] == "ready", "scope": denied and listing[0] == 200 and len(listing[1]["data"]["clips"]) == 1}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _media_job_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "media-job-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            token = issue_token(subject="ANALYST-JOB-EVAL", role="analyst", organization_id="ORG-JOB-EVAL", secret=secret)
            headers = {"Authorization": "Bearer " + token}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-JOB-EVAL", "job_id":"MEDIA-JOB-EVAL-001", "asset_id":"FILM-JOB-EVAL-001", "operation":"probe", "payload":{}}
            created = handle_request(method="POST", path="/v1/media/jobs", body=body, headers=headers, service=service)[0] == 201
            claimed = handle_request(method="POST", path="/v1/media/jobs/MEDIA-JOB-EVAL-001/claim", body={"organization_id":"ORG-JOB-EVAL", "worker_id":"WORKER-EVAL"}, headers=headers, service=service)[1]["data"]["status"] == "running"
            completed = handle_request(method="POST", path="/v1/media/jobs/MEDIA-JOB-EVAL-001/complete", body={"organization_id":"ORG-JOB-EVAL", "worker_id":"WORKER-EVAL", "output_refs":["META-EVAL-001"]}, headers=headers, service=service)[1]["data"]["status"] == "completed"
            denied = handle_request(method="GET", path="/v1/media/jobs?organization_id=ORG-OTHER", headers=headers, service=service)[0] == 403
            return {"claim": created and claimed, "complete": completed, "scope": denied}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _source_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "source-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            owner_headers = {"Authorization": "Bearer " + issue_token(subject="OWNER-SOURCE-EVAL", role="program_owner", organization_id="ORG-SOURCE-EVAL", secret=secret)}
            analyst_headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SOURCE-EVAL", role="analyst", organization_id="ORG-SOURCE-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-SOURCE-EVAL", "source_id":"SOURCE-EVAL-API", "tier":"tier_1_authoritative", "kind":"official_rulebook", "uri":"https://rules.example.test/nfl", "captured_at":"2026-08-23", "effective_period":"2026-season", "citation_location":"rule 1", "allowed_domains":["rules.example.test"]}
            owner_status = handle_request(method="POST", path="/v1/sources", body=body, headers=owner_headers, service=service)[0]
            analyst_status = handle_request(method="POST", path="/v1/sources", body=body, headers=analyst_headers, service=service)[0]
            listing = handle_request(method="GET", path="/v1/sources?organization_id=ORG-SOURCE-EVAL", headers=analyst_headers, service=service)
            denied = handle_request(method="GET", path="/v1/sources?organization_id=ORG-OTHER", headers=analyst_headers, service=service)[0] == 403
            return {"register": owner_status == 201 and analyst_status == 403, "freshness": listing[0] == 200 and listing[1]["data"]["sources"][0]["stale"] is True, "scope": denied}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _operator_summary_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "summary-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            token = issue_token(subject="COACH-SUMMARY-EVAL", role="coach_staff", organization_id="ORG-SUMMARY-EVAL", secret=secret)
            headers = {"Authorization": "Bearer " + token}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("media_processing_jobs", "MEDIA-JOB-SUMMARY-EVAL", {"id":"MEDIA-JOB-SUMMARY-EVAL", "organization_id":"ORG-SUMMARY-EVAL", "status":"retryable"}, actor="COACH-SUMMARY-EVAL", reason="eval_fixture")
            response = handle_request(method="GET", path="/v1/operator/summary?organization_id=ORG-SUMMARY-EVAL", headers=headers, service=service)
            denied = handle_request(method="GET", path="/v1/operator/summary?organization_id=ORG-OTHER", headers=headers, service=service)
            data = response[1].get("data", {})
            return {"scope": response[0] == 200 and denied[0] == 403 and data.get("organization_id") == "ORG-SUMMARY-EVAL", "role": "game_plan" in data.get("allowed_sections", []) and "governance" not in data.get("allowed_sections", []), "counts": data.get("pending_review_count") == 1 and data.get("media_job_counts", {}).get("retryable") == 1}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _approval_inbox_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "inbox-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            owner_headers = {"Authorization": "Bearer " + issue_token(subject="OWNER-INBOX-EVAL", role="program_owner", organization_id="ORG-INBOX-EVAL", secret=secret)}
            analyst_headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-INBOX-EVAL", role="analyst", organization_id="ORG-INBOX-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("game_plans", "GAMEPLAN-INBOX-EVAL", {"id":"GAMEPLAN-INBOX-EVAL", "organization_id":"ORG-INBOX-EVAL", "status":"under_review", "source_refs":["SOURCE-INBOX-EVAL"]}, actor="ANALYST-INBOX-EVAL", reason="eval_fixture")
            response = handle_request(method="GET", path="/v1/governance/inbox?organization_id=ORG-INBOX-EVAL", headers=owner_headers, service=service)
            denied = handle_request(method="GET", path="/v1/governance/inbox?organization_id=ORG-INBOX-EVAL", headers=analyst_headers, service=service)
            item = response[1].get("data", {}).get("items", [{}])[0]
            return {"visible": response[0] == 200 and response[1]["data"]["count"] == 1, "denied": denied[0] == 403, "boundary": item.get("can_approve") is True and "SOURCE-INBOX-EVAL" in item.get("evidence_refs", [])}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _player_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "player-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization": "Bearer " + issue_token(subject="COACH-PLAYER-EVAL", role="coach_staff", organization_id="ORG-PLAYER-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-EVAL", role="player", organization_id="ORG-PLAYER-EVAL", secret=secret)}
            other_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-OTHER-EVAL", role="player", organization_id="ORG-PLAYER-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PLAYER-EVAL", "assignment_id":"ASSIGNMENT-PLAYER-EVAL", "player_id":"PLAYER-EVAL", "title":"Protection", "assignment_type":"playbook", "artifact_id":"PLAY-PLAYER-EVAL", "source_refs":["PLAY-PLAYER-EVAL"]}
            assignment = handle_request(method="POST", path="/v1/player/assignments", body=body, headers=coach_headers, service=service)
            today = handle_request(method="GET", path="/v1/player/today?organization_id=ORG-PLAYER-EVAL&player_id=PLAYER-EVAL", headers=player_headers, service=service)
            privacy = handle_request(method="GET", path="/v1/player/today?organization_id=ORG-PLAYER-EVAL&player_id=PLAYER-EVAL", headers=other_headers, service=service)
            return {"assignment": assignment[0] == 201, "today": today[0] == 200 and today[1]["data"]["next_step"]["id"] == "ASSIGNMENT-PLAYER-EVAL", "privacy": privacy[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _game_plan_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "game-plan-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization": "Bearer " + issue_token(subject="COACH-PLAN-EVAL", role="coach_staff", organization_id="ORG-PLAN-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-PLAN-EVAL", role="player", organization_id="ORG-PLAN-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("game_plans", "GAMEPLAN-PLAN-EVAL", {"id":"GAMEPLAN-PLAN-EVAL", "organization_id":"ORG-PLAN-EVAL", "week":"WEEK-EVAL", "status":"under_review"}, actor="COACH-PLAN-EVAL", reason="eval_fixture")
            response = handle_request(method="GET", path="/v1/game-plan/workspace?organization_id=ORG-PLAN-EVAL&week=WEEK-EVAL", headers=coach_headers, service=service)
            denied = handle_request(method="GET", path="/v1/game-plan/workspace?organization_id=ORG-PLAN-EVAL", headers=player_headers, service=service)
            data = response[1].get("data", {})
            return {"visible": response[0] == 200 and len(data.get("plans", [])) == 1, "review": data.get("pending_review_count") == 1 and data.get("human_approval_required") is True, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _practice_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "practice-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization": "Bearer " + issue_token(subject="COACH-PRACTICE-EVAL", role="coach_staff", organization_id="ORG-PRACTICE-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-PRACTICE-EVAL", role="player", organization_id="ORG-PRACTICE-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PRACTICE-EVAL", "practice_id":"PRACTICE-EVAL-001", "team_context":"TEAM-EVAL", "season_phase":"regular_season", "week_context":"WEEK-EVAL", "objective":"fit run", "opponent_priorities":["gap run"], "periods":[{"id":"PERIOD-EVAL-1", "type":"team", "objective":"fit", "owner":"COACH", "players":["DL"], "minutes":20, "reps":8, "learning_rationale":"leverage", "load_rationale":"moderate"}], "staff_available":["COACH"], "facility_constraints":[], "load_controls":{"max_total_minutes":30, "max_reps_by_position":{"DL":20}}, "restrictions":[]}
            created = handle_request(method="POST", path="/v1/practice/plans", body=body, headers=coach_headers, service=service)
            workspace = handle_request(method="GET", path="/v1/practice/workspace?organization_id=ORG-PRACTICE-EVAL&week=WEEK-EVAL", headers=coach_headers, service=service)
            denied = handle_request(method="GET", path="/v1/practice/workspace?organization_id=ORG-PRACTICE-EVAL", headers=player_headers, service=service)
            data = workspace[1].get("data", {})
            return {"create": created[0] == 201, "workspace": workspace[0] == 200 and data.get("status") == "ready" and data.get("human_review_required") is True, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _scheme_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "scheme-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization": "Bearer " + issue_token(subject="COACH-SCHEME-EVAL", role="coach_staff", organization_id="ORG-SCHEME-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-SCHEME-EVAL", role="player", organization_id="ORG-SCHEME-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            scheme = {"id":"SCHEME-EVAL-API", "version":"0.1.0", "unit":"offense", "name":"Eval offense", "components":[{"id":"C-1", "kind":"personnel", "label":"11 personnel"},{"id":"C-2", "kind":"formation", "label":"shotgun"},{"id":"C-3", "kind":"concept", "label":"inside_zone"}], "assignments":[{"role":"QB", "responsibility":"read"}], "constraints":[], "source":{"kind":"team_playbook", "ref":"PB-EVAL-API"}}
            saved = handle_request(method="POST", path="/v1/schemes", body={"organization_id":"ORG-SCHEME-EVAL", "scheme":scheme}, headers=coach_headers, service=service)
            workspace = handle_request(method="GET", path="/v1/schemes/workspace?organization_id=ORG-SCHEME-EVAL&unit=offense", headers=coach_headers, service=service)
            denied = handle_request(method="GET", path="/v1/schemes/workspace?organization_id=ORG-SCHEME-EVAL", headers=player_headers, service=service)
            return {"save": saved[0] == 201 and saved[1]["data"]["status"] == "validated", "workspace": workspace[0] == 200 and len(workspace[1]["data"]["schemes"]) == 1, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _analytics_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "analytics-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            analyst_headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-EVAL", role="analyst", organization_id="ORG-ANALYTICS-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-EVAL", role="player", organization_id="ORG-ANALYTICS-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            observation = {"id":"METRIC-OBS-EVAL-API", "metric_id":"METRIC-DEF-001", "numerator":6, "denominator":10, "rate":0.6, "confidence":"moderate", "uncertainty":{"method":"wilson", "interval":[0.3,0.8]}, "context":{"situation":"third_down"}, "source":{"kind":"charting", "ref":"FILM-EVAL-API"}, "observation_ids":["PLAY-EVAL-API"], "status":"valid"}
            body = {"organization_id":"ORG-ANALYTICS-EVAL", "report_id":"ANALYTICS-REPORT-EVAL-API", "audience":"coach_staff", "metric_observations":[observation], "context":{"situation":"third_down"}, "caveats":["sample only"]}
            created = handle_request(method="POST", path="/v1/analytics/reports", body=body, headers=analyst_headers, service=service)
            workspace = handle_request(method="GET", path="/v1/analytics/workspace?organization_id=ORG-ANALYTICS-EVAL&situation=third_down", headers=analyst_headers, service=service)
            denied = handle_request(method="GET", path="/v1/analytics/workspace?organization_id=ORG-ANALYTICS-EVAL", headers=player_headers, service=service)
            data = workspace[1].get("data", {})
            return {"create": created[0] == 201 and created[1]["data"]["status"] == "draft", "workspace": workspace[0] == 200 and data.get("lineage_complete_count") == 1 and data.get("uncertainty_count") == 1, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _scouting_api_eval() -> dict[str, bool]:
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "scouting-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            analyst_headers = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SCOUT-EVAL", role="analyst", organization_id="ORG-SCOUT-EVAL", secret=secret)}
            player_headers = {"Authorization": "Bearer " + issue_token(subject="PLAYER-SCOUT-EVAL", role="player", organization_id="ORG-SCOUT-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            report = {"id":"SCOUT-REPORT-EVAL-API", "opponent":"OPP-EVAL", "situation":{"down":3}, "claims":[{"classification":"observed", "confidence":"moderate", "uncertainty":["sample"], "evidence_refs":["CLIP-EVAL-API"]}], "sample_size":4, "source_refs":["CLIP-EVAL-API"], "analyst":"ANALYST-SCOUT-EVAL", "status":"under_review"}
            created = handle_request(method="POST", path="/v1/scouting/reports", body={"organization_id":"ORG-SCOUT-EVAL", "report":report}, headers=analyst_headers, service=service)
            workspace = handle_request(method="GET", path="/v1/scouting/workspace?organization_id=ORG-SCOUT-EVAL&opponent=OPP-EVAL", headers=analyst_headers, service=service)
            denied = handle_request(method="GET", path="/v1/scouting/workspace?organization_id=ORG-SCOUT-EVAL", headers=player_headers, service=service)
            data = workspace[1].get("data", {})
            return {"create": created[0] == 201 and data.get("human_review_required") is True, "workspace": workspace[0] == 200 and data.get("low_sample_count") == 1, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _agent_runtime_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-AGENT-EVAL", actor="coach")
        runtime = AgentRuntime(repository)
        runtime.register_bible({"roles":[{"id":"AGT-007", "name":"Validator", "family":"validation", "authority":["validate"]}]})
        blocked = runtime.dispatch(run_id="RUN-EVAL-BLOCKED", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-EVAL", payload={"play_id":"PLAY-EVAL"})
        runtime.activate(agent_id="AGT-007", capability="validate")
        pending = runtime.dispatch(run_id="RUN-EVAL-PENDING", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-EVAL", payload={"play_id":"PLAY-EVAL"})
        runtime.register_adapter(agent_id="AGT-007", capability="validate", adapter=lambda payload, context: {"valid": True, "play_id": payload["play_id"]})
        completed = runtime.dispatch(run_id="RUN-EVAL-COMPLETED", from_agent="AGT-001", family="validation", capability="validate", workflow_id="WF-EVAL", payload={"play_id":"PLAY-EVAL"})
        saved = repository.get("agent_runs", "RUN-EVAL-COMPLETED")
        return {"completed": completed["status"] == "completed" and completed["output"]["valid"], "bounded": blocked["status"] == "blocked" and pending["status"] == "awaiting_adapter" and pending["human_review_required"], "audit": saved is not None and saved["organization_id"] == "ORG-AGENT-EVAL" and saved["handoff"]["status"] == "ready"}


def _operational_readiness_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "fidos.sqlite3"
        repository = SqliteRepository(database)
        repository.close()
        apply_migrations(database)
        ready = run_operational_readiness(environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_DATABASE":str(database)}, database_path=database, run_evals=False)
        missing = run_operational_readiness(environ={"NFL_FIDOS_ENV":"validation", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_DATABASE":str(Path(directory) / "missing.sqlite3")}, database_path=Path(directory) / "missing.sqlite3", run_evals=False)
        secret = run_operational_readiness(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"short", "NFL_FIDOS_DATABASE":str(Path(directory) / "secret.sqlite3")}, database_path=Path(directory) / "secret.sqlite3", run_evals=False)
        tools = run_operational_readiness(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32, "NFL_FIDOS_FFMPEG":"missing-ffmpeg", "NFL_FIDOS_FFPROBE":"missing-ffprobe", "NFL_FIDOS_DATABASE":str(Path(directory) / "tools.sqlite3")}, database_path=Path(directory) / "tools.sqlite3", run_evals=False)
        ready_ids = {check["id"] for check in ready["checks"] if check["status"] == "pass"}
        return {"ready": {"runtime_config", "database_parent", "database_integrity", "database_migrations", "control_plane"}.issubset(ready_ids), "database_blocked": "database_integrity" in missing["blockers"] and "database_migrations" in missing["blockers"], "secret_blocked": "runtime_config" in secret["blockers"], "media_tooling_blocked": "media_tooling" in tools["blockers"]}


def _visual_workspace_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "visual-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization":"Bearer " + issue_token(subject="COACH-VISUAL-EVAL", role="coach_staff", organization_id="ORG-VISUAL-EVAL", secret=secret)}
            player_headers = {"Authorization":"Bearer " + issue_token(subject="PLAYER-VISUAL-EVAL", role="player", organization_id="ORG-OTHER-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            visual = {"id":"VISUAL-EVAL-001", "play_id":"PLAY-EVAL-001", "source_play_version":"1.0.0", "players":[{"id":"P-QB", "role":"QB", "position":{"x":10, "y":26.6}}], "paths":[{"player_id":"P-QB", "points":[{"x":10, "y":26.6},{"x":20, "y":26.6}]}], "timeline":[{"time_ms":0, "event":"snap"}], "role_views":["QB","coach"], "accessibility":["QB takes snap"]}
            created = handle_request(method="POST", path="/v1/playbook/visuals", body={"organization_id":"ORG-VISUAL-EVAL", "visual":visual}, headers=coach_headers, service=service)
            rendered = handle_request(method="GET", path="/v1/playbook/visual?organization_id=ORG-VISUAL-EVAL&visual_id=VISUAL-EVAL-001&role=QB", headers=coach_headers, service=service)
            denied = handle_request(method="GET", path="/v1/playbook/visual?organization_id=ORG-VISUAL-EVAL&visual_id=VISUAL-EVAL-001", headers=player_headers, service=service)
            return {"create": created[0] == 201 and created[1]["data"]["status"] == "renderable", "render": rendered[0] == 200 and "<svg" in rendered[1]["data"]["svg"] and rendered[1]["data"]["role"] == "QB", "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _visual_what_if_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    with tempfile.TemporaryDirectory() as directory:
        secret = "visual-what-if-eval-secret-012345678901"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            coach_headers = {"Authorization":"Bearer " + issue_token(subject="COACH-WHATIF-EVAL", role="coach_staff", organization_id="ORG-WHATIF-EVAL", secret=secret)}
            player_headers = {"Authorization":"Bearer " + issue_token(subject="PLAYER-WHATIF-EVAL", role="player", organization_id="ORG-WHATIF-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            visual = {"id":"VISUAL-WHATIF-001", "play_id":"PLAY-WHATIF-001", "source_play_version":"1.0.0", "players":[{"id":"P-QB", "role":"QB", "position":{"x":10, "y":26.6}}], "paths":[{"player_id":"P-QB", "points":[{"x":10, "y":26.6},{"x":20, "y":26.6}]}], "timeline":[{"time_ms":0, "event":"snap"}], "role_views":["QB"], "accessibility":["QB takes snap"]}
            handle_request(method="POST", path="/v1/playbook/visuals", body={"organization_id":"ORG-WHATIF-EVAL", "visual":visual}, headers=coach_headers, service=service)
            scenario = handle_request(method="POST", path="/v1/playbook/visuals/VISUAL-WHATIF-001/what-if", body={"organization_id":"ORG-WHATIF-EVAL", "simulation_id":"SIM-WHATIF-001", "adjustment":{"type":"rotate_coverage"}}, headers=coach_headers, service=service)
            denied = handle_request(method="POST", path="/v1/playbook/visuals/VISUAL-WHATIF-001/what-if", body={"organization_id":"ORG-WHATIF-EVAL", "simulation_id":"SIM-WHATIF-002", "adjustment":{"type":"rotate_coverage"}}, headers=player_headers, service=service)
            canonical = service.repository.get("visual_plays", "VISUAL-WHATIF-001")
            saved_scenario = service.repository.get("visual_scenarios", "SIM-WHATIF-001")
            return {"created": scenario[0] == 201 and scenario[1]["data"]["human_review_required"], "isolated": canonical is not None and saved_scenario["source_visual_id"] == canonical["id"] and saved_scenario["canonical_unchanged"], "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _film_annotation_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    from .film_intelligence import build_film_observation
    with tempfile.TemporaryDirectory() as directory:
        secret = "film-annotation-eval-secret-012345678901"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            analyst = {"Authorization":"Bearer " + issue_token(subject="ANALYST-ANNOTATION-EVAL", role="analyst", organization_id="ORG-ANNOTATION-EVAL", secret=secret)}
            player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-ANNOTATION-EVAL", role="player", organization_id="ORG-OTHER-ANNOTATION", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            opened = handle_request(method="POST", path="/v1/film/annotation-sessions", body={"organization_id":"ORG-ANNOTATION-EVAL", "session_id":"ANNOTATION-EVAL-001", "clip_id":"CLIP-ANNOTATION-EVAL", "allowed_domains":["coverage"], "source_refs":["CLIP-ANNOTATION-EVAL"]}, headers=analyst, service=service)
            observation = build_film_observation(observation_id="FILM-ANNOTATION-EVAL", clip_id="CLIP-ANNOTATION-EVAL", asset_id="FILM-ASSET-ANNOTATION-EVAL", domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2", situation={"down":3}, source_frame="00:00:02.000", confidence="low", observed_or_inferred="inferred", annotator="ANALYST-ANNOTATION-EVAL", evidence="limited view")
            appended = handle_request(method="POST", path="/v1/film/annotation-sessions/ANNOTATION-EVAL-001/annotations", body={"organization_id":"ORG-ANNOTATION-EVAL", "observation":observation}, headers=analyst, service=service)
            denied = handle_request(method="GET", path="/v1/film/annotation-sessions?organization_id=ORG-ANNOTATION-EVAL", headers=player, service=service)
            return {"open": opened[0] == 201 and opened[1]["data"]["status"] == "open", "correction": appended[0] == 200 and appended[1]["data"]["correction_required"], "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _film_search_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "film.sqlite3"
        first_repository = SqliteRepository(database)
        second_repository = SqliteRepository(database)
        other_repository = SqliteRepository(database)
        try:
            first = FilmRoomService(TenantRepository(first_repository, organization_id="ORG-FTS-EVAL", actor="ANALYST"))
            observation = {"id":"FILM-FTS-EVAL", "organization_id":"ORG-FTS-EVAL", "domain":"coverage", "label":"two_high", "evidence":"rotation visible", "confidence":"moderate", "context":{"team":"TEAM-1", "opponent":"TEAM-2"}}
            first.save_observation(observation, actor="ANALYST")
            second = FilmRoomService(TenantRepository(second_repository, organization_id="ORG-FTS-EVAL", actor="COACH"))
            records = second.search(query="rotation", opponent="TEAM-2")
            other = FilmRoomService(TenantRepository(other_repository, organization_id="ORG-OTHER-FTS-EVAL", actor="COACH"))
            return {"persistent": len(records) == 1, "filters": records[0]["context"]["opponent"] == "TEAM-2", "privacy": other.search(query="rotation") == []}
        finally:
            first_repository.close()
            second_repository.close()
            other_repository.close()


def _http_server_eval() -> dict[str, bool]:
    import json
    import threading
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
    from .http_server import create_server
    with tempfile.TemporaryDirectory() as directory:
        server, repository = create_server(port=0, database_path=Path(directory) / "http.sqlite3")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            with urlopen(base + "/health") as response:
                health = json.loads(response.read())
            with urlopen(base + "/v1/control") as response:
                control = json.loads(response.read())
            request = Request(base + "/v1/plays/compile", data=b"not-json", method="POST", headers={"Content-Type":"application/json", "Content-Length":"8"})
            try:
                urlopen(request)
                bad_json = False
            except HTTPError as error:
                bad_json = error.code == 400 and json.loads(error.read()).get("status") == "error"
            return {"health": health.get("status") == "ok", "control": control.get("data", {}).get("stage") == "STAGE-0", "bad_json": bad_json}
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
            repository.close()


def _media_worker_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        media = Path(directory) / "game.mp4"
        media.write_bytes(b"fixture")
        repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-MEDIA-EVAL", actor="ANALYST")
        jobs = MediaProcessingJobService(repository)
        jobs.create_job(job_id="MEDIA-JOB-EVAL-001", asset_id="FILM-ASSET-EVAL-001", operation="probe", payload={"file_path":str(media), "allowed_roots":[directory]}, requested_by="ANALYST")
        completed = process_media_job(repository=repository, job_id="MEDIA-JOB-EVAL-001", worker_id="WORKER-EVAL", runner=lambda arguments: (0, '{"format":{"duration":"10.0","format_name":"mp4"}}', ""))
        fallback = probe_media_file(file_path=media, allowed_roots=[directory], runner=lambda arguments: (127, "", "missing"))
        blocked = probe_media_file(file_path=media, allowed_roots=[Path(directory) / "not-approved"], runner=lambda arguments: (0, "{}", ""))
        return {"completed": completed["status"] == "completed" and len(repository.list("media_processing_outputs")) == 1, "fallback": fallback["status"] == "metadata_only" and fallback["tool_available"] is False, "path_blocked": blocked["status"] == "rejected"}


def _media_stream_eval() -> dict[str, bool]:
    import os
    import threading
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
    from .auth import issue_token
    from .http_server import create_server
    secret = "media-stream-eval-secret-012345678901"
    previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
    os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
    with tempfile.TemporaryDirectory() as directory:
        media = Path(directory) / "game.mp4"
        media.write_bytes(b"0123456789")
        server, repository = create_server(port=0, database_path=Path(directory) / "state.sqlite3")
        repository.put("film_assets", "FILM-STREAM-EVAL", {"id":"FILM-STREAM-EVAL", "organization_id":"ORG-STREAM-EVAL", "uri":media.as_uri(), "media_type":"video/mp4"}, actor="owner", reason="stream_eval")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}/v1/media/assets/FILM-STREAM-EVAL/content?organization_id=ORG-STREAM-EVAL"
            token = issue_token(subject="COACH-STREAM-EVAL", role="coach_staff", organization_id="ORG-STREAM-EVAL", secret=secret)
            headers = {"Authorization":"Bearer " + token}
            with urlopen(Request(base, headers=headers)) as response:
                full = response.read() == b"0123456789"
            with urlopen(Request(base, headers={**headers, "Range":"bytes=2-5"})) as response:
                ranged = response.status == 206 and response.read() == b"2345"
            other = issue_token(subject="COACH-OTHER-STREAM-EVAL", role="coach_staff", organization_id="ORG-OTHER-STREAM-EVAL", secret=secret)
            try:
                urlopen(Request(base, headers={"Authorization":"Bearer " + other}))
                privacy = False
            except HTTPError as error:
                privacy = error.code == 403
            return {"full":full, "range":ranged, "privacy":privacy}
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
            repository.close()
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _media_transform_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "source.mp4"
        output = Path(directory) / "output.mp4"
        source.write_bytes(b"fixture")
        command, _, _ = build_transform_command(operation="transcode", input_path=source, output_path=output, allowed_roots=[directory])
        command_ok = command[0] == "ffmpeg" and "-nostdin" in command and "-n" in command
        repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-TRANSFORM-EVAL", actor="ANALYST")
        jobs = MediaProcessingJobService(repository)
        jobs.create_job(job_id="MEDIA-JOB-TRANSFORM-EVAL", asset_id="FILM-ASSET-TRANSFORM-EVAL", operation="transcode", payload={"file_path":str(source), "output_path":str(output), "allowed_roots":[directory]}, requested_by="ANALYST")
        completed = process_media_job(repository=repository, job_id="MEDIA-JOB-TRANSFORM-EVAL", worker_id="WORKER-TRANSFORM-EVAL", runner=lambda arguments: (0, "", ""))
        escaped = run_transform(operation="transcode", input_path=source, output_path=Path(directory).parent / "escape.mp4", allowed_roots=[directory], runner=lambda arguments: (0, "", ""))
        missing_tool = run_transform(operation="transcode", input_path=source, output_path=Path(directory) / "missing.mp4", allowed_roots=[directory], runner=lambda arguments: (127, "", "missing"))
        return {"command":command_ok, "completed":completed["status"] == "completed" and len(repository.list("media_processing_outputs")) == 1, "safety":escaped["status"] == "rejected" and missing_tool["status"] == "failed" and missing_tool["tool_available"] is False}


def _media_storage_eval() -> dict[str, bool]:
    from .media_storage import copy_authorized_media
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source_root = root / "approved"
        storage_root = root / "managed"
        source_root.mkdir()
        source = source_root / "game.mp4"
        source.write_bytes(b"media")
        stored = copy_authorized_media(source_path=source, storage_root=storage_root, organization_id="ORG-STORAGE-EVAL", asset_id="FILM-STORAGE-EVAL", allowed_source_roots=[source_root])
        duplicate = copy_authorized_media(source_path=source, storage_root=storage_root, organization_id="ORG-STORAGE-EVAL", asset_id="FILM-STORAGE-EVAL", allowed_source_roots=[source_root])
        boundary = copy_authorized_media(source_path=source, storage_root=storage_root, organization_id="ORG-STORAGE-EVAL", asset_id="FILM-STORAGE-BOUNDARY", allowed_source_roots=[root / "not-approved"])
        return {"stored": stored["status"] == "stored" and len(stored["sha256"]) == 64, "duplicate": duplicate["status"] == "rejected", "boundary": boundary["status"] == "rejected"}


def _media_retention_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    from .auth import issue_token
    with tempfile.TemporaryDirectory() as directory:
        secret = "retention-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            owner = {"Authorization":"Bearer " + issue_token(subject="OWNER-RETENTION-EVAL", role="program_owner", organization_id="ORG-RETENTION-EVAL", secret=secret)}
            player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-RETENTION-EVAL", role="player", organization_id="ORG-RETENTION-EVAL", secret=secret)}
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("film_assets", "FILM-RETENTION-EVAL", {"id":"FILM-RETENTION-EVAL", "organization_id":"ORG-RETENTION-EVAL", "captured_at":"2020-01-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/old.mp4"}}, actor="owner", reason="retention_eval")
            report = handle_request(method="GET", path="/v1/media/retention-plan?organization_id=ORG-RETENTION-EVAL&retention_days=1", headers=owner, service=service)
            denied = handle_request(method="GET", path="/v1/media/retention-plan?organization_id=ORG-RETENTION-EVAL", headers=player, service=service)
            return {"candidate": report[0] == 200 and len(report[1]["data"]["candidates"]) == 1, "non_destructive": report[1]["data"]["delete_performed"] is False and service.repository.get("film_assets", "FILM-RETENTION-EVAL") is not None, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _source_refresh_batch_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    from .auth import issue_token
    with tempfile.TemporaryDirectory() as directory:
        secret = "source-batch-eval-secret-012345678901"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            owner = {"Authorization":"Bearer " + issue_token(subject="OWNER-SOURCE-BATCH", role="program_owner", organization_id="ORG-SOURCE-BATCH", secret=secret)}
            analyst = {"Authorization":"Bearer " + issue_token(subject="ANALYST-SOURCE-BATCH", role="analyst", organization_id="ORG-SOURCE-BATCH", secret=secret)}
            player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-SOURCE-BATCH", role="player", organization_id="ORG-SOURCE-BATCH", secret=secret)}
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            service_source = _sources_for_eval(service, "ORG-SOURCE-BATCH", "OWNER", lambda uri, limit: (b"fresh", {}) if uri.endswith("GOOD") else (_ for _ in ()).throw(RuntimeError("refresh failed")))
            for source_id in ("SOURCE-BATCH-GOOD", "SOURCE-BATCH-BAD"):
                service_source.register_source(source_id=source_id, tier="tier_1_authoritative", kind="official_rulebook", uri=f"https://rules.example.test/{source_id}", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER-SOURCE-BATCH", allowed_domains=["rules.example.test"], actor="OWNER-SOURCE-BATCH")
            report = service_source.refresh_all(actor="ANALYST-SOURCE-BATCH", stale_only=True, max_sources=2)
            denied = handle_request(method="POST", path="/v1/sources/refresh-all", body={"organization_id":"ORG-SOURCE-BATCH"}, headers=player, service=service)
            return {"selected": report["selected_count"] == 2, "partial": report["status"] == "partial_failure" and report["failed_count"] == 1, "privacy": denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _source_scheduler_eval() -> dict[str, bool]:
    from datetime import datetime, timezone
    with tempfile.TemporaryDirectory() as directory:
        base_repository = JsonRepository(Path(directory) / "state.json")
        repository = TenantRepository(base_repository, organization_id="ORG-SOURCE-SCHED", actor="OWNER-SOURCE-SCHED")
        service = _sources_for_eval(FootballIntelligenceService(base_repository), "ORG-SOURCE-SCHED", "OWNER-SOURCE-SCHED", lambda uri, limit: (b"fresh", {}))
        for source_id in ("SOURCE-SCHED-A", "SOURCE-SCHED-B"):
            service.register_source(source_id=source_id, tier="tier_1_authoritative", kind="official_rulebook", uri=f"https://rules.example.test/{source_id}", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER-SOURCE-SCHED", allowed_domains=["rules.example.test"], freshness_days=1, actor="OWNER-SOURCE-SCHED")
        scheduler = SourceRefreshScheduler(repository, connector=service)
        now = datetime(2026, 8, 23, tzinfo=timezone.utc)
        plan = scheduler.plan_due(now=now, max_sources=1)
        report = scheduler.run_due(actor="ANALYST-SOURCE-SCHED", now=now, max_sources=1)
        current = SourceRefreshScheduler(TenantRepository(JsonRepository(Path(directory) / "current.json"), organization_id="ORG-CURRENT", actor="OWNER")).plan_due(now=now, max_sources=1)
        return {"bounded": plan["due_count"] == 2 and len(plan["selected"]) == 1, "persisted": report["refreshed_count"] == 1 and len(repository.list("source_refresh_batches")) == 1, "safe": current["status"] == "current" and current["destructive_action_required"] is False}


def _film_playlist_eval() -> dict[str, bool]:
    import os
    from .api import handle_request
    from .auth import issue_token
    with tempfile.TemporaryDirectory() as directory:
        secret = "playlist-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            service.repository.put("film_clips", "CLIP-PLAYLIST-EVAL", {"id":"CLIP-PLAYLIST-EVAL", "organization_id":"ORG-PLAYLIST-EVAL", "status":"ready"}, actor="seed", reason="playlist_eval_seed")
            coach = {"Authorization":"Bearer " + issue_token(subject="COACH-PLAYLIST-EVAL", role="coach_staff", organization_id="ORG-PLAYLIST-EVAL", secret=secret)}
            player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-PLAYLIST-EVAL", role="player", organization_id="ORG-PLAYLIST-EVAL", secret=secret)}
            body = {"organization_id":"ORG-PLAYLIST-EVAL", "playlist_id":"PLAYLIST-EVAL", "name":"Teaching cutup", "purpose":"teaching", "clip_ids":["CLIP-PLAYLIST-EVAL"], "filters":{}, "access_roles":["coach_staff"]}
            created = handle_request(method="POST", path="/v1/film/playlists", body=body, headers=coach, service=service)
            listed = handle_request(method="GET", path="/v1/film/playlists?organization_id=ORG-PLAYLIST-EVAL", headers=coach, service=service)
            player_list = handle_request(method="GET", path="/v1/film/playlists?organization_id=ORG-PLAYLIST-EVAL", headers=player, service=service)
            invalid = handle_request(method="POST", path="/v1/film/playlists", body={**body, "playlist_id":"PLAYLIST-BAD", "clip_ids":["CLIP-MISSING"]}, headers=coach, service=service)
            return {"created": created[0] == 201 and len(service.repository.list("film_playlists")) == 1, "scoped": listed[0] == 200 and len(listed[1]["data"]["playlists"]) == 1 and player_list[0] == 403, "validated": invalid[0] == 422}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _retention_scheduler_eval() -> dict[str, bool]:
    import os
    from datetime import datetime, timezone
    from .api import handle_request
    from .auth import issue_token
    with tempfile.TemporaryDirectory() as directory:
        secret = "retention-scan-eval-secret-012345678901234567890"
        previous = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            base = JsonRepository(Path(directory) / "state.json")
            repository = TenantRepository(base, organization_id="ORG-RETENTION-SCAN-EVAL", actor="OWNER-RETENTION-SCAN")
            repository.put("film_assets", "FILM-OLD-SCAN-EVAL", {"id":"FILM-OLD-SCAN-EVAL", "organization_id":"ORG-RETENTION-SCAN-EVAL", "captured_at":"2020-01-01T00:00:00+00:00", "managed_storage":{"destination_path":"managed/old.mp4"}}, actor="OWNER-RETENTION-SCAN", reason="retention_scan_eval_seed")
            report = MediaRetentionScheduler(repository).run_scan(actor="OWNER-RETENTION-SCAN", retention_days=1, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
            service = FootballIntelligenceService(base)
            owner = {"Authorization":"Bearer " + issue_token(subject="OWNER-RETENTION-SCAN", role="program_owner", organization_id="ORG-RETENTION-SCAN-EVAL", secret=secret)}
            player = {"Authorization":"Bearer " + issue_token(subject="PLAYER-RETENTION-SCAN", role="player", organization_id="ORG-RETENTION-SCAN-EVAL", secret=secret)}
            denied = handle_request(method="POST", path="/v1/media/retention-scan", body={"organization_id":"ORG-RETENTION-SCAN-EVAL"}, headers=player, service=service)
            owner_result = handle_request(method="POST", path="/v1/media/retention-scan", body={"organization_id":"ORG-RETENTION-SCAN-EVAL"}, headers=owner, service=service)
            return {"persisted":report["status"] == "review_required" and repository.get("media_retention_runs", report["id"]) is not None and owner_result[0] == 200, "safe": report["destructive_action_executed"] is False and repository.get("film_assets", "FILM-OLD-SCAN-EVAL") is not None, "privacy":denied[0] == 403}
        finally:
            if previous is None:
                os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
            else:
                os.environ["NFL_FIDOS_AUTH_SECRET"] = previous


def _transform_orchestrator_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.mp4"
        source.write_bytes(b"video")
        base = JsonRepository(root / "state.json")
        repository = TenantRepository(base, organization_id="ORG-TRANSFORM-EVAL", actor="ANALYST")
        jobs = MediaProcessingJobService(repository)
        for index in range(2):
            jobs.create_job(job_id=f"MEDIA-JOB-EVAL-{index}", asset_id=f"FILM-EVAL-{index}", operation="thumbnail", payload={"file_path":str(source), "output_path":str(root / f"thumb-{index}.jpg"), "allowed_roots":[str(root)]}, requested_by="ANALYST")
        report = MediaTransformOrchestrator(repository).run_batch(actor="ANALYST", worker_id="WORKER-EVAL", max_jobs=1, allowed_roots=[str(root)], runner=lambda arguments: (0, "", ""))
        invalid_base = JsonRepository(root / "invalid-state.json")
        invalid_repository = TenantRepository(invalid_base, organization_id="ORG-TRANSFORM-EVAL", actor="ANALYST")
        invalid = MediaProcessingJobService(invalid_repository).create_job(job_id="MEDIA-JOB-EVAL-INVALID", asset_id="FILM-EVAL-INVALID", operation="transcode", payload={"file_path":str(root / "missing.mp4"), "output_path":str(root / "out.mp4"), "allowed_roots":[str(root)]}, requested_by="ANALYST")
        invalid_report = MediaTransformOrchestrator(invalid_repository).run_batch(actor="ANALYST", worker_id="WORKER-EVAL-2", max_jobs=1, allowed_roots=[str(root)], runner=lambda arguments: (_ for _ in ()).throw(AssertionError("runner must not execute")))
        return {"bounded":report["selected_count"] == 1 and len(jobs.list_jobs(status="queued")) == 1, "persisted":report["completed_count"] == 1 and repository.get("media_transform_batches", report["id"]) is not None, "safe":invalid_report["failed_count"] == 1 and invalid["status"] == "queued"}


def _source_fetcher_safety_eval() -> bool:
    from unittest.mock import patch
    from .source_connectors import _default_fetcher
    class Headers:
        def items(self):
            return [("content-type", "text/plain")]
    class Response:
        headers = Headers()
        def geturl(self):
            return "https://outside.example.test/rules"
        def read(self, limit):
            return b"outside"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    with patch("urllib.request.urlopen", return_value=Response()):
        try:
            _default_fetcher("https://rules.example.test/nfl", 100, allowed_domains=["rules.example.test"])
        except ValueError as exc:
            return "redirect" in str(exc)
    return False


def _knowledge_search_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        base = JsonRepository(Path(directory) / "state.json")
        tenant = TenantRepository(base, organization_id="ORG-KNOWLEDGE-EVAL", actor="ANALYST")
        tenant.put("knowledge_items", "KNOWLEDGE-EVAL", {"id":"KNOWLEDGE-EVAL", "organization_id":"ORG-KNOWLEDGE-EVAL", "normalized_claim":"NFL red zone rule evidence", "classification":"rule", "state":"current", "source_id":"SOURCE-EVAL", "citation":{"source_ref":"https://rules.example.test/nfl", "location":"rule 1"}}, actor="ANALYST", reason="knowledge_search_eval_seed")
        service = KnowledgeRetrievalService(tenant)
        results = service.search(query="red zone", limit=1)
        other = TenantRepository(base, organization_id="ORG-OTHER-KNOWLEDGE", actor="ANALYST")
        other_results = KnowledgeRetrievalService(other).search(query="red zone", limit=1)
        try:
            service.search(limit=501)
            bounded = False
        except ValueError:
            bounded = True
        return {"retrieved":len(results) == 1 and results[0]["record"].get("citation", {}).get("source_ref") is not None, "scoped":not other_results, "bounded":bounded}


def _scheduled_operations_eval() -> dict[str, bool]:
    with tempfile.TemporaryDirectory() as directory:
        tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEDULE-EVAL", actor="OWNER")
        service = ScheduledOperationsService(tenant, environment="validation")
        plan = service.run(actor="OWNER", worker_id="WORKER-EVAL", execute=False, max_sources=2, max_transforms=3, retention_days=30)
        production = ScheduledOperationsService(tenant, environment="production", control_root=Path(__file__).resolve().parents[1]).run(actor="OWNER", worker_id="WORKER-EVAL", execute=True)
        return {"dry_run":plan["dry_run"] and plan["max_sources"] == 2 and plan["max_transforms"] == 3 and not plan["destructive_action_required"], "blocked":production["status"] == "blocked" and "Stage 0" in production["blocker"]}


def _release_validation_eval() -> dict[str, bool]:
    root = Path(__file__).resolve().parents[2]
    result = validate_release_artifacts(root=root, eval_result={"status":"passed"})
    return {"artifacts":result["artifact_status"] == "complete" and not result["missing_artifacts"], "approval":result["status"] == "blocked" and result["human_approval_required"], "non_deploying":result["deploy_performed"] is False}


def _deployment_contract_eval() -> dict[str, bool]:
    result = validate_deployment_contract(path=Path(__file__).resolve().parents[2] / "deployment" / "nfl-fidos-deployment.json")
    return {"valid":result["status"] == "valid" and result["service_count"] == 3, "safe":result["production_implementation_allowed"] is False}


def _sources_for_eval(service: FootballIntelligenceService, organization_id: str, actor: str, fetcher: Callable) -> Any:
    from .source_connectors import SourceConnectorService
    return SourceConnectorService(TenantRepository(service.repository, organization_id=organization_id, actor=actor), fetcher=fetcher)


def _stage0_registry() -> dict[str, Any]:
    """Load the controlled Stage 0A registry for the gate eval."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "control" / "stage-0a-registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _system_architecture() -> dict[str, Any]:
    """Load the controlled Stage 1 architecture artifact for the gate eval."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "architecture" / "system-architecture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _scheme_bible() -> dict[str, Any]:
    """Load the controlled offensive/defensive scheme-family library."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "scheme" / "scheme-bible.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _special_teams_bible() -> dict[str, Any]:
    """Load the controlled Stage 8 special-teams library."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "special_teams" / "special-teams-bible.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _extended_eval_play() -> dict[str, Any]:
    return {
        **_play(), "play_family_id":"PLAY-FAM-EVAL", "checks":[{"role":"QB","text":"confirm rotation"}],
        "situational_variants":[{"situation":"third_down","variant":"hot"}], "opponent_notes":["check pressure"],
        "coaching_notes":["eyes before feet"], "install_level":"game_ready", "dependencies":["SCHEME-EVAL-001"],
        "approval":{"state":"draft", "approver":None, "decision_ref":None},
        "assignments":[{"role":"QB","assignment":"read","responsibility":"read safety"},{"role":"C","assignment":"block","responsibility":"set protection"}],
    }


def _visual_eval_play() -> dict[str, Any]:
    return build_visual_play(
        visual_id="VISUAL-EVAL", play={"id":"PLAY-EVAL-001", "version":"0.1.0"},
        players=[{"id":"P-QB-EVAL","role":"QB","position":{"x":0,"y":26.5}},{"id":"P-WR-EVAL","role":"X","position":{"x":0,"y":10}}],
        paths=[{"player_id":"P-WR-EVAL","notation":"route","points":[{"x":0,"y":10},{"x":8,"y":10},{"x":20,"y":18}]}],
        timeline=[{"time_ms":0,"event":"snap"},{"time_ms":500,"event":"break"}],
        role_views=["coach","QB","X"], accessibility=["role labels", "text read progression"],
    )


def _eval_drill() -> dict[str, Any]:
    return build_drill(
        drill_id="DRILL-EVAL", name="Read and replace", drill_type="individual", position="QB", target_skill="coverage recognition", competencies=["CAP-003"],
        classification={"contact_level":"non_contact","decision_load":"high"}, setup={"space":"half_field","equipment":["cones"]}, dose={"minutes":8,"reps":12,"intensity":"moderate"},
        coaching_cues=["eyes before feet"], common_errors=["late confirmation"], corrections=["reset vision"], kpis=[{"name":"correct_read_rate","target":0.8}], regressions=["static shell"], progressions=["add rotation"], film_angles=["wide"], safety={"controls":["no contact"]},
    )


def _eval_practice() -> dict[str, Any]:
    return build_practice_architecture(
        practice_id="PRACTICE-EVAL", team_context="TEAM-EVAL", season_phase="regular_season", week_context="week_1", objective="install third down", opponent_priorities=["pressure"],
        periods=[{"id":"PERIOD-EVAL","type":"individual","objective":"read","owner":"QB_COACH","players":["QB"],"minutes":10,"reps":12,"learning_rationale":"read timing","load_rationale":"moderate"}], staff_available=["QB_COACH"], facility_constraints=[], load_controls={"max_total_minutes":120,"max_reps_by_position":{"QB":40}}, restrictions=[],
    )


def _performance_bible() -> dict[str, Any]:
    """Load the controlled Stage 13 performance-domain bible."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "performance" / "performance-domain-bible.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _film_observation() -> dict[str, Any]:
    return build_film_observation(observation_id="FILM-OBS-EVAL", clip_id="CLIP-EVAL", asset_id="FILM-EVAL", domain="coverage", label="two_high", team="TEAM-EVAL", opponent="TEAM-OPP", situation={"down":3,"distance":6}, source_frame="00:01:02.100", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-EVAL", evidence="safety rotation visible")


def _scout_profile_eval(source_kind: str = "licensed_film") -> dict[str, Any]:
    return build_opponent_profile(profile_id="OPP-PROFILE-EVAL", opponent="OPP-EVAL", season="2026", schedule_context={"week":1}, roster_context={"source":"public"}, offense={"formations":[]}, defense={"coverages":[]}, special_teams={"units":[]}, sources=[{"kind":source_kind,"ref":"FILM-EVAL","captured_at":"2026-08-23"}])


def _scout_report_eval() -> dict[str, Any]:
    return build_situational_scouting_report(report_id="SCOUT-REPORT-EVAL", opponent="OPP-EVAL", situation={"down":3,"distance":"medium"}, claims=[{"classification":"observed","confidence":"moderate","uncertainty":["sample"],"evidence_refs":["FILM-EVAL"]}], sample_size=8, source_refs=["FILM-EVAL"], analyst="SCOUT-EVAL")


def _analytics_dictionary() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "analytics" / "metrics-dictionary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _analytics_observation() -> dict[str, Any]:
    return calculate_metric(definition=_analytics_dictionary()["metrics"][0], numerator=6, denominator=10, context={"team":"TEAM-EVAL","situation":"third_down"}, source={"kind":"charting","ref":"DATA-EVAL"}, observation_ids=["PLAY-EVAL-1"])


def _game_plan_eval() -> dict[str, Any]:
    return build_weekly_game_plan(
        plan_id="GAMEPLAN-EVAL", team_context="TEAM-EVAL", week_context="week_1", identity={"offense":"wide_zone","defense":"match"}, assumptions=["sample is current"], evidence_refs=["SCOUT-EVAL"], offense={"base_calls":["run"]}, defense={"base_calls":["fit"]}, special_teams={"base_calls":["punt"]}, opening_script=[{"call":"run","owner":"OC"}], base_calls=[{"call":"run","owner":"OC"}], shot_plan=[{"call":"play_action","owner":"OC"}], pressure_answers=[{"threat":"pressure","answer":"hot","owner":"OC"}], situational_plans=[{"situation":"third_down","primary":"concept_a","opponent_responses":["pressure"],"counters":["hot"]}], matchups=[{"player":"WR1","opponent":"CB1","plan":"release"}], contingencies=[{"id":"TRIGGER-EVAL","trigger":"pressure_rate>40%","response":"change protection","owner":"OC","evidence_refs":["FILM-EVAL"]}], ownership={"head_coach":"HC","offense":"OC","defense":"DC","special_teams":"STC"}, teaching_outputs=[{"role":"QB","message":"confirm pressure"}], in_game_update={"cadence":"series","owner":"HC"},
    )


def _rules_model_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "rules" / "rules-knowledge-model.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _research_item_eval() -> dict[str, Any]:
    source = register_research_source(source_id="SOURCE-EVAL", tier="tier_1_authoritative", kind="official_rulebook", ref="RULEBOOK-EVAL", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="RESEARCH-EVAL")
    return ingest_knowledge_item(item_id="KNOWLEDGE-EVAL", question="rule question", source=source, raw_excerpt="source excerpt", normalized_claim="normalized claim", classification="rule", context={"jurisdiction":"NFL"}, ontology_refs=["OBJ-004"], state="current", extractor="AGT-013", confidence="high", uncertainty=["verify exceptions"])


def _eval_bible() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "governance" / "eval-bible.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _data_architecture_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "data" / "data-architecture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _ux_architecture_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "ux" / "ux-architecture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _engineering_architecture_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "engineering" / "engineering-architecture.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _mvp_strategy_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "delivery" / "mvp-strategy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _master_spec_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "control" / "master-codex-build-spec.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _core_slice_eval() -> dict[str, Any]:
    """Run the first MVP vertical slice against the repository contract."""
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        repository = JsonRepository(f"{directory}/state.json")
        service = FootballIntelligenceService(repository)
        drill = _eval_drill()
        package = service.create_core_play_slice(
            play=_extended_eval_play(), role="QB", drill=drill, actor="COACH-EVAL", decision_ref="DEC-SLICE-EVAL"
        )
        approved = service.approve_core_play_slice(play_id="PLAY-EVAL-001", approver="OWNER-EVAL", decision_ref="DEC-SLICE-EVAL")
        return {
            "package": package,
            "view_status": repository.get("play_views", package["play_view_id"])["status"],
            "drill_has_kpi": bool(repository.get("drills", package["drill_id"])["kpis"]),
            "approved": approved,
            "play_status": repository.get("plays", "PLAY-EVAL-001")["status"],
            "play_events": len(repository.history(collection="plays", record_id="PLAY-EVAL-001")),
        }


def _evidence_slice_eval() -> dict[str, Any]:
    import tempfile
    asset = register_film_asset(asset_id="FILM-EVAL-SLICE", uri="authorized://film/eval", duration_seconds=90, source={"kind":"licensed_film", "ref":"LICENSE-EVAL"}, captured_at="2026-08-23", team_context="TEAM-EVAL")
    clip = create_film_clip(clip_id="CLIP-EVAL-SLICE", asset=asset, start_seconds=5, end_seconds=12, team="TEAM-EVAL", opponent="TEAM-OPP", situation="third_down")
    observation = build_film_observation(observation_id="FILM-OBS-EVAL-SLICE", clip_id=clip["id"], asset_id=asset["id"], domain="coverage", label="two_high", team="TEAM-EVAL", opponent="TEAM-OPP", situation={"down":3,"distance":6}, source_frame="00:00:07.000", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-EVAL", evidence="rotation visible")
    report = build_situational_scouting_report(report_id="SCOUT-REPORT-EVAL-SLICE", opponent="TEAM-OPP", situation={"down":3,"distance":"medium"}, claims=[{"classification":"observed","confidence":"moderate","uncertainty":["sample"],"evidence_refs":[clip["id"]]}], sample_size=12, source_refs=[clip["id"]], analyst="SCOUT-EVAL")
    metric = calculate_metric(definition=_analytics_dictionary()["metrics"][0], numerator=7, denominator=12, context={"team":"TEAM-EVAL","opponent":"TEAM-OPP","situation":"third_down"}, source={"kind":"charting","ref":clip["id"]}, observation_ids=[observation["id"]])
    with tempfile.TemporaryDirectory() as directory:
        repository = JsonRepository(f"{directory}/state.json")
        service = FootballIntelligenceService(repository)
        package = service.create_evidence_intelligence_slice(asset=asset, clip=clip, observation=observation, scouting_report=report, metric_observation=metric, analyst="SCOUT-EVAL", qa_reviewer="COACH-EVAL")
        return {"package":package, "clip_asset_linked":repository.get("film_clips", clip["id"])["asset_id"] == asset["id"], "scouting_status":repository.get("scouting_reports", report["id"])["status"], "metric_status":repository.get("metric_observations", metric["id"])["status"], "qa_status":repository.get("film_qa", f"QA-{observation['id']}")["status"], "analytics_status":repository.get("analytics_reports", f"ANALYTICS-REPORT-{metric['id']}")["status"]}


def _weekly_delivery_eval() -> dict[str, Any]:
    import tempfile
    plan = build_weekly_game_plan(plan_id="GAMEPLAN-EVAL-SLICE", team_context="TEAM-EVAL", week_context="week_1", identity={"offense":"wide_zone", "defense":"match"}, assumptions=["sample is current"], evidence_refs=["SCOUT-EVAL"], offense={"base_calls":["run"]}, defense={"base_calls":["fit"]}, special_teams={"base_calls":["punt"]}, opening_script=[{"call":"run", "owner":"OC"}], base_calls=[{"call":"run", "owner":"OC"}], shot_plan=[{"call":"play_action", "owner":"OC"}], pressure_answers=[{"threat":"pressure", "answer":"hot", "owner":"OC"}], situational_plans=[{"situation":"third_down", "primary":"concept_a", "opponent_responses":["pressure"], "counters":["hot"]}], matchups=[{"player":"WR1", "opponent":"CB1", "plan":"release"}], contingencies=[{"id":"TRIGGER-EVAL-SLICE", "trigger":"pressure_rate>40%", "response":"change protection", "owner":"OC", "evidence_refs":["SCOUT-EVAL"]}], ownership={"head_coach":"HC", "offense":"OC", "defense":"DC", "special_teams":"STC"}, teaching_outputs=[{"role":"QB", "message":"confirm pressure"}], in_game_update={"cadence":"series", "owner":"HC"})
    recommendation = build_rule_aware_recommendation(recommendation_id="RULE-REC-EVAL-SLICE", question="fourth down", rule_facts=[{"id":"RULE-KB-005", "authority":"authoritative", "fact":"rule fact"}], strategy_recommendation="compare options", situation={"down":4,"distance":2}, requester_role="coach_staff", rule_refs=["RULE-KB-005"], evidence_refs=["SCOUT-EVAL"])
    with tempfile.TemporaryDirectory() as directory:
        service = FootballIntelligenceService(JsonRepository(f"{directory}/state.json"))
        blocked = service.create_weekly_delivery_package(game_plan=plan, rule_recommendation=recommendation, eval_result={"status":"passed"}, capability_ids=["CAP-018"], feature_gates=[{"id":"GATE-EVAL-018", "capability_id":"CAP-018", "status":"complete"}], actor="COACH-EVAL")
        approved = service.create_weekly_delivery_package(game_plan=plan, rule_recommendation=recommendation, eval_result={"status":"passed"}, capability_ids=["CAP-018"], feature_gates=[{"id":"GATE-EVAL-018", "capability_id":"CAP-018", "status":"complete"}], actor="COACH-EVAL", human_approval="APPROVAL-EVAL")
        return {"plan_status":plan["status"], "rule_status":recommendation["status"], "blocked_status":blocked["status"], "approved_status":approved["status"]}


def _auth_eval() -> dict[str, Any]:
    token = issue_token(subject="ANALYST-EVAL", role="analyst", organization_id="ORG-EVAL", secret="eval-secret", ttl_seconds=60, now=100)
    principal = verify_token(token, secret="eval-secret", now=120)
    return {
        "principal_org": principal.organization_id,
        "can_scout": authorize_principal(principal=principal, action="create_scouting_claim", organization_id="ORG-EVAL")["allowed"],
        "can_lock": authorize_principal(principal=principal, action="lock_artifact", organization_id="ORG-EVAL")["allowed"],
        "cross_org_allowed": authorize_principal(principal=principal, action="create_scouting_claim", organization_id="ORG-OTHER")["allowed"],
    }


def _tenant_eval() -> dict[str, Any]:
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        repository = JsonRepository(f"{directory}/state.json")
        scoped = TenantRepository(repository, organization_id="ORG-EVAL", actor="OWNER-EVAL")
        scoped.put("plays", "PLAY-TENANT-EVAL", {"id":"PLAY-TENANT-EVAL", "organization_id":"ORG-EVAL", "status":"draft"})
        mismatch_rejected = False
        try:
            scoped.put("plays", "PLAY-OTHER-EVAL", {"id":"PLAY-OTHER-EVAL", "organization_id":"ORG-OTHER"})
        except PermissionError:
            mismatch_rejected = True
        other = TenantRepository(repository, organization_id="ORG-OTHER", actor="OWNER-OTHER")
        return {"mismatch_rejected": mismatch_rejected, "hidden": other.get("plays", "PLAY-TENANT-EVAL") is None, "history_scoped": len(scoped.history(collection="plays")) == 1}


def _ui_eval() -> dict[str, Any]:
    from pathlib import Path
    document = (Path(__file__).resolve().parents[2] / "ui" / "operator-dashboard.html").read_text(encoding="utf-8")
    return {"routes": "/v1/control" in document and "/v1/evals" in document, "approval": "human review and approval" in document, "accessible": 'aria-label="Primary navigation"' in document and 'lang="en"' in document}


def _media_eval() -> dict[str, Any]:
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "eval.mp4"
        path.write_bytes(b"authorized film fixture")
        registered = ingest_media_file(file_path=path, asset_id="FILM-MEDIA-EVAL", organization_id="ORG-EVAL", source={"kind":"licensed_film", "ref":"LICENSE-EVAL"}, captured_at="2026-08-23", allowed_roots=[root])
        rejected = ingest_media_file(file_path=root / "bad.exe", asset_id="FILM-MEDIA-EVAL-BAD", organization_id="ORG-EVAL", source={"kind":"unknown", "ref":"BAD"}, captured_at="2026-08-23", allowed_roots=[root])
        return {"registered": registered["status"] == "registered" and registered["organization_id"] == "ORG-EVAL", "rejected": rejected["status"] == "rejected", "digest": registered["sha256"] is not None and len(registered["sha256"]) == 64}


def _observability_eval() -> dict[str, Any]:
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        recorder = ObservabilityRecorder(f"{directory}/events.jsonl")
        with recorder.span(operation="eval_operation", actor="AGT-EVAL", organization_id="ORG-EVAL"):
            pass
        try:
            with recorder.span(operation="eval_failure", actor="AGT-EVAL", organization_id="ORG-EVAL"):
                raise RuntimeError("fixture")
        except RuntimeError:
            pass
        events = recorder.read()
        return {"success": events[0]["status"] == "ok", "failure": events[1]["status"] == "error", "identity": bool(events[0]["event_id"] and events[0]["request_id"] and events[0]["organization_id"])}


def _migration_eval() -> dict[str, Any]:
    import tempfile
    from pathlib import Path
    from .sqlite_repository import SqliteRepository
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "state.db"
        repository = SqliteRepository(database)
        repository.put("plays", "PLAY-MIGRATION-EVAL", {"id":"PLAY-MIGRATION-EVAL", "organization_id":"ORG-EVAL"}, actor="OWNER-EVAL", reason="fixture")
        repository.close()
        planned = apply_migrations(database, dry_run=True)
        applied = apply_migrations(database)
        migrated = SqliteRepository(database)
        history = len(migrated.history(record_id="PLAY-MIGRATION-EVAL")) == 1 and migrated.get("plays", "PLAY-MIGRATION-EVAL")["organization_id"] == "ORG-EVAL"
        migrated.close()
        return {"planned": planned["status"] == "planned", "current": applied["version"] == 1 and inspect_migrations(database)["version"] == 1, "history": history}


def _film_room_eval() -> dict[str, Any]:
    observation = build_film_observation(observation_id="FILM-OBS-ROOM-EVAL", clip_id="CLIP-ROOM-EVAL", asset_id="FILM-ROOM-EVAL", domain="coverage", label="two_high", team="TEAM-EVAL", opponent="TEAM-OPP", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-EVAL", evidence="rotation visible")
    observation["organization_id"] = "ORG-EVAL"
    index = FilmRoomIndex(organization_id="ORG-EVAL")
    index.add(observation)
    session = build_annotation_session(session_id="ANNOTATION-EVAL", clip_id="CLIP-ROOM-EVAL", organization_id="ORG-EVAL", annotator="SCOUT-EVAL", allowed_domains=["coverage"], source_refs=["CLIP-ROOM-EVAL"])
    corrected = append_annotation(session=session, observation={**observation, "confidence":"low", "status":"needs_review"})
    quiz = build_film_quiz(quiz_id="QUIZ-EVAL", title="Coverage quiz", organization_id="ORG-EVAL", role="QB", clip_ids=["CLIP-ROOM-EVAL"], questions=[{"id":"Q-EVAL", "prompt":"shell", "expected_answer":"two_high", "evidence_refs":["CLIP-ROOM-EVAL"]}], owner="COACH-EVAL")
    attempt = submit_film_quiz(attempt_id="QUIZ-ATTEMPT-EVAL", quiz=quiz, participant="PLAYER-EVAL", answers={"Q-EVAL":"two_high"})
    return {"search": len(index.search(opponent="TEAM-OPP", label="two_high")) == 1, "correction": corrected["correction_required"], "quiz": attempt["score"] == 1.0 and attempt["human_review_required"] and attempt["graded_answers"][0]["evidence_refs"] == ["CLIP-ROOM-EVAL"]}


def _runtime_eval() -> dict[str, Any]:
    local = load_config(environ={"NFL_FIDOS_ENV":"local", "NFL_FIDOS_PORT":"9000", "NFL_FIDOS_AUTH_SECRET":"local-secret"})
    production = load_config(environ={"NFL_FIDOS_ENV":"production", "NFL_FIDOS_AUTH_SECRET":"x" * 32})
    missing_secret = False
    try:
        load_config(environ={"NFL_FIDOS_ENV":"validation"})
    except ValueError:
        missing_secret = True
    return {"local": local.port == 9000 and local.environment == "local", "production": production.environment == "production", "missing_secret": missing_secret}


def _ontology_depth_eval() -> dict[str, Any]:
    resolver = OntologyResolver()
    categories = {term.get("category") for term in resolver.terms.values()}
    required = {"position", "personnel", "formation", "pass_concept", "run_concept", "coverage", "front", "pressure", "special_teams", "situation"}
    return {"domains": required.issubset(categories), "terms": all(resolver.resolve(label)["status"] == "resolved" for label in ("running back", "pistol", "quarters", "simulated pressure", "punt")), "valid": resolver.validate() == []}


def _agent_bible_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    bible = json.loads((Path(__file__).resolve().parents[2] / "agents" / "agent-organization-bible.json").read_text(encoding="utf-8"))
    result = validate_agent_bible(bible)
    handoffs = {item.get("from_family") for item in bible.get("handoff_matrix", [])} >= {"orchestration", "film", "scouting", "rules", "governance"}
    requirements = all(any(keyword in item.lower() for item in bible.get("prompt_requirements", [])) for keyword in ("nfl scope", "uncertainty", "human review")) and len(bible.get("agent_eval_requirements", [])) >= 6
    return {"valid": result["status"] == "valid" and result["role_count"] == 16, "handoffs": handoffs, "requirements": requirements}


def _player_development_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    bible = json.loads((Path(__file__).resolve().parents[2] / "development" / "player-development-bible.json").read_text(encoding="utf-8"))
    result = validate_player_development_bible(bible)
    evidence = all(position.get("evidence") and position.get("assessment_methods") and position.get("drills") for position in bible["position_families"])
    controls = all(field in bible and bible[field] for field in ("mastery_levels", "idp_requirements", "assessment_rules", "learning_path_requirements"))
    return {"coverage": result["status"] == "valid" and result["position_count"] >= 12 and result["role_count"] >= 20, "evidence": evidence, "controls": controls}


def _staff_bible_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    bible = json.loads((Path(__file__).resolve().parents[2] / "staff" / "coaching-staff-bible.json").read_text(encoding="utf-8"))
    result = validate_staff_bible(bible)
    return {"roles": result["status"] == "valid" and result["role_count"] == 8, "pathway": bible.get("development_pathway") == ["observe","teach","practice","diagnose","adapt","review"] and all(item.get("dimensions") for item in bible.get("role_trees", [])), "boundaries": len(bible.get("collaboration_model", [])) >= 5 and len(bible.get("boundaries", [])) >= 4}


def _scheme_architecture_eval() -> dict[str, Any]:
    import json
    from pathlib import Path
    architecture = json.loads((Path(__file__).resolve().parents[2] / "scheme" / "scheme-architecture.json").read_text(encoding="utf-8"))
    result = validate_scheme_architecture(architecture)
    counters = all(item.get("trigger") and item.get("evidence_required") and item.get("counter_counter") for unit in ("offense", "defense") for item in architecture[unit]["counter_library"])
    return {"offense": result["status"] == "valid" and len(architecture["offense"]["concept_graph"]) >= 5, "defense": result["status"] == "valid" and all(key in architecture["defense"]["taxonomies"] for key in ("fronts","techniques","coverages","pressures","checks")), "counters": counters}


def _visual_render_eval() -> dict[str, Any]:
    from .visual_playbook import build_visual_play
    visual = build_visual_play(visual_id="VISUAL-EVAL-RENDER", play={"id":"PLAY-EVAL-RENDER","version":"0.1.0"}, players=[{"id":"P-QB-EVAL","role":"QB","position":{"x":15,"y":26.5}},{"id":"P-X-EVAL","role":"X","position":{"x":10,"y":10}}], paths=[{"player_id":"P-X-EVAL","notation":"route","points":[{"x":10,"y":10},{"x":25,"y":10},{"x":45,"y":18}]}], timeline=[{"time_ms":0,"event":"snap"}], role_views=["coach","QB","X"], accessibility=["role labels","text progression"])
    canonical = render_visual_svg(visual=visual, role="QB")
    what_if = render_visual_svg(visual=visual, role="X", scenario={"type":"rotation"})
    return {"canonical": 'data-mode="canonical"' in canonical and "QB" in canonical, "what_if": 'data-mode="what-if"' in what_if and "HUMAN REVIEW REQUIRED" in what_if, "accessibility": 'role="img"' in canonical and 'aria-label' in canonical and "canonical play data is not replaced" in what_if}


def _knowledge_graph_eval() -> dict[str, Any]:
    graph = KnowledgeGraph(organization_id="ORG-EVAL")
    node = graph.add_node(node_id="NODE-EVAL-1", label="validated play", node_type="play", source_refs=["PB-EVAL"], context={"season":"2026"}, classification="team_rule", confidence="high", state="current")
    other = graph.add_node(node_id="NODE-EVAL-2", label="pressure tendency", node_type="tendency", source_refs=["FILM-EVAL"], context={"down":3}, classification="observed_tendency", confidence="moderate", state="current")
    edge = graph.add_edge(edge_id="EDGE-EVAL-1", from_id="NODE-EVAL-2", to_id="NODE-EVAL-1", relation="informs", source_refs=["FILM-EVAL"], context={"situation":"third_down"})
    graph.add_node(node_id="NODE-EVAL-H", label="hypothesis", node_type="claim", source_refs=["OBS-EVAL"], context={"sample":1}, classification="hypothesis", confidence="low", state="proposed")
    weak = graph.add_edge(edge_id="EDGE-EVAL-H", from_id="NODE-EVAL-H", to_id="NODE-EVAL-1", relation="supports", source_refs=["OBS-EVAL"], context={"sample":1}, confidence="low")
    return {"nodes":node["organization_id"] == "ORG-EVAL" and node["source_refs"] == ["PB-EVAL"] and other["classification"] == "observed_tendency", "edges":edge["canonical_allowed"] and graph.neighbors("NODE-EVAL-1")[0]["node"]["id"] == "NODE-EVAL-2", "review":not weak["canonical_allowed"] and weak["human_review_required"]}


def _film_room_service_eval() -> dict[str, Any]:
    import tempfile
    from pathlib import Path
    from .film_intelligence import build_film_observation
    from .repository import JsonRepository
    from .tenant_repository import TenantRepository
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "state.json"
        observation = build_film_observation(observation_id="FILM-OBS-SVC-EVAL", clip_id="CLIP-SVC-EVAL", asset_id="FILM-SVC-EVAL", domain="coverage", label="two_high", team="TEAM-EVAL", opponent="TEAM-OPP", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-EVAL", evidence="rotation visible")
        observation["organization_id"] = "ORG-EVAL"
        service = FilmRoomService(TenantRepository(JsonRepository(path), organization_id="ORG-EVAL", actor="SCOUT-EVAL"))
        service.save_observation(observation, actor="SCOUT-EVAL")
        recreated = FilmRoomService(TenantRepository(JsonRepository(path), organization_id="ORG-EVAL", actor="COACH-EVAL"))
        search = len(recreated.search(opponent="TEAM-OPP")) == 1
        quiz = recreated.create_quiz(quiz_id="QUIZ-SVC-EVAL", title="Coverage", role="QB", clip_ids=["CLIP-SVC-EVAL"], questions=[{"id":"Q-SVC-EVAL", "prompt":"shell", "expected_answer":"two_high", "evidence_refs":["CLIP-SVC-EVAL"]}], owner="COACH-EVAL", actor="COACH-EVAL")
        attempt = recreated.submit_quiz(attempt_id="QUIZ-ATTEMPT-SVC-EVAL", quiz_id=quiz["id"], participant="PLAYER-EVAL", answers={"Q-SVC-EVAL":"two_high"}, actor="PLAYER-EVAL")
        return {"search":search, "quiz":attempt["score"] == 1.0 and attempt["human_review_required"] and len(recreated.repository.history(collection="film_quiz_attempts")) == 1, "scope":all(record.get("organization_id") == "ORG-EVAL" for record in recreated.repository.list("film_observations") + recreated.repository.list("film_quizzes") + recreated.repository.list("film_quiz_attempts"))}
