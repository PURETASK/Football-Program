"""Safe, synthetic end-to-end data for the local NFL FIDOS showcase.

The demo fixture deliberately uses the real repository and service contracts so
the operator dashboard can be explored without connecting a real organization,
roster, source, provider, or production workflow. Every top-level fixture is
marked with ``synthetic_demo`` and a seed id. Cleanup is predicate-based and
fail-closed in the CLI wrappers.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .analytics_dictionary import build_analytics_report, calculate_metric
from .film_intelligence import build_assignment_grade, build_film_observation, build_film_playlist, validate_film_qa
from .film_room_service import FilmRoomService
from .game_plan_architecture import build_countermeasure as build_game_plan_countermeasure, build_weekly_game_plan
from .game_plan_collaboration import GamePlanCollaborationService
from .media import create_film_clip, register_film_asset
from .media_jobs import MediaProcessingJobService
from .organization_analytics import approve_organization_analytics_package, build_organization_analytics_package
from .organization_doctrine import approve_organization_doctrine, build_organization_doctrine
from .organization_drill_validation import approve_organization_drill_validation, build_organization_drill_validation
from .organization_game_plan import approve_organization_game_plan, build_organization_game_plan
from .organization_media_review import approve_organization_media_review, build_organization_media_review
from .organization_onboarding import approve_onboarding_package, build_onboarding_package
from .organization_operating_bundle import COMPONENT_COLLECTIONS, build_organization_operating_bundle
from .organization_performance import approve_organization_performance, build_organization_performance
from .organization_player_development import approve_organization_player_development, build_organization_player_development
from .organization_play_corpus import approve_organization_play_corpus, build_organization_play_corpus
from .organization_scouting import approve_organization_scouting_package, build_organization_scouting_package
from .organization_special_teams import approve_organization_special_teams, build_organization_special_teams
from .organization_staff_review import approve_organization_staff_package, build_organization_staff_package
from .play_design_collaboration import PlayDesignCollaborationService
from .play_design_service import PlayDesignService
from .playbook_architecture import build_extended_play
from .practice_architecture import build_practice_architecture
from .repository import JsonRepository
from .scheme import build_scheme
from .scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report
from .sqlite_repository import SqliteRepository
from .tenant_repository import TenantRepository
from .visual_playbook import build_animation_timeline, build_visual_play


DEMO_ORGANIZATION_ID = "ORG-DEMO-FIDOS-001"
DEMO_TEAM_ID = "TEAM-DEMO-FIDOS-001"
DEMO_SEASON = "2026"
DEMO_SEED_ID = "DEMO-SEED-2026-08-24"
DEMO_ACTOR = "DEMO-SEEDER"
DEMO_OWNER = "DEMO-PROGRAM-OWNER"
DEMO_COACH = "DEMO-COACH"
DEMO_ANALYST = "DEMO-ANALYST"
DEMO_DATE = "2026-08-24T12:00:00+00:00"
DEMO_MEDIA_DIRECTORY = "nfl-fidos-demo-media"
DEMO_MARKER = "SAFE-TO-DELETE-SYNTHETIC-DEMO"


def default_database_path() -> Path:
    return Path(os.environ.get("NFL_FIDOS_DATABASE", ".runtime/nfl_fidos.sqlite3")).expanduser().resolve()


def _validate_scope(organization_id: str, seed_id: str) -> None:
    if organization_id != DEMO_ORGANIZATION_ID:
        raise ValueError(f"Synthetic demo operations are locked to {DEMO_ORGANIZATION_ID}")
    if not seed_id.startswith("DEMO-SEED-") or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for character in seed_id):
        raise ValueError("seed_id must be a safe DEMO-SEED-* identifier")


def open_repository(path: str | Path) -> JsonRepository | SqliteRepository:
    resolved = Path(path).expanduser().resolve()
    if resolved.suffix.lower() == ".json":
        return JsonRepository(resolved)
    return SqliteRepository(resolved)


def _stamp(record: dict[str, Any], *, organization_id: str, seed_id: str) -> dict[str, Any]:
    output = deepcopy(record)
    output.setdefault("organization_id", organization_id)
    output.update({"synthetic_demo": True, "demo_seed_id": seed_id, "demo_marker": DEMO_MARKER})
    return output


def _source_ref(seed_id: str) -> str:
    return f"DEMO-SOURCE-{seed_id.removeprefix('DEMO-SEED-')}"


def _put(tenant: TenantRepository, collection: str, record: dict[str, Any], *, seed_id: str, actor: str = DEMO_ACTOR, reason: str = "synthetic_demo_seed") -> dict[str, Any]:
    stamped = _stamp(record, organization_id=tenant.organization_id, seed_id=seed_id)
    record_id = stamped.get("id")
    if not isinstance(record_id, str) or not record_id:
        raise ValueError(f"Synthetic record in {collection} requires a non-empty id")
    return tenant.put(collection, record_id, stamped, actor=actor, reason=reason)


def _mark_existing(tenant: TenantRepository, collection: str, record_id: str, *, seed_id: str, actor: str = DEMO_ACTOR) -> dict[str, Any]:
    record = tenant.get(collection, record_id)
    if record is None:
        raise KeyError(f"Expected synthetic record was not persisted: {collection}/{record_id}")
    return _put(tenant, collection, record, seed_id=seed_id, actor=actor, reason="synthetic_demo_marker_applied")


def _people() -> list[dict[str, Any]]:
    players = [
        ("DEMO-QB-1", "Jordan Vale", "QB", 7),
        ("DEMO-RB-1", "Marcus Reed", "RB", 21),
        ("DEMO-WR-X", "Eli Brooks", "WR", 81),
        ("DEMO-WR-H", "Noah Grant", "WR", 11),
        ("DEMO-WR-Z", "Caleb Stone", "WR", 3),
        ("DEMO-TE-1", "Mason Cole", "TE", 88),
        ("DEMO-LT-1", "Owen Price", "LT", 72),
        ("DEMO-LG-1", "Leo Hart", "LG", 64),
        ("DEMO-C-1", "Evan Moss", "C", 55),
        ("DEMO-RG-1", "Kai Brooks", "RG", 66),
        ("DEMO-RT-1", "Drew Lane", "RT", 74),
        ("DEMO-DE-1", "Jace Ward", "DE", 92),
        ("DEMO-DT-1", "Tyson Bell", "DT", 95),
        ("DEMO-DT-2", "Riley Knox", "DT", 90),
        ("DEMO-DE-2", "Andre Fox", "DE", 97),
        ("DEMO-MLB-1", "Sam Ellis", "MLB", 54),
        ("DEMO-WLB-1", "Nico Shaw", "WLB", 42),
        ("DEMO-CB-L", "Jalen North", "CB", 23),
        ("DEMO-CB-R", "Micah West", "CB", 24),
        ("DEMO-FS-1", "Theo Banks", "FS", 32),
        ("DEMO-SS-1", "Cameron Hill", "SS", 36),
    ]
    people = [{"id": player_id, "name": name, "type": "player", "position": position, "number": number} for player_id, name, position, number in players]
    people.extend([
        {"id": "DEMO-HC", "name": "Alex Mercer", "type": "coach", "staff_role": "head_coach"},
        {"id": "DEMO-OC", "name": "Taylor Quinn", "type": "coach", "staff_role": "coordinator"},
        {"id": "DEMO-DC", "name": "Riley Morgan", "type": "coach", "staff_role": "coordinator"},
        {"id": "DEMO-ANALYST", "name": "Casey Brooks", "type": "staff", "staff_role": "analyst"},
        {"id": "DEMO-FILM", "name": "Parker Lee", "type": "staff", "staff_role": "film_staff"},
        {"id": "DEMO-PERFORMANCE", "name": "Jamie Fox", "type": "staff", "staff_role": "performance_staff"},
    ])
    return people


def _approve_package(package: dict[str, Any], *, function: Callable[..., dict[str, Any]], argument_name: str, decision_suffix: str) -> dict[str, Any]:
    return function(**{argument_name: package}, approver=DEMO_OWNER, approver_role="program_owner", decision_ref=f"DEC-DEMO-{decision_suffix}")


def _build_operating_components(*, organization_id: str, season: str, team_id: str, source_ref: str) -> dict[str, dict[str, Any]]:
    people = _people()
    onboarding = build_onboarding_package(
        organization_id=organization_id,
        name="Synthetic Football Club — FIDOS Showcase",
        season=season,
        team_id=team_id,
        people=people,
        terminology_version="TERM-DEMO-1.0.0",
        owner=DEMO_OWNER,
        source={"kind": "synthetic_fixture", "ref": source_ref},
    )
    approved_onboarding = approve_onboarding_package(
        organization=onboarding["organization"],
        terminology_bundle=onboarding["terminology_bundle"],
        approver=DEMO_OWNER,
        decision_ref="DEC-DEMO-ONBOARDING",
    )
    components: dict[str, dict[str, Any]] = {
        "organization_context": approved_onboarding["organization"],
        "terminology_bundle": approved_onboarding["terminology_bundle"],
    }

    doctrine = build_organization_doctrine(
        doctrine_id="ORG-DOCTRINE-DEMO-001", organization_id=organization_id, team_context=team_id, season=season,
        scheme_family_ids=["SCHEME-FAM-OFF-001", "SCHEME-FAM-DEF-001"],
        special_teams_unit_ids=["ST-UNIT-003"], source_refs=[source_ref], compiler=DEMO_COACH,
    )
    components["doctrine"] = _approve_package(doctrine, function=approve_organization_doctrine, argument_name="doctrine", decision_suffix="DOCTRINE")

    play_corpus = build_organization_play_corpus(
        corpus_id="ORG-PLAY-CORPUS-DEMO-001", organization_id=organization_id, team_context=team_id, season=season,
        plays=[{"id": "PLAY-DEMO-DAGGER", "version": "1.0.0", "team_context": team_id, "situation": {"down": 3, "distance": 6, "field_zone": "open_field"}, "personnel": "11", "formation": "shotgun_trips_right", "motion": None, "assignments": [{"role": "QB", "assignment": "read boundary safety"}, {"role": "C", "assignment": "identify protection point"}, {"role": "WR1", "assignment": "run post route"}], "source": {"kind": "synthetic_fixture", "ref": source_ref}, "unit": "offense", "concept": "Dagger", "status": "draft"}],
        source_refs=[source_ref], compiler=DEMO_COACH,
    )
    components["play_corpus"] = _approve_package(play_corpus, function=approve_organization_play_corpus, argument_name="corpus", decision_suffix="PLAY-CORPUS")

    player_development = build_organization_player_development(
        package_id="ORG-PLAYER-DEV-DEMO-001", organization_id=organization_id, team_context=team_id, season=season,
        players=[{"player_id": "PLAYER-DEMO-QB-1", "position": "QB", "owner": DEMO_COACH, "objectives": [{"capability_id": "CAP-READ-SHELL", "outcome": "confirm shell and deliver on time", "measure": "4 of 5 correct reads"}], "mastery_records": [{"record_id": "MASTERY-DEMO-QB-READ", "capability_id": "CAP-READ-SHELL", "current_level": "developing", "target_level": "functional", "evidence": [{"source_ref": source_ref, "observation": "synthetic practice rep"}], "next_actions": ["repeat boundary safety read"]}]}],
        compiler=DEMO_COACH,
    )
    components["player_development"] = _approve_package(player_development, function=approve_organization_player_development, argument_name="package", decision_suffix="PLAYER-DEVELOPMENT")

    staff = build_organization_staff_package(
        package_id="ORG-STAFF-DEMO-001", organization_id=organization_id, team_context=team_id, season=season,
        staff=[{"person_id": "DEMO-HC", "role": "head_coach", "review_owner": DEMO_OWNER}, {"person_id": "DEMO-OC", "role": "offensive_coordinator", "review_owner": "DEMO-HC"}],
        evaluations=[{"evaluation_id": "EVAL-COACH-DEMO-001", "coach_id": "DEMO-OC", "role": "offensive_coordinator", "ratings": {"offensive_scheme": 4, "installation": 4, "play_calling": 4, "adjustments": 3, "staff_alignment": 4}, "evidence": [{"source_ref": source_ref, "observation": "synthetic weekly review"}], "evaluator": DEMO_OWNER}],
        compiler=DEMO_COACH,
    )
    components["staff_review"] = _approve_package(staff, function=approve_organization_staff_package, argument_name="package", decision_suffix="STAFF")

    drill_validation = build_organization_drill_validation(
        validation_id="ORG-DRILL-VALIDATION-DEMO-001", organization_id=organization_id, season=season, position="QB",
        selected_drill_ids=["DRILL-QB-001", "VARIANT-DRILL-QB-OFFSEASON-001"], source_refs=[source_ref], validator=DEMO_COACH,
    )
    components["drill_validation"] = _approve_package(drill_validation, function=approve_organization_drill_validation, argument_name="package", decision_suffix="DRILLS")

    special_teams = build_organization_special_teams(
        package_id="ORG-SPECIAL-TEAMS-DEMO-001", organization_id=organization_id, team_context=team_id, season=season,
        assignments=[{"assignment_id": "ST-ASSIGNMENT-DEMO-001", "specialist_id": "DEMO-QB-1", "unit_id": "ST-UNIT-003", "role": "holder", "responsibilities": ["secure operation and communicate alert"], "mastery_evidence": [{"source_ref": source_ref, "observation": "synthetic walkthrough"}], "source_ref": source_ref, "review_owner": DEMO_COACH}],
        source_refs=[source_ref], compiler=DEMO_COACH,
    )
    components["special_teams"] = _approve_package(special_teams, function=approve_organization_special_teams, argument_name="package", decision_suffix="SPECIAL-TEAMS")

    performance = build_organization_performance(
        package_id="ORG-PERFORMANCE-DEMO-001", organization_id=organization_id, season=season, batch_id="PERF-BATCH-DEMO-001",
        records=[{"organization_id": organization_id, "observation_id": "PERF-OBS-DEMO-001", "athlete_id": "DEMO-QB-1", "session_type": "practice", "duration_minutes": 32, "repetitions": 18, "quality_score": 0.86, "season_phase": "regular_season", "position": "QB", "observed_at": DEMO_DATE}],
        source_manifest={"kind": "synthetic_practice_tracking", "ref": source_ref, "captured_at": DEMO_DATE},
        readiness_summaries=[{"summary_id": "READINESS-DEMO-QB-001", "athlete_id": "DEMO-QB-1", "signals": ["monitor late-down decision speed"]}], compiler="DEMO-PERFORMANCE",
    )
    components["performance"] = _approve_package(performance, function=approve_organization_performance, argument_name="package", decision_suffix="PERFORMANCE")

    media_review = build_organization_media_review(
        package_id="ORG-MEDIA-REVIEW-DEMO-001", organization_id=organization_id, season=season,
        assets=[{"id": "FILM-DEMO-GAME-001", "organization_id": organization_id, "uri": "file:///synthetic/nfl-fidos-demo-media/demo-game.mp4", "duration_seconds": 12, "sha256": "d" * 64, "status": "registered"}],
        clips=[{"id": "CLIP-DEMO-GAME-001", "asset_id": "FILM-DEMO-GAME-001", "status": "ready"}],
        playlists=[{"id": "PLAYLIST-DEMO-THIRD-DOWN", "clip_ids": ["CLIP-DEMO-GAME-001"], "status": "draft"}],
        observations=[{"id": "FILM-OBS-DEMO-001", "clip_id": "CLIP-DEMO-GAME-001", "confidence": "high", "classification": "observed"}],
        qa_id="QA-DEMO-GAME-001", reviewer=DEMO_ANALYST,
    )
    components["media_review"] = _approve_package(media_review, function=approve_organization_media_review, argument_name="package", decision_suffix="MEDIA")

    scouting = build_organization_scouting_package(
        package_id="ORG-SCOUT-DEMO-001", organization_id=organization_id, opponent="OPP-DEMO-LIONS", season=season, source_refs=[source_ref],
        profile={"id": "OPP-PROFILE-DEMO-LIONS", "schedule_context": {"week": 1, "venue": "away"}, "roster_context": {"status": "review"}, "offense": {"formations": ["11 personnel", "pistol"], "tendencies": ["early-down wide zone"]}, "defense": {"coverages": ["cover_3", "quarters"], "pressure_rate": 0.34}, "special_teams": {"units": ["punt" ]}, "sources": [{"kind": "team_film", "ref": source_ref, "captured_at": DEMO_DATE}]},
        reports=[{"id": "SCOUT-REPORT-DEMO-THIRD-DOWN", "situation": {"down": 3, "distance": "medium"}, "claims": [{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample size"], "evidence_refs": [source_ref]}], "sample_size": 8, "source_refs": [source_ref]}],
        matchups=[], evolutions=[], analyst=DEMO_ANALYST,
    )
    components["scouting"] = _approve_package(scouting, function=approve_organization_scouting_package, argument_name="package", decision_suffix="SCOUTING")

    metric_definition = {"id": "METRIC-DEF-DEMO-EPA", "name": "Third-down success rate", "unit": "rate", "definition": "Successful third-down conversions divided by third-down opportunities", "required_data": ["play_id", "down", "conversion"], "formula": "successes / opportunities", "context_dimensions": ["situation", "personnel"], "caveats": ["Synthetic ten-play sample; do not generalize."], "validation_method": "staff review", "consumers": ["coach_staff", "analyst"]}
    metric_observation = calculate_metric(definition=metric_definition, numerator=6, denominator=10, context={"situation": "third_down", "personnel": "11"}, source={"kind": "synthetic_analytics", "ref": source_ref}, observation_ids=["PLAY-DEMO-DAGGER"])
    analytics = build_organization_analytics_package(
        package_id="ORG-ANALYTICS-DEMO-001", organization_id=organization_id, season=season, source_refs=[source_ref],
        observations=[{"observation_id": metric_observation["id"], "definition": metric_definition, "numerator": 6, "denominator": 10, "context": {"situation": "third_down", "personnel": "11"}, "source_ref": source_ref, "observation_ids": ["PLAY-DEMO-DAGGER"]}],
        reports=[{"id": "ANALYTICS-REPORT-DEMO-THIRD-DOWN", "audience": "coach_staff", "observation_ids": [metric_observation["id"]], "context": {"situation": "third_down"}, "caveats": ["Synthetic sample requires human interpretation."]}], analyst=DEMO_ANALYST,
    )
    components["analytics"] = _approve_package(analytics, function=approve_organization_analytics_package, argument_name="package", decision_suffix="ANALYTICS")

    game_plan = build_organization_game_plan(
        package_id="ORG-GAMEPLAN-DEMO-001", organization_id=organization_id, season=season, team_context=team_id, week_context="WEEK-1",
        plan={"id": "GAMEPLAN-DEMO-WEEK-1", "identity": {"offense": "shotgun-spread", "defense": "4-2-5-match"}, "assumptions": ["Synthetic opponent sample is intentionally small."], "evidence_refs": [source_ref], "offense": {"base_calls": ["Dagger", "Inside Zone"]}, "defense": {"base_calls": ["Cover 3", "Sim Pressure"]}, "special_teams": {"base_calls": ["Punt Safe"]}, "opening_script": [{"call": "Dagger", "owner": "DEMO-OC"}], "base_calls": [{"call": "Inside Zone", "owner": "DEMO-OC"}], "shot_plan": [{"call": "Dagger", "owner": "DEMO-OC"}], "pressure_answers": [{"threat": "mugged linebackers", "answer": "slide and hot", "owner": "DEMO-OC"}], "situational_plans": [{"situation": "third_down", "primary": "Dagger", "opponent_responses": ["pressure", "match coverage"], "counters": ["hot", "sprint out"]}], "matchups": [{"player": "DEMO-WR-X", "opponent": "OPP-CB-1", "plan": "attack leverage"}], "contingencies": [{"id": "TRIGGER-DEMO-PRESSURE", "trigger": "pressure_rate > 40%", "response": "check to quick game", "owner": "DEMO-OC", "evidence_refs": [source_ref]}], "ownership": {"head_coach": "DEMO-HC", "offense": "DEMO-OC", "defense": "DEMO-DC", "special_teams": "DEMO-STC"}, "teaching_outputs": [{"role": "QB", "message": "Confirm the boundary safety before the Dagger read."}], "in_game_update": {"cadence": "series", "owner": "DEMO-HC"}}, compiler=DEMO_COACH,
    )
    components["game_plan"] = _approve_package(game_plan, function=approve_organization_game_plan, argument_name="package", decision_suffix="GAMEPLAN")
    return components


def _player_design_players(unit: str) -> list[dict[str, Any]]:
    if unit == "offense":
        rows = [("DEMO-OFF-QB", "QB", 50, 25), ("DEMO-OFF-RB", "RB", 47, 29), ("DEMO-OFF-X", "WR", 8, 21), ("DEMO-OFF-H", "WR", 70, 21), ("DEMO-OFF-Z", "WR", 92, 21), ("DEMO-OFF-TE", "TE", 61, 22), ("DEMO-OFF-LT", "LT", 39, 22), ("DEMO-OFF-LG", "LG", 44, 22), ("DEMO-OFF-C", "C", 49, 22), ("DEMO-OFF-RG", "RG", 54, 22), ("DEMO-OFF-RT", "RT", 59, 22)]
    else:
        rows = [("DEMO-DEF-DE-L", "DE", 36, 22), ("DEMO-DEF-DT-L", "DT", 43, 22), ("DEMO-DEF-DT-R", "DT", 53, 22), ("DEMO-DEF-DE-R", "DE", 60, 22), ("DEMO-DEF-MLB", "MLB", 47, 28), ("DEMO-DEF-WLB", "WLB", 56, 29), ("DEMO-DEF-CB-L", "CB", 12, 20), ("DEMO-DEF-CB-R", "CB", 84, 20), ("DEMO-DEF-SS", "SS", 70, 30), ("DEMO-DEF-FS", "FS", 49, 35), ("DEMO-DEF-NICKEL", "NB", 27, 28)]
    return [{"id": player_id, "position": position, "role": position, "start": {"x": x, "y": y}} for player_id, position, x, y in rows]


def _element(element_id: str, kind: str, player_id: str | None, points: list[dict[str, int]], arrow_style: str, start_ms: int, end_ms: int, **fields: Any) -> dict[str, Any]:
    output = {"id": element_id, "kind": kind, "player_id": player_id, "points": points, "arrow_style": arrow_style, "start_ms": start_ms, "end_ms": end_ms, **fields}
    return output


def _offense_design(*, design_id: str, seed_id: str) -> dict[str, Any]:
    elements = [
        _element("DEMO-OFF-X-POST", "route", "DEMO-OFF-X", [{"x": 8, "y": 21}, {"x": 8, "y": 12}, {"x": 28, "y": 5}], "route", 350, 1700, type="post", asset_id="ASSET-ROUTE-POST", note="Win outside leverage, stem vertical, then cross the safety's face.", role="WR", read_key="boundary_safety"),
        _element("DEMO-OFF-H-DIG", "route", "DEMO-OFF-H", [{"x": 70, "y": 21}, {"x": 70, "y": 13}, {"x": 51, "y": 13}], "route", 350, 1800, type="dig", asset_id="ASSET-ROUTE-DIG", note="Push the hook defender and flatten at twelve.", role="WR"),
        _element("DEMO-OFF-Z-MOTION", "motion", "DEMO-OFF-Z", [{"x": 92, "y": 21}, {"x": 83, "y": 21}], "motion", 0, 500, type="jet", asset_id="ASSET-MOTION-JET", snap_ms=250, snap_direction="lateral", requires_reset=False, at_snap=True, note="Fast jet motion to widen the apex defender."),
        _element("DEMO-OFF-Z-CLEAR", "route", "DEMO-OFF-Z", [{"x": 83, "y": 21}, {"x": 83, "y": 11}, {"x": 83, "y": 3}], "route", 450, 1600, type="vertical", asset_id="ASSET-ROUTE-VERTICAL", note="Clear the corner and stretch the deep third."),
        _element("DEMO-OFF-TE-FLAT", "route", "DEMO-OFF-TE", [{"x": 61, "y": 22}, {"x": 69, "y": 25}, {"x": 82, "y": 26}], "route", 450, 1450, type="flat", asset_id="ASSET-ROUTE-FLAT", note="Release outside and settle in the flat."),
        _element("DEMO-OFF-RB-CHECK", "route", "DEMO-OFF-RB", [{"x": 47, "y": 29}, {"x": 56, "y": 31}, {"x": 69, "y": 31}], "route", 500, 1500, type="swing", note="Check protection first, then become the outlet."),
        _element("DEMO-OFF-LT-BLOCK", "block", "DEMO-OFF-LT", [{"x": 39, "y": 22}, {"x": 35, "y": 24}], "block", 0, 1250, assignment="Base the defensive end.", gap="C", protection_target="DEMO-DEF-DE-L"),
        _element("DEMO-OFF-LG-BLOCK", "block", "DEMO-OFF-LG", [{"x": 44, "y": 22}, {"x": 42, "y": 25}], "block", 0, 1250, assignment="Work to the backside linebacker.", gap="B", protection_target="DEMO-DEF-DT-L"),
        _element("DEMO-OFF-C-BLOCK", "block", "DEMO-OFF-C", [{"x": 49, "y": 22}, {"x": 49, "y": 25}], "block", 0, 1250, assignment="Set the point and anchor interior pressure.", gap="A", protection_target="DEMO-DEF-MLB"),
        _element("DEMO-OFF-RG-BLOCK", "block", "DEMO-OFF-RG", [{"x": 54, "y": 22}, {"x": 56, "y": 25}], "block", 0, 1250, assignment="Post and hinge the three-technique.", gap="A-R", protection_target="DEMO-DEF-DT-R"),
        _element("DEMO-OFF-RT-BLOCK", "block", "DEMO-OFF-RT", [{"x": 59, "y": 22}, {"x": 63, "y": 24}], "block", 0, 1250, assignment="Fan the edge.", gap="D", protection_target="DEMO-DEF-DE-R"),
        {"id": "DEMO-OFF-QB-READ", "kind": "read", "player_id": "DEMO-OFF-QB", "read_key": "boundary_safety", "read_prompt": "If the safety widens, hit the dig; if he stays inside, throw the post.", "responsibility": "Read the boundary safety, confirm protection, and deliver on rhythm.", "start_ms": 0, "end_ms": 2200, "visibility": "shared"},
        {"id": "DEMO-OFF-COACH-CUE", "kind": "annotation", "player_id": None, "arrow_style": "check", "note": "Coaching cue: eyes before feet; protect the ball on the dig window.", "visibility": "shared", "start_ms": 0, "end_ms": 2600},
    ]
    return {"id": design_id, "version": "1.0.0", "unit": "offense", "personnel": "11", "formation": "shotgun_trips_right", "concept": "Dagger / Boundary Read", "rule_profile": "nfl", "route_collision_policy": "warning", "players": _player_design_players("offense"), "elements": elements, "timeline": {"snap_ms": 0, "duration_ms": 2800, "markers": [{"id": "DEMO-MARK-SNAP", "label": "Snap", "kind": "cue", "ms": 0}, {"id": "DEMO-MARK-READ", "label": "Confirm boundary safety", "kind": "read", "ms": 650}, {"id": "DEMO-MARK-THROW", "label": "Throw window", "kind": "cue", "ms": 1450}], "narration": [{"id": "DEMO-NARRATION-QB", "role": "QB", "start_ms": 0, "end_ms": 1200, "text": "Confirm the boundary safety before choosing the post or dig."}, {"id": "DEMO-NARRATION-COACH", "role": "coach", "start_ms": 1200, "end_ms": 2200, "text": "The dig wins when the safety expands with the clear route."}], "events": [{"id": "DEMO-EVENT-READ", "type": "qb_read", "at_ms": 650, "label": "Boundary safety read"}]}, "teaching": {"quizzes": [{"id": "DEMO-QUIZ-QB-READ", "question": "What is the QB key in Dagger?", "options": ["Boundary safety", "Mike linebacker", "Backside end"], "answer": "Boundary safety", "step_id": "STEP-DEMO-OFF-QB-READ-confirm"}]}, "practice_linkage": {"practice_refs": ["PRACTICE-DEMO-WEEK-1"], "drill_ids": ["DRILL-DEMO-QB-SHELL"]}, "coaching_notes": ["Install after protection is clean.", "Ask the QB to verbalize the safety key before full-speed reps."]}


def _defense_design(*, design_id: str, seed_id: str) -> dict[str, Any]:
    elements = [
        _element("DEMO-DEF-CB-L-COVER", "coverage", "DEMO-DEF-CB-L", [{"x": 12, "y": 20}, {"x": 16, "y": 11}, {"x": 13, "y": 3}], "coverage", 0, 2600, coverage="cover_3", zone="deep_left", assignment="Carry the outside third."),
        _element("DEMO-DEF-FS-MIDDLE", "coverage", "DEMO-DEF-FS", [{"x": 49, "y": 35}, {"x": 50, "y": 18}, {"x": 50, "y": 3}], "coverage", 0, 2600, coverage="cover_3", zone="deep_middle", assignment="Own the post and overlap the QB read."),
        _element("DEMO-DEF-CB-R-COVER", "coverage", "DEMO-DEF-CB-R", [{"x": 84, "y": 20}, {"x": 80, "y": 11}, {"x": 87, "y": 3}], "coverage", 0, 2600, coverage="cover_3", zone="deep_right", assignment="Carry the outside third."),
        _element("DEMO-DEF-DE-L-RUSH", "rush", "DEMO-DEF-DE-L", [{"x": 36, "y": 22}, {"x": 31, "y": 18}, {"x": 26, "y": 12}], "rush", 250, 1800, rush_lane="C-gap", assignment="Speed to the passer and keep contain."),
        _element("DEMO-DEF-DT-L-TEX", "stunt", "DEMO-DEF-DT-L", [{"x": 43, "y": 22}, {"x": 47, "y": 19}, {"x": 54, "y": 13}], "stunt", 250, 1900, stunt="tex", exchange_with="DEMO-DEF-DE-R-RUSH", assignment="Penetrate before exchanging."),
        _element("DEMO-DEF-DE-R-RUSH", "rush", "DEMO-DEF-DE-R", [{"x": 60, "y": 22}, {"x": 56, "y": 19}, {"x": 50, "y": 13}], "rush", 250, 1850, rush_lane="B-gap", assignment="Wrap inside after the tackle crosses."),
        _element("DEMO-DEF-MLB-FIT", "fit", "DEMO-DEF-MLB", [{"x": 47, "y": 28}, {"x": 45, "y": 24}, {"x": 42, "y": 19}], "fit", 300, 1700, fit_gap="A", responsibility="spill", assignment="Fit the frontside A gap and spill the run."),
        _element("DEMO-DEF-WLB-FIT", "fit", "DEMO-DEF-WLB", [{"x": 56, "y": 29}, {"x": 56, "y": 25}, {"x": 57, "y": 19}], "fit", 300, 1700, fit_gap="B", responsibility="box", assignment="Scrape and box the back."),
        _element("DEMO-DEF-SS-ROTATE", "rotation", "DEMO-DEF-SS", [{"x": 70, "y": 30}, {"x": 69, "y": 22}, {"x": 65, "y": 16}], "rotation", 0, 2200, rotation="buzz_flat", assignment="Rotate down late and rob the glance route."),
        {"id": "DEMO-DEF-QB-READ", "kind": "read", "player_id": "DEMO-DEF-MLB", "read_key": "backfield_flow", "read_prompt": "Key the mesh, fit inside-out, and communicate the pressure answer.", "responsibility": "Set the front and confirm the rotation.", "start_ms": 0, "end_ms": 2200, "visibility": "shared"},
        {"id": "DEMO-DEF-COACH-CUE", "kind": "annotation", "player_id": None, "arrow_style": "check", "note": "Coaching cue: rush with lane integrity so the deep middle safety can overlap the glance window.", "visibility": "shared", "start_ms": 0, "end_ms": 2600},
    ]
    return {"id": design_id, "version": "1.0.0", "unit": "defense", "personnel": "nickel", "formation": "4-2-5_over", "front": "4-2-5_over", "coverage": "cover_3", "rule_profile": "nfl", "coverage_zones": ["deep_left", "deep_middle", "deep_right"], "players": _player_design_players("defense"), "elements": elements, "timeline": {"snap_ms": 0, "duration_ms": 2700, "markers": [{"id": "DEMO-DEF-MARK-SNAP", "label": "Snap", "kind": "cue", "ms": 0}, {"id": "DEMO-DEF-MARK-ROTATE", "label": "Late safety rotation", "kind": "rotation", "ms": 420}], "narration": [{"id": "DEMO-DEF-NARRATION-MIKE", "role": "MLB", "start_ms": 0, "end_ms": 1200, "text": "Key the mesh, fit inside-out, then confirm the buzz rotation."}], "events": [{"id": "DEMO-DEF-EVENT-ROTATE", "type": "coverage_rotation", "at_ms": 420, "label": "Safety rotates to the flat"}]}, "teaching": {"quizzes": [{"id": "DEMO-QUIZ-MLB-FIT", "question": "What is the Mike's first key?", "options": ["Backfield flow", "Wide receiver stem", "Guard release"], "answer": "Backfield flow", "step_id": "STEP-DEMO-DEF-QB-READ-identify"}]}, "practice_linkage": {"practice_refs": ["PRACTICE-DEMO-WEEK-1"], "drill_ids": ["DRILL-DEMO-DEF-FIT"]}, "coaching_notes": ["Install the rotation separately before adding the stunt.", "Keep the rush picture stable for the coverage teaching rep."]}


def _seed_play_designs(tenant: TenantRepository, *, seed_id: str) -> dict[str, Any]:
    service = PlayDesignService(tenant)
    offense = _stamp(_offense_design(design_id="PD-DEMO-OFF-DAGGER", seed_id=seed_id), organization_id=tenant.organization_id, seed_id=seed_id)
    defense = _stamp(_defense_design(design_id="PD-DEMO-DEF-COVER3", seed_id=seed_id), organization_id=tenant.organization_id, seed_id=seed_id)
    saved_offense = service.save(offense, actor=DEMO_COACH)
    saved_offense = service.request_review(saved_offense["id"], actor=DEMO_COACH, decision_ref="DEC-DEMO-PLAY-REVIEW-OFFENSE")
    saved_offense = service.publish(saved_offense["id"], actor=DEMO_OWNER, decision_ref="DEC-DEMO-PUBLISH-OFFENSE", game_plan_snapshot_id="GAMEPLAN-SNAPSHOT-DEMO-WEEK-1")
    saved_defense = service.save(defense, actor=DEMO_COACH)
    saved_defense = service.request_review(saved_defense["id"], actor=DEMO_COACH, decision_ref="DEC-DEMO-PLAY-REVIEW-DEFENSE")
    branch = service.branch(saved_offense["id"], branch_id="PD-DEMO-OFF-DAGGER-COUNTER", actor=DEMO_COACH)
    comment = service.add_comment(saved_defense["id"], actor=DEMO_ANALYST, text="Confirm the weakside fit language before the staff review.", element_id="DEMO-DEF-WLB-FIT")
    reply = service.reply_comment(saved_defense["id"], comment_id=comment["id"], actor=DEMO_COACH, text="Updated the coaching cue to box the back and keep the rotation intact.")
    resolved = service.resolve_comment(saved_defense["id"], comment_id=comment["id"], actor=DEMO_OWNER, resolved=False)
    collaboration = PlayDesignCollaborationService(tenant)
    events = [
        collaboration.record_event(design_id=saved_defense["id"], event_type="design_saved", actor=DEMO_COACH, payload={"revision": saved_defense.get("_revision")}),
        collaboration.record_event(design_id=saved_defense["id"], event_type="comment_added", actor=DEMO_ANALYST, payload={"comment_id": comment["id"], "element_id": comment.get("element_id")}),
        collaboration.record_event(design_id=saved_defense["id"], event_type="comment_replied", actor=DEMO_COACH, payload={"comment_id": comment["id"], "reply_id": reply["id"]}),
        collaboration.record_event(design_id=saved_defense["id"], event_type="comment_reopened", actor=DEMO_OWNER, payload={"comment_id": comment["id"]}),
    ]
    mastery = [
        service.record_mastery(saved_offense["id"], role="QB", user_id="DEMO-QB-1", step_id="STEP-DEMO-OFF-QB-READ-confirm", score=0.8, result="passed", actor=DEMO_COACH, practice_ref="PRACTICE-DEMO-WEEK-1", notes="Good shell confirmation; keep eyes disciplined.", attempt_id="MASTERY-DEMO-OFF-QB-001"),
        service.record_mastery(saved_offense["id"], role="QB", user_id="DEMO-QB-1", step_id="STEP-DEMO-OFF-QB-READ-decide", score=0.65, result="needs_review", actor=DEMO_COACH, practice_ref="PRACTICE-DEMO-WEEK-1", notes="Late dig decision in the synthetic rep.", attempt_id="MASTERY-DEMO-OFF-QB-002"),
    ]
    for collection, records in (("play_design_comments", [comment, reply, resolved]), ("play_design_collaboration_events", events), ("play_design_mastery", mastery)):
        for record in records:
            _mark_existing(tenant, collection, record["id"], seed_id=seed_id)
    for collection in ("play_designs", "play_design_versions", "play_design_releases"):
        for record in tenant.list(collection):
            design = record.get("design") if isinstance(record.get("design"), dict) else record
            if record.get("design_id") in {saved_offense["id"], saved_defense["id"], branch["id"]} or design.get("id") in {saved_offense["id"], saved_defense["id"], branch["id"]}:
                _mark_existing(tenant, collection, record["id"], seed_id=seed_id)
    return {"offense": saved_offense, "defense": saved_defense, "branch": branch}


def _build_visual(organization_id: str, *, seed_id: str) -> dict[str, Any]:
    visual = build_visual_play(
        visual_id="VISUAL-DEMO-DAGGER", play={"id": "PLAY-DEMO-DAGGER", "version": "1.0.0"},
        players=[{"id": "DEMO-VIS-QB", "role": "QB", "position": {"x": 50, "y": 25}}, {"id": "DEMO-VIS-X", "role": "X", "position": {"x": 8, "y": 21}}, {"id": "DEMO-VIS-H", "role": "H", "position": {"x": 70, "y": 21}}],
        paths=[{"id": "VIS-PATH-X", "player_id": "DEMO-VIS-X", "points": [{"x": 8, "y": 21}, {"x": 8, "y": 12}, {"x": 28, "y": 5}], "style": "post"}, {"id": "VIS-PATH-H", "player_id": "DEMO-VIS-H", "points": [{"x": 70, "y": 21}, {"x": 70, "y": 13}, {"x": 51, "y": 13}], "style": "dig"}],
        timeline=[{"id": "VIS-T0", "time_ms": 0, "label": "Snap"}, {"id": "VIS-T1", "time_ms": 700, "label": "Read boundary safety"}, {"id": "VIS-T2", "time_ms": 1500, "label": "Throw window"}],
        role_views=["QB", "WR", "coach"], accessibility=["Dagger; shotgun trips right. QB reads the boundary safety. X runs a post and H runs a dig."],
    )
    visual["organization_id"] = organization_id
    visual["animation_timeline"] = build_animation_timeline(timeline_id="TIMELINE-DEMO-DAGGER", events=[{"id": "ANIM-DEMO-SNAP", "time_ms": 0, "target": "DEMO-VIS-QB", "action": "snap"}, {"id": "ANIM-DEMO-READ", "time_ms": 700, "target": "DEMO-VIS-X", "action": "reveal_route"}])
    return _stamp(visual, organization_id=organization_id, seed_id=seed_id)


def _write_demo_media(database_path: Path, *, organization_id: str, seed_id: str, enabled: bool) -> dict[str, Any]:
    root = database_path.parent / DEMO_MEDIA_DIRECTORY
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".nfl-fidos-demo-marker"
    marker.write_text(f"{DEMO_MARKER}\norganization_id={organization_id}\nseed_id={seed_id}\n", encoding="utf-8")
    output = root / f"{seed_id}.mp4"
    result = {"directory": str(root), "media_file": str(output), "available": False, "generator": "not_run"}
    if not enabled:
        result["generator"] = "disabled"
        return result
    ffmpeg = os.environ.get("NFL_FIDOS_FFMPEG", "ffmpeg")
    command = [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=0x13243f:s=640x360:d=4", "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=45)
        result["generator"] = "ffmpeg"
        result["return_code"] = completed.returncode
        result["available"] = completed.returncode == 0 and output.exists() and output.stat().st_size > 0
    except (OSError, subprocess.SubprocessError) as exc:
        result["generator"] = "unavailable"
        result["error"] = str(exc)
    return result


def _extra_records(*, organization_id: str, season: str, team_id: str, source_ref: str, seed_id: str, media: dict[str, Any], designs: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    media_path = Path(media["media_file"])
    media_uri = media_path.as_uri()
    film_asset = register_film_asset(asset_id="FILM-DEMO-GAME-001", uri=media_uri, duration_seconds=4.0, source={"kind": "synthetic_fixture", "ref": source_ref}, captured_at=DEMO_DATE, team_context=team_id)
    film_asset.update({"media_type": "video/mp4", "file_name": media_path.name, "size_bytes": media_path.stat().st_size if media_path.exists() else 0, "sha256": hashlib.sha256(media_path.read_bytes()).hexdigest() if media_path.exists() else "0" * 64, "media_available": bool(media.get("available"))})
    film_clip = create_film_clip(clip_id="CLIP-DEMO-GAME-001", asset=film_asset, start_seconds=0.4, end_seconds=3.6, team=team_id, opponent="OPP-DEMO-LIONS", situation="third_down")
    observation = build_film_observation(observation_id="FILM-OBS-DEMO-001", clip_id=film_clip["id"], asset_id=film_asset["id"], domain="coverage", label="Cover 3 buzz rotation", team=team_id, opponent="OPP-DEMO-LIONS", situation={"down": 3, "distance": "medium"}, source_frame="00:01.200", confidence="high", observed_or_inferred="observed", annotator=DEMO_ANALYST, evidence="Synthetic teaching clip shows late safety rotation.")
    grade = build_assignment_grade(grade_id="GRADE-DEMO-QB-001", observation=observation, player_id="DEMO-QB-1", assignment="Confirm boundary safety", grade="plus", assignment_basis="coach_annotation", confidence="moderate", evidence_refs=[source_ref], grader=DEMO_COACH)
    playlist = build_film_playlist(playlist_id="PLAYLIST-DEMO-THIRD-DOWN", name="Demo · Third-down rotation", purpose="Teach the Cover 3 rotation and QB boundary read.", clip_ids=[film_clip["id"]], filters={"opponent": "OPP-DEMO-LIONS", "situation": "third_down"}, owner=DEMO_ANALYST, access_roles=["program_owner", "coach_staff", "analyst", "player"])
    qa = validate_film_qa(qa_id="QA-DEMO-GAME-001", clips=[film_clip], observations=[observation], reviewer=DEMO_ANALYST)
    practice = build_practice_architecture(practice_id="PRACTICE-DEMO-WEEK-1", team_context=team_id, season_phase="regular_season", week_context="WEEK-1", objective="Install Dagger and Cover 3 buzz rotation", opponent_priorities=["third-down pressure", "late safety rotation"], periods=[{"id": "PERIOD-DEMO-QB", "type": "individual", "objective": "confirm shell before throw", "owner": DEMO_COACH, "players": ["DEMO-QB-1"], "minutes": 8, "reps": 12, "learning_rationale": "Build decision speed.", "load_rationale": "Moderate cognitive load."}, {"id": "PERIOD-DEMO-TEAM", "type": "team", "objective": "connect offense and defense teaching clips", "owner": DEMO_COACH, "players": ["offense", "defense"], "minutes": 18, "reps": 10, "learning_rationale": "Transfer the read into team tempo.", "load_rationale": "Controlled team volume."}], staff_available=[DEMO_COACH, DEMO_ANALYST], facility_constraints=[], load_controls={"max_total_minutes": 40, "max_reps_by_position": {"QB": 20, "DB": 20}}, restrictions=[])
    offense_scheme = build_scheme({"id": "SCHEME-DEMO-OFFENSE", "version": "1.0.0", "unit": "offense", "name": "Demo Spread Dagger", "components": [{"id": "SC-DEMO-PERSONNEL", "kind": "personnel", "label": "11 personnel"}, {"id": "SC-DEMO-FORMATION", "kind": "formation", "label": "shotgun trips"}, {"id": "SC-DEMO-CONCEPT", "kind": "concept", "label": "Dagger"}], "assignments": [{"role": "QB", "responsibility": "read boundary safety"}, {"role": "X", "responsibility": "post"}], "constraints": [], "source": {"kind": "synthetic_fixture", "ref": source_ref}})
    defense_scheme = build_scheme({"id": "SCHEME-DEMO-DEFENSE", "version": "1.0.0", "unit": "defense", "name": "Demo 4-2-5 Buzz", "components": [{"id": "SC-DEMO-FRONT", "kind": "front", "label": "4-2-5 over"}, {"id": "SC-DEMO-COVERAGE", "kind": "coverage", "label": "Cover 3 buzz"}, {"id": "SC-DEMO-PRESSURE", "kind": "pressure_or_check", "label": "TEX stunt"}], "assignments": [{"role": "FS", "responsibility": "deep middle"}, {"role": "MLB", "responsibility": "fit A gap"}], "constraints": [], "source": {"kind": "synthetic_fixture", "ref": source_ref}})
    opponent_profile = build_opponent_profile(profile_id="OPP-PROFILE-DEMO-LIONS", opponent="OPP-DEMO-LIONS", season=season, schedule_context={"week": 1, "venue": "away"}, roster_context={"source": "synthetic_fixture"}, offense={"formations": ["11 personnel", "pistol"], "tendencies": ["wide zone" ]}, defense={"coverages": ["cover_3", "quarters"], "pressure_rate": 0.34}, special_teams={"units": ["punt"]}, sources=[{"kind": "team_film", "ref": source_ref, "captured_at": DEMO_DATE}])
    scouting_report = build_situational_scouting_report(report_id="SCOUT-REPORT-DEMO-THIRD-DOWN", opponent="OPP-DEMO-LIONS", situation={"down": 3, "distance": "medium"}, claims=[{"classification": "observed", "confidence": "moderate", "uncertainty": ["eight-play sample"], "evidence_refs": ["FILM-DEMO-GAME-001"]}], sample_size=8, source_refs=[source_ref], analyst=DEMO_ANALYST)
    matchup = build_matchup_model(model_id="MATCHUP-DEMO-WR-CB", opponent="OPP-DEMO-LIONS", matchups=[{"our_role": "DEMO-WR-X", "opponent_role": "OPP-CB-1", "advantage_hypothesis": "win outside leverage", "counter": "stack release", "uncertainty": "small sample"}], evidence_refs=[source_ref], context={"situation": "third_down"}, analyst=DEMO_ANALYST)
    evolution = build_opponent_evolution(evolution_id="EVOLUTION-DEMO-LIONS", opponent="OPP-DEMO-LIONS", historical_claims=[{"claim": "Middle-field closed on early downs"}], current_claims=[{"claim": "Late safety rotation increased on third down"}], evidence_refs=[source_ref], analyst=DEMO_ANALYST)
    metric_definition = {"id": "METRIC-DEF-DEMO-EPA", "name": "Third-down success rate", "unit": "rate", "definition": "Conversions / opportunities", "required_data": ["play_id", "down", "conversion"], "formula": "successes / opportunities", "context_dimensions": ["situation"], "caveats": ["Synthetic sample"], "validation_method": "staff review", "consumers": ["coach_staff"]}
    metric = calculate_metric(definition=metric_definition, numerator=6, denominator=10, context={"situation": "third_down"}, source={"kind": "synthetic_analytics", "ref": source_ref}, observation_ids=["PLAY-DEMO-DAGGER"])
    analytics_report = build_analytics_report(report_id="ANALYTICS-REPORT-DEMO-THIRD-DOWN", audience="coach_staff", metric_observations=[metric], context={"situation": "third_down"}, caveats=["Synthetic ten-play sample; staff review required."], analyst=DEMO_ANALYST)
    game_plan = build_weekly_game_plan(plan_id="GAMEPLAN-DEMO-WEEK-1", team_context=team_id, week_context="WEEK-1", identity={"offense": "shotgun-spread", "defense": "4-2-5-match"}, assumptions=["Synthetic opponent sample is intentionally small."], evidence_refs=[source_ref], offense={"base_calls": ["Dagger", "Inside Zone"]}, defense={"base_calls": ["Cover 3", "Sim Pressure"]}, special_teams={"base_calls": ["Punt Safe"]}, opening_script=[{"call": "Dagger", "owner": "DEMO-OC"}], base_calls=[{"call": "Inside Zone", "owner": "DEMO-OC"}], shot_plan=[{"call": "Dagger", "owner": "DEMO-OC"}], pressure_answers=[{"threat": "mugged linebackers", "answer": "slide and hot", "owner": "DEMO-OC"}], situational_plans=[{"situation": "third_down", "primary": "Dagger", "opponent_responses": ["pressure", "match coverage"], "counters": ["hot", "sprint out"]}], matchups=[{"player": "DEMO-WR-X", "opponent": "OPP-CB-1", "plan": "attack leverage"}], contingencies=[{"id": "TRIGGER-DEMO-PRESSURE", "trigger": "pressure_rate > 40%", "response": "check to quick game", "owner": "DEMO-OC", "evidence_refs": [source_ref]}], ownership={"head_coach": "DEMO-HC", "offense": "DEMO-OC", "defense": "DEMO-DC", "special_teams": "DEMO-STC"}, teaching_outputs=[{"role": "QB", "message": "Confirm the boundary safety before the Dagger read."}], in_game_update={"cadence": "series", "owner": "DEMO-HC"})
    extended_play = build_extended_play({"id": "PLAY-DEMO-DAGGER", "version": "1.0.0", "unit": "offense", "formation": "shotgun_trips_right", "personnel": "11", "assignments": [{"role": "QB", "assignment": "read boundary safety", "responsibility": "read boundary safety"}, {"role": "X", "assignment": "post", "responsibility": "win outside leverage"}], "source": {"kind": "synthetic_fixture", "ref": source_ref}, "status": "draft"}, play_family_id="FAMILY-DEMO-DAGGER", install_level="core", checks=[{"id": "CHECK-DEMO-PRESSURE", "trigger": "mugged backers", "response": "slide and hot"}], situational_variants=[{"situation": "third_down", "change": "convert dig to choice"}], opponent_notes=["Expect late safety rotation."], coaching_notes=["Teach the key before the route detail."], dependencies=["SCHEME-DEMO-OFFENSE"])
    records: list[tuple[str, dict[str, Any]]] = [
        ("players", {"id": "PLAYER-DEMO-QB-1", "name": "Jordan Vale", "position": "QB", "number": 7, "status": "active", "depth_chart": 1, "person_id": "DEMO-QB-1"}),
        ("players", {"id": "PLAYER-DEMO-WR-X", "name": "Eli Brooks", "position": "WR", "number": 81, "status": "active", "depth_chart": 1, "person_id": "DEMO-WR-X"}),
        ("staff", {"id": "STAFF-DEMO-OC", "name": "Taylor Quinn", "role": "offensive_coordinator", "status": "active", "person_id": "DEMO-OC"}),
        ("plays", {"id": "PLAY-DEMO-DAGGER", "version": "1.0.0", "name": "Dagger / Boundary Read", "unit": "offense", "formation": "shotgun_trips_right", "personnel": "11", "concept": "Dagger", "status": "published", "play_design_id": designs["offense"]["id"], "source": {"kind": "synthetic_fixture", "ref": source_ref}}),
        ("plays", {"id": "PLAY-DEMO-COVER3", "version": "1.0.0", "name": "4-2-5 Cover 3 Buzz", "unit": "defense", "formation": "4-2-5_over", "front": "4-2-5_over", "coverage": "cover_3", "status": "under_review", "play_design_id": designs["defense"]["id"], "source": {"kind": "synthetic_fixture", "ref": source_ref}}),
        ("playbook_drafts", extended_play),
        ("play_views", {"id": "VIEW-PLAY-DEMO-DAGGER-QB", "play_id": "PLAY-DEMO-DAGGER", "role": "QB", "status": "renderable", "assignments": [{"role": "QB", "responsibility": "read boundary safety"}], "accessible_text": "Dagger; quarterback reads the boundary safety before choosing the post or dig."}),
        ("player_assignments", {"id": "ASSIGNMENT-DEMO-QB-001", "player_id": "PLAYER-DEMO-QB-1", "title": "Dagger boundary-safety read", "assignment_type": "play_lesson", "artifact_id": "PD-DEMO-OFF-DAGGER", "due_date": "2026-08-26", "owner": DEMO_COACH, "source_refs": [source_ref], "status": "assigned", "human_review_required": False}),
        ("lessons", {"id": "LESSON-DEMO-QB-DAGGER", "player_id": "PLAYER-DEMO-QB-1", "learner_role": "QB", "title": "Dagger: boundary read", "source_play_id": "PLAY-DEMO-DAGGER", "status": "assigned", "steps": [{"id": "LESSON-STEP-1", "instruction": "Identify the boundary safety."}, {"id": "LESSON-STEP-2", "instruction": "Choose post or dig based on leverage."}]}),
        ("mastery_records", {"id": "MASTERY-RECORD-DEMO-QB", "player_id": "PLAYER-DEMO-QB-1", "learner_id": "PLAYER-DEMO-QB-1", "capability_id": "CAP-READ-SHELL", "current_level": "developing", "target_level": "functional", "score": 0.8, "status": "in_progress", "evidence_refs": ["MASTERY-DEMO-OFF-QB-001"], "next_actions": ["Repeat the read under pressure."]}),
        ("development_plans", {"id": "DEVELOPMENT-DEMO-QB", "player_id": "PLAYER-DEMO-QB-1", "title": "Quarterback decision speed", "status": "active", "objectives": [{"capability_id": "CAP-READ-SHELL", "measure": "4 of 5 correct reads"}], "owner": DEMO_COACH}),
        ("film_assets", film_asset),
        ("film_clips", film_clip),
        ("film_observations", observation),
        ("film_assignment_grades", grade),
        ("film_playlists", playlist),
        ("film_qa", qa),
        ("film_quizzes", {"id": "QUIZ-DEMO-FILM-COVER3", "title": "Cover 3 buzz rotation", "organization_id": organization_id, "role": "MLB", "clip_ids": [film_clip["id"]], "questions": [{"id": "QUESTION-DEMO-1", "prompt": "Who owns the deep middle?", "answer": "FS"}], "owner": DEMO_ANALYST, "status": "ready"}),
        ("film_quiz_attempts", {"id": "QUIZ-ATTEMPT-DEMO-1", "quiz_id": "QUIZ-DEMO-FILM-COVER3", "participant": "PLAYER-DEMO-QB-1", "score": 0.8, "status": "under_review", "human_review_required": True}),
        ("film_annotation_sessions", {"id": "SESSION-DEMO-FILM-001", "clip_id": film_clip["id"], "annotator": DEMO_ANALYST, "allowed_domains": ["coverage", "pressure"], "source_refs": [source_ref], "status": "open", "annotations": []}),
        ("practice_plans", practice),
        ("schemes", offense_scheme),
        ("schemes", defense_scheme),
        ("countermeasures", build_game_plan_countermeasure(countermeasure_id="COUNTERMEASURE-DEMO-PRESSURE", threat="mugged linebackers", primary_response="slide and hot", opponent_counter="drop eight", counter_counter="screen", trigger="two backers threaten both A gaps", evidence_refs=[source_ref], owner="DEMO-OC")),
        ("compatibility_results", {"id": "COMPAT-DEMO-OFFENSE", "scheme_id": "SCHEME-DEMO-OFFENSE", "play_id": "PLAY-DEMO-DAGGER", "compatible": True, "reasons": ["Personnel, formation, and concept are aligned."]}),
        ("red_team_matrices", {"id": "REDTEAM-DEMO-WEEK-1", "unit": "offense", "threats": [{"threat": "Cover 3 buzz", "answer": "Dagger with boundary read", "confidence": "moderate"}], "status": "under_review", "human_review_required": True}),
        ("opponent_profiles", opponent_profile),
        ("scouting_reports", scouting_report),
        ("matchup_models", matchup),
        ("opponent_evolutions", evolution),
        ("metric_observations", metric),
        ("analytics_reports", analytics_report),
        ("game_plans", game_plan),
        ("rule_recommendations", {"id": "RULE-RECOMMENDATION-DEMO-001", "topic": "Defensive contact and motion review", "source_refs": ["https://operations.nfl.com/the-rules/nfl-rulebook"], "status": "under_review", "recommendation": "Keep the synthetic play model under NFL rule-profile review.", "human_review_required": True}),
        ("game_plan_review_threads", {"id": "GAMEPLAN-THREAD-DEMO-001", "plan_id": "GAMEPLAN-DEMO-WEEK-1", "week": "WEEK-1", "topic": "Third-down answer", "status": "open", "created_by": DEMO_ANALYST, "created_role": "analyst", "created_at": DEMO_DATE, "comments": [{"id": "COMMENT-GAMEPLAN-DEMO-001", "author": DEMO_ANALYST, "role": "analyst", "body": "Confirm the hot answer against the late rotation.", "evidence_refs": [source_ref], "created_at": DEMO_DATE}], "decision": None, "human_decision_required": True}),
        ("weekly_delivery_packages", {"id": "WEEKLY-DELIVERY-DEMO-WEEK-1", "game_plan_id": "GAMEPLAN-DEMO-WEEK-1", "status": "under_review", "blockers": ["Synthetic dataset requires coach interpretation before activation."], "human_approval_required": True}),
        ("release_candidates", {"id": "RC-DEMO-WEEK-1", "status": "blocked", "blockers": ["Stage 0 owner approval and live pilot evidence remain external gates."], "human_approval_required": True}),
        ("governance_audits", {"id": "AUDIT-DEMO-WEEK-1", "status": "under_review", "issues": ["Synthetic fixture; no production activation permitted."], "observability_evidence": ["TRACE-DEMO-WEEK-1"], "human_approval_required": True}),
        ("game_plan_snapshots", {"id": "GAMEPLAN-SNAPSHOT-DEMO-WEEK-1", "game_plan_id": "GAMEPLAN-DEMO-WEEK-1", "week": "WEEK-1", "immutable": True, "content_checksum": "demo-snapshot", "status": "locked_for_demo"}),
        ("visual_plays", _build_visual(organization_id, seed_id=seed_id)),
        ("visual_scenarios", {"id": "SIM-DEMO-COVERAGE-ROTATE", "source_visual_id": "VISUAL-DEMO-DAGGER", "adjustment": {"type": "rotate_coverage"}, "requester_role": "coach_staff", "status": "scenario_ready", "human_review_required": True, "canonical_unchanged": True}),
        ("knowledge_sources", {"id": "SOURCE-DEMO-RULEBOOK", "uri": "https://operations.nfl.com/the-rules/nfl-rulebook", "classification": "rule", "authorization_status": "authorized", "status": "current", "title": "NFL rulebook reference (synthetic link metadata)", "freshness": {"captured_at": DEMO_DATE}}),
        ("knowledge_items", {"id": "KNOWLEDGE-DEMO-COVER3", "normalized_claim": "Cover 3 buzz rotation is a teaching example, not a verified opponent fact.", "classification": "team_knowledge", "state": "current", "source_id": "SOURCE-DEMO-RULEBOOK", "citation": {"source_ref": source_ref, "location": "synthetic teaching note"}, "status": "under_review", "human_review_required": True}),
        ("media_processing_jobs", {"id": "MEDIA-JOB-DEMO-THUMBNAIL", "asset_id": film_asset["id"], "operation": "thumbnail", "payload": {"file_path": str(media_path), "allowed_roots": [str(media_path.parent)]}, "requested_by": DEMO_ANALYST, "status": "queued", "attempt": 0, "max_attempts": 3, "created_at": DEMO_DATE, "updated_at": DEMO_DATE, "issues": []}),
        ("agent_runs", {"id": "RUN-DEMO-VALIDATION-001", "organization_id": organization_id, "agent_id": "AGT-DEMO-VALIDATOR", "family": "validation", "capability": "validate", "workflow_id": "WF-DEMO-PLAY-001", "status": "completed", "local_validation": True, "provider_called": False, "payload": {"play_id": "PD-DEMO-OFF-DAGGER"}, "result": {"status": "passed", "checks": ["structure", "timeline", "NFL profile"]}}),
        ("change_requests", {"id": "CHANGE-DEMO-PLAY-DESIGN", "request_type": "play_design_update", "target_id": "PD-DEMO-DEF-COVER3", "status": "under_review", "requester": DEMO_ANALYST, "rationale": "Clarify weakside fit language before release.", "evidence_refs": [source_ref], "human_review_required": True}),
        ("decisions", {"id": "DECISION-DEMO-PLAY-REVIEW", "decision_type": "staff_review", "status": "pending", "target_id": "PD-DEMO-DEF-COVER3", "decision_ref": "DEC-DEMO-PLAY-REVIEW-DEFENSE", "owner": DEMO_OWNER, "human_approval_required": True}),
    ]
    return records


def _known_collections(repository: JsonRepository | SqliteRepository) -> set[str]:
    return {str(event.get("collection")) for event in repository.history() if event.get("collection")}


def _is_demo_record(collection: str, record: dict[str, Any], *, organization_id: str, seed_id: str) -> bool:
    if record.get("organization_id") != organization_id:
        return False
    if record.get("synthetic_demo") is True and record.get("demo_seed_id") == seed_id:
        return True
    nested = record.get("design") if isinstance(record.get("design"), dict) else None
    return bool(nested and nested.get("synthetic_demo") is True and nested.get("demo_seed_id") == seed_id)


def find_demo_records(repository: JsonRepository | SqliteRepository, *, organization_id: str = DEMO_ORGANIZATION_ID, seed_id: str = DEMO_SEED_ID) -> dict[str, int]:
    _validate_scope(organization_id, seed_id)
    counts: dict[str, int] = {}
    for collection in sorted(_known_collections(repository)):
        count = sum(1 for record in repository.list(collection) if _is_demo_record(collection, record, organization_id=organization_id, seed_id=seed_id))
        if count:
            counts[collection] = count
    return counts


def _purge(repository: JsonRepository | SqliteRepository, *, database_path: Path, organization_id: str, seed_id: str, remove_media: bool = True) -> dict[str, Any]:
    counts = find_demo_records(repository, organization_id=organization_id, seed_id=seed_id)
    result = repository.delete_where(lambda collection, record: _is_demo_record(collection, record, organization_id=organization_id, seed_id=seed_id))
    media_result = {"removed": [], "preserved": []}
    if remove_media:
        root = (database_path.parent / DEMO_MEDIA_DIRECTORY).resolve()
        marker = root / ".nfl-fidos-demo-marker"
        marker_is_owned = marker.exists() and DEMO_MARKER in marker.read_text(encoding="utf-8", errors="replace") and f"organization_id={organization_id}" in marker.read_text(encoding="utf-8", errors="replace") and f"seed_id={seed_id}" in marker.read_text(encoding="utf-8", errors="replace")
        if marker_is_owned:
            expected_file = root / f"{seed_id}.mp4"
            for path in (expected_file, marker):
                if path.exists() and path.is_file():
                    path.unlink()
                    media_result["removed"].append(str(path))
            if root.exists() and root.is_dir() and not any(root.iterdir()):
                try:
                    root.rmdir()
                except OSError:
                    # OneDrive/antivirus/indexer races can briefly deny removal
                    # after the owned files are deleted. Preserve the empty
                    # directory and report it instead of failing the data purge.
                    media_result["preserved"].append(str(root))
        elif root.exists():
            media_result["preserved"].append(str(root))
    return {"status": "purged", "organization_id": organization_id, "seed_id": seed_id, "matched_before_delete": counts, **result, "media": media_result, "production_implementation_allowed": False}


def purge_demo_data(repository: JsonRepository | SqliteRepository, *, database_path: str | Path, organization_id: str = DEMO_ORGANIZATION_ID, seed_id: str = DEMO_SEED_ID) -> dict[str, Any]:
    """Remove only the exact synthetic demo seed from a local repository."""
    path = Path(database_path).expanduser().resolve()
    _validate_scope(organization_id, seed_id)
    environment = os.environ.get("NFL_FIDOS_ENV", "local").lower()
    if environment == "production":
        raise RuntimeError("Synthetic demo cleanup is blocked when NFL_FIDOS_ENV=production")
    if "var" in path.parts and "lib" in path.parts and "nfl-fidos" in path.parts:
        raise RuntimeError("Synthetic demo cleanup is blocked for the production data mount")
    return _purge(repository, database_path=path, organization_id=organization_id, seed_id=seed_id)


def seed_demo_data(repository: JsonRepository | SqliteRepository, *, database_path: str | Path, organization_id: str = DEMO_ORGANIZATION_ID, seed_id: str = DEMO_SEED_ID, replace: bool = False, replace_confirmed: bool = False, generate_media: bool = True) -> dict[str, Any]:
    """Populate a real local repository with a marked, repeatable showcase tenant."""
    path = Path(database_path).expanduser().resolve()
    _validate_scope(organization_id, seed_id)
    if os.environ.get("NFL_FIDOS_ENV", "local").lower() == "production":
        raise RuntimeError("Synthetic demo seeding is blocked when NFL_FIDOS_ENV=production")
    existing = find_demo_records(repository, organization_id=organization_id, seed_id=seed_id)
    if existing and not replace:
        return {"status": "already_seeded", "organization_id": organization_id, "seed_id": seed_id, "record_counts": existing, "message": "The exact synthetic seed already exists. Use --replace with its explicit confirmation to recreate it."}
    if replace:
        if not replace_confirmed:
            raise ValueError("Replacing demo data requires explicit confirmation: RESEED-SYNTHETIC-DEMO-DATA")
        _purge(repository, database_path=path, organization_id=organization_id, seed_id=seed_id)

    source_ref = _source_ref(seed_id)
    components = _build_operating_components(organization_id=organization_id, season=DEMO_SEASON, team_id=DEMO_TEAM_ID, source_ref=source_ref)
    media = _write_demo_media(path, organization_id=organization_id, seed_id=seed_id, enabled=generate_media)
    tenant = TenantRepository(repository, organization_id=organization_id, actor=DEMO_ACTOR)
    for component_name, record in components.items():
        _put(tenant, COMPONENT_COLLECTIONS[component_name], record, seed_id=seed_id)
    bundle = build_organization_operating_bundle(bundle_id="ORG-BUNDLE-DEMO-2026", organization_id=organization_id, season=DEMO_SEASON, components=components)
    _put(tenant, "organization_operating_bundles", bundle, seed_id=seed_id)
    designs = _seed_play_designs(tenant, seed_id=seed_id)
    for collection, record in _extra_records(organization_id=organization_id, season=DEMO_SEASON, team_id=DEMO_TEAM_ID, source_ref=source_ref, seed_id=seed_id, media=media, designs=designs):
        _put(tenant, collection, record, seed_id=seed_id)
    # The package records are intentionally ready for owner review; the demo
    # never activates production or records real approval evidence.
    run = {"id": f"{seed_id}-RUN", "organization_id": organization_id, "seed_id": seed_id, "status": "active", "synthetic_demo": True, "demo_marker": DEMO_MARKER, "created_at": datetime.now(timezone.utc).isoformat(), "media": media, "notes": "Synthetic showcase data only. Do not treat as a live organization, approval, roster, source, or production release.", "production_implementation_allowed": False}
    _put(tenant, "demo_seed_runs", run, seed_id=seed_id)
    return {"status": "seeded", "organization_id": organization_id, "seed_id": seed_id, "record_counts": find_demo_records(repository, organization_id=organization_id, seed_id=seed_id), "media": media, "demo_entry_points": {"dashboard": "/operator-dashboard", "play_designer": "PD-DEMO-OFF-DAGGER", "defensive_play": "PD-DEMO-DEF-COVER3", "published_release": "PD-DEMO-OFF-DAGGER", "player": "PLAYER-DEMO-QB-1", "opponent": "OPP-DEMO-LIONS", "week": "WEEK-1"}, "production_implementation_allowed": False, "external_state_changed": False}
