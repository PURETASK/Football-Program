"""Rehearse the complete synthetic organization operating set end to end."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable

from nfl_fidos.organization_analytics import approve_organization_analytics_package, build_organization_analytics_package
from nfl_fidos.organization_doctrine import approve_organization_doctrine, build_organization_doctrine
from nfl_fidos.organization_drill_validation import approve_organization_drill_validation, build_organization_drill_validation
from nfl_fidos.organization_game_plan import approve_organization_game_plan, build_organization_game_plan
from nfl_fidos.organization_media_review import approve_organization_media_review, build_organization_media_review
from nfl_fidos.organization_onboarding import approve_onboarding_package, build_onboarding_package
from nfl_fidos.organization_operating_bundle import COMPONENT_COLLECTIONS, REQUIRED_COMPONENTS, build_organization_operating_bundle, load_persisted_organization_components
from nfl_fidos.organization_performance import approve_organization_performance, build_organization_performance
from nfl_fidos.organization_player_development import approve_organization_player_development, build_organization_player_development
from nfl_fidos.organization_play_corpus import approve_organization_play_corpus, build_organization_play_corpus
from nfl_fidos.organization_scouting import approve_organization_scouting_package, build_organization_scouting_package
from nfl_fidos.organization_special_teams import approve_organization_special_teams, build_organization_special_teams
from nfl_fidos.organization_staff_review import approve_organization_staff_package, build_organization_staff_package
from nfl_fidos.organization_population_readiness import build_organization_population_readiness
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


ORG = "ORG-SYNTHETIC-OPERATING-SET"
SEASON = "2026"
TEAM = "TEAM-SYNTHETIC-OPERATING-SET"
SOURCE = "AUTH-SOURCE-SYNTHETIC-001"


def _validate_then_approve(package: dict[str, Any], approver: str, fn: Callable[..., dict[str, Any]], decision: str, argument_name: str = "package") -> dict[str, Any]:
    if package.get("status") not in {"under_review", "ready_for_owner_review"}:
        raise ValueError(f"synthetic package did not reach owner review: {package.get('id')} ({package.get('status')})")
    return fn(**{argument_name: package}, approver=approver, approver_role="program_owner", decision_ref=decision)


def _build_components() -> dict[str, dict[str, Any]]:
    onboarding = build_onboarding_package(organization_id=ORG, name="Synthetic NFL Operating Organization", season=SEASON, team_id=TEAM, people=[], terminology_version="TERM-0.1.0", owner="OWNER-SYNTHETIC", source={"kind": "synthetic_fixture", "ref": SOURCE})
    onboarding = approve_onboarding_package(organization=onboarding["organization"], terminology_bundle=onboarding["terminology_bundle"], approver="OWNER-SYNTHETIC", decision_ref="DEC-SYNTHETIC-ONBOARDING")
    components: dict[str, dict[str, Any]] = {"organization_context": onboarding["organization"], "terminology_bundle": onboarding["terminology_bundle"]}

    doctrine = build_organization_doctrine(doctrine_id="ORG-DOCTRINE-SYNTHETIC-001", organization_id=ORG, team_context=TEAM, season=SEASON, scheme_family_ids=["SCHEME-FAM-OFF-001", "SCHEME-FAM-DEF-001"], special_teams_unit_ids=["ST-UNIT-001"], source_refs=[SOURCE], compiler="COACH-SYNTHETIC")
    components["doctrine"] = _validate_then_approve(doctrine, "OWNER-SYNTHETIC", approve_organization_doctrine, "DEC-SYNTHETIC-DOCTRINE", "doctrine")

    play = {"id": "PLAY-SYNTHETIC-001", "version": "0.1.0", "unit": "offense", "team_context": TEAM, "situation": {"down": 1, "distance": 10, "field_zone": "open_field"}, "personnel": "11", "formation": "shotgun", "assignments": [{"role": "QB", "assignment": "read shell"}, {"role": "C", "assignment": "set protection"}], "source": {"kind": "team_playbook", "ref": SOURCE}, "status": "draft"}
    corpus = build_organization_play_corpus(corpus_id="ORG-PLAY-CORPUS-SYNTHETIC-001", organization_id=ORG, team_context=TEAM, season=SEASON, plays=[play], source_refs=[SOURCE], compiler="COACH-SYNTHETIC")
    components["play_corpus"] = _validate_then_approve(corpus, "OWNER-SYNTHETIC", approve_organization_play_corpus, "DEC-SYNTHETIC-PLAY", "corpus")

    player_development = build_organization_player_development(package_id="ORG-PLAYER-DEV-SYNTHETIC-001", organization_id=ORG, team_context=TEAM, season=SEASON, players=[{"player_id": "PLAYER-SYNTHETIC-001", "position": "QB", "owner": "COACH-SYNTHETIC", "objectives": [{"capability_id": "CAP-001", "outcome": "execute assignment", "measure": "4 of 5 reps"}], "mastery_records": [{"record_id": "MASTERY-SYNTHETIC-001", "capability_id": "CAP-001", "current_level": "developing", "target_level": "functional", "evidence": [{"source_ref": SOURCE, "observation": "practice rep"}], "next_actions": ["repeat read progression"]}]}], compiler="COACH-SYNTHETIC")
    components["player_development"] = _validate_then_approve(player_development, "OWNER-SYNTHETIC", approve_organization_player_development, "DEC-SYNTHETIC-PLAYER")

    staff = build_organization_staff_package(package_id="ORG-STAFF-SYNTHETIC-001", organization_id=ORG, team_context=TEAM, season=SEASON, staff=[{"person_id": "STAFF-SYNTHETIC-001", "role": "head_coach", "review_owner": "OWNER-SYNTHETIC"}], evaluations=[{"evaluation_id": "EVAL-COACH-SYNTHETIC-001", "coach_id": "STAFF-SYNTHETIC-001", "role": "head_coach", "ratings": {"leadership": 4, "culture": 4, "decision_quality": 3, "staff_alignment": 4, "program_evaluation": 3}, "evidence": [{"source_ref": SOURCE, "observation": "weekly review artifact"}], "evaluator": "OWNER-SYNTHETIC"}], compiler="COACH-SYNTHETIC")
    components["staff_review"] = _validate_then_approve(staff, "OWNER-SYNTHETIC", approve_organization_staff_package, "DEC-SYNTHETIC-STAFF")

    drills = build_organization_drill_validation(validation_id="ORG-DRILL-VALIDATION-SYNTHETIC-001", organization_id=ORG, season=SEASON, position="QB", selected_drill_ids=["DRILL-QB-001", "VARIANT-DRILL-QB-OFFSEASON-001"], source_refs=[SOURCE], validator="COACH-SYNTHETIC")
    components["drill_validation"] = _validate_then_approve(drills, "OWNER-SYNTHETIC", approve_organization_drill_validation, "DEC-SYNTHETIC-DRILL")

    special_teams = build_organization_special_teams(package_id="ORG-SPECIAL-TEAMS-SYNTHETIC-001", organization_id=ORG, team_context=TEAM, season=SEASON, assignments=[{"assignment_id": "ST-ASSIGNMENT-SYNTHETIC-001", "specialist_id": "PLAYER-SYNTHETIC-001", "unit_id": "ST-UNIT-001", "role": "kicker", "responsibilities": ["execute location and trajectory"], "mastery_evidence": [{"source_ref": SOURCE, "observation": "practice result"}], "source_ref": SOURCE, "review_owner": "COACH-SYNTHETIC"}], source_refs=[SOURCE], compiler="COACH-SYNTHETIC")
    components["special_teams"] = _validate_then_approve(special_teams, "OWNER-SYNTHETIC", approve_organization_special_teams, "DEC-SYNTHETIC-ST")

    performance = build_organization_performance(package_id="ORG-PERFORMANCE-SYNTHETIC-001", organization_id=ORG, season=SEASON, batch_id="PERF-BATCH-SYNTHETIC-001", records=[{"organization_id": ORG, "observation_id": "PERF-OBS-SYNTHETIC-001", "athlete_id": "PLAYER-SYNTHETIC-001", "session_type": "practice", "duration_minutes": 30, "repetitions": 20, "quality_score": 0.9, "season_phase": "regular_season", "position": "QB", "observed_at": "2026-08-23T10:00:00Z"}], source_manifest={"kind": "practice_tracking", "ref": SOURCE, "captured_at": "2026-08-23T12:00:00Z"}, readiness_summaries=[{"summary_id": "READINESS-SYNTHETIC-001", "athlete_id": "PLAYER-SYNTHETIC-001", "signals": ["monitor workload"]}], compiler="PERF-SYNTHETIC")
    components["performance"] = _validate_then_approve(performance, "OWNER-SYNTHETIC", approve_organization_performance, "DEC-SYNTHETIC-PERF")

    media_review = build_organization_media_review(package_id="ORG-MEDIA-REVIEW-SYNTHETIC-001", organization_id=ORG, season=SEASON, assets=[{"id": "FILM-SYNTHETIC-001", "organization_id": ORG, "uri": "file:///synthetic/game.mp4", "duration_seconds": 20, "sha256": "a" * 64, "status": "registered"}], clips=[{"id": "CLIP-SYNTHETIC-001", "asset_id": "FILM-SYNTHETIC-001", "status": "ready"}], playlists=[{"id": "PLAYLIST-SYNTHETIC-001", "clip_ids": ["CLIP-SYNTHETIC-001"], "status": "draft"}], observations=[{"id": "FILM-OBS-SYNTHETIC-001", "clip_id": "CLIP-SYNTHETIC-001", "confidence": "high", "classification": "observed"}], qa_id="QA-SYNTHETIC-001", reviewer="ANALYST-SYNTHETIC")
    components["media_review"] = _validate_then_approve(media_review, "OWNER-SYNTHETIC", approve_organization_media_review, "DEC-SYNTHETIC-MEDIA")

    scouting = build_organization_scouting_package(package_id="ORG-SCOUT-SYNTHETIC-001", organization_id=ORG, opponent="TEAM-OPPONENT-SYNTHETIC", season=SEASON, source_refs=[SOURCE], profile={"id": "OPP-PROFILE-SYNTHETIC-001", "schedule_context": {"week": 1}, "roster_context": {"status": "review"}, "offense": {"status": "review"}, "defense": {"status": "review"}, "special_teams": {"status": "review"}, "sources": [{"kind": "team_film", "ref": SOURCE, "captured_at": "2026-08-23T00:00:00Z"}]}, reports=[{"id": "SCOUT-REPORT-SYNTHETIC-001", "situation": {"down": 3}, "claims": [{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample"], "evidence_refs": [SOURCE]}], "sample_size": 4, "source_refs": [SOURCE]}], matchups=[], evolutions=[], analyst="ANALYST-SYNTHETIC")
    components["scouting"] = _validate_then_approve(scouting, "OWNER-SYNTHETIC", approve_organization_scouting_package, "DEC-SYNTHETIC-SCOUT")

    definition = {"id": "METRIC-DEF-SYNTHETIC", "name": "Success rate", "unit": "rate", "definition": "successes", "required_data": ["play_id"], "formula": "numerator / denominator", "context_dimensions": ["situation"], "caveats": ["sample"], "validation_method": "review", "consumers": ["coach_staff"]}
    analytics = build_organization_analytics_package(package_id="ORG-ANALYTICS-SYNTHETIC-001", organization_id=ORG, season=SEASON, source_refs=[SOURCE], observations=[{"observation_id": "METRIC-OBS-SYNTHETIC-001", "definition": definition, "numerator": 5, "denominator": 10, "context": {"situation": "third_down"}, "source_ref": SOURCE, "observation_ids": ["PLAY-SYNTHETIC-001"]}], reports=[{"id": "ANALYTICS-REPORT-SYNTHETIC-001", "audience": "coach_staff", "observation_ids": ["METRIC-OBS-SYNTHETIC-001"], "context": {"situation": "third_down"}, "caveats": ["sample"]}], analyst="ANALYST-SYNTHETIC")
    components["analytics"] = _validate_then_approve(analytics, "OWNER-SYNTHETIC", approve_organization_analytics_package, "DEC-SYNTHETIC-ANALYTICS")

    game_plan = build_organization_game_plan(package_id="ORG-GAMEPLAN-SYNTHETIC-001", organization_id=ORG, season=SEASON, team_context=TEAM, week_context="WEEK-1", plan={"id": "GAMEPLAN-SYNTHETIC-001", "identity": {"offense": "wide_zone", "defense": "match"}, "assumptions": ["sample is current"], "evidence_refs": [SOURCE], "offense": {"base_calls": ["run"]}, "defense": {"base_calls": ["fit"]}, "special_teams": {"base_calls": ["punt"]}, "opening_script": [{"call": "run", "owner": "OC"}], "base_calls": [{"call": "run", "owner": "OC"}], "shot_plan": [{"call": "play_action", "owner": "OC"}], "pressure_answers": [{"threat": "pressure", "answer": "hot", "owner": "OC"}], "situational_plans": [{"situation": "third_down", "primary": "concept_a", "opponent_responses": ["pressure"], "counters": ["hot"]}], "matchups": [{"player": "PLAYER-SYNTHETIC-001", "opponent": "CB-SYNTHETIC-001", "plan": "release"}], "contingencies": [{"id": "TRIGGER-SYNTHETIC-001", "trigger": "pressure_rate>40%", "response": "change protection", "owner": "OC", "evidence_refs": [SOURCE]}], "ownership": {"head_coach": "HC", "offense": "OC", "defense": "DC", "special_teams": "STC"}, "teaching_outputs": [{"role": "QB", "message": "confirm pressure"}], "in_game_update": {"cadence": "series", "owner": "HC"}}, compiler="COACH-SYNTHETIC")
    components["game_plan"] = _validate_then_approve(game_plan, "OWNER-SYNTHETIC", approve_organization_game_plan, "DEC-SYNTHETIC-GAMEPLAN")
    return components


def run_rehearsal() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        repository = JsonRepository(Path(directory) / "state.json")
        tenant = TenantRepository(repository, organization_id=ORG, actor="OWNER-SYNTHETIC")
        components = _build_components()
        for name, record in components.items():
            tenant.put(COMPONENT_COLLECTIONS[name], record["id"], record, reason="synthetic_organization_operating_set")
        readiness = build_organization_population_readiness(tenant=tenant, organization_id=ORG, season=SEASON)
        resolved = load_persisted_organization_components(tenant)
        bundle = build_organization_operating_bundle(bundle_id="ORG-BUNDLE-SYNTHETIC-2026", organization_id=ORG, season=SEASON, components=resolved)
        return {"status": "passed" if readiness["status"] == "ready_for_bundle" and bundle["status"] == "ready_for_owner_review" else "failed", "organization_id": ORG, "component_count": len(components), "required_component_count": len(REQUIRED_COMPONENTS), "readiness": readiness, "bundle": bundle, "owner_approval_required": True, "production_implementation_allowed": False, "activation_performed": False, "external_state_changed": False, "synthetic": True}


if __name__ == "__main__":
    import json
    print(json.dumps(run_rehearsal(), indent=2))
