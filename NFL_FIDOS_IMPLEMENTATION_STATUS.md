# NFL FIDOS Implementation Status

This is a living traceability summary against the uploaded Master Codex Plan. It is not a claim that the entire 26-stage program is complete.

Current Play Designer catalog verification (2026-08-29): the canonical
`playbook/asset-registry.json` contains 128 valid assets across 13 authoring
families, including the expanded professional front, coverage, pressure,
line-game, rotation, blocking, protection, route, motion, run, check, and
teaching vocabulary. The registry service contract passes and the React asset
palette consumes the same organization-aware compatibility and lifecycle data.

## New operational systems implemented in the current slice

| System | Current connected capability |
| --- | --- |
| Unified Operations Inbox | Role-scoped aggregation of reviews, tasks, notifications, open collaboration threads, due state, urgency, ownership, blockers, evidence, read acknowledgement, and safe deep links. |
| Film Intelligence Studio | Authenticated media loading, bounded video playback, frame stepping, timeline control, pointer telestration, frame-linked player tracking, bounded clip creation, transcript-backed voice-note capture with an inline 256 KiB safety limit, source-linked observation handoff, governed downstream links to Playbook/Scouting/Player Development/Game Plan/Analytics records with context-aware navigation, and authenticated `index` jobs that persist bounded searchable stream metadata. |
| Roster / Personnel | Organization-scoped player identity, position and availability, depth charts, personnel packages, roster-driven Practice selectors, and player privacy filtering. |
| Practice / Install | Period builder with drag/keyboard ordering, live Roster and Playbook catalog selectors, play/drill IDs, install phase, coaching objective, attendance policy, roster IDs, load envelope, print preference persistence, roster-linked attendance, and period-specific rep outcomes linked into Analytics. |
| Game Plan Release Room | Immutable snapshots with dependency manifests, linked/unresolved evidence refs, release-manifest hash, renderer version, changed-field summary, owner approval/lock, and explicit rollback. |
| Scouting Tendency Explorer | Organization-scoped server-backed tendency query across down, distance, field zone, personnel, formation, motion, front, coverage, and pressure with normalized claims, sample/confidence context, trends, source clips/evidence, explicit and stance-derived contradictions, explainable review gates, and collaboration handoff into Game Plan review. |
| Player Learning Hub | Privacy-scoped assignments, lessons, read reveal, mastery, quizzes, coach assignment, and privacy-scoped offline cache fallback. |
| Staff Collaboration / Notifications | Organization-scoped cross-system threads with linked entities and safe deep links, replies, mentions, assignments, due dates, priority, resolution/reopen, recipient-scoped notifications, activity feed, expiring presence heartbeat, and audit-backed state changes. Existing governed Game Plan threads and Play Designer SSE collaboration remain authoritative in their workspaces. |
| Outcome Analytics | Lineage-complete observations, structured intended-versus-actual outcome records, linked play/practice/film/game-plan evidence, sample-size-aware confidence, Wilson uncertainty, situation filtering, design-to-outcome comparison, and staff report composition. |
| Game-Week Delivery Center | Task calendar, deadlines, owner assignment, completion audit, packet output checklist, release readiness, internal owner notifications with safe Delivery deep links, and explicit non-publishing boundary. |

## Verified implementation foundations

| Master Plan area | Capability / workflow | Implementation | Evidence |
| --- | --- | --- | --- |
| Stage 0 control plane | Registry, stable IDs, stage gates | `control/` | `scripts/validate_control_plane.py` passes |
| Play Designer state-of-the-art build | Professional asset registry and searchable palette; drag-to-draw offense/defense editor; route handles, landmarks, timing, layers, snapping, grouping, mirroring, and defensive assignments; timeline playback and narration; organization-scoped autosave, encrypted offline queue, recovery, retry, and conflict handling; authenticated SSE collaboration with short-poll fallback, presence, threads, replies, resolution, branching, immutable publishing, diffs, merges, rollback, and release checksums; role-filtered teaching/player views, quizzes, mastery, and practice linkage; production PDF/SVG/PNG/HTML/JSON/CSV exports with call-sheet, wristband, install-sheet, accessibility text, branding, and black-and-white layouts; NFL/NCAA/high-school/youth/flag legality profiles with explainable owner overrides; security, rate limiting, tenant checks, signed exports, redacted audit events, quality gates, visual baseline, and pilot-readiness evidence | `src/nfl_fidos/play_design_service.py`, `src/nfl_fidos/play_legality.py`, `src/nfl_fidos/play_design_exports.py`, `src/nfl_fidos/play_design_versioning.py`, `src/nfl_fidos/play_design_collaboration.py`, `src/nfl_fidos/play_designer_quality.py`, `src/nfl_fidos/security_controls.py`, `src/nfl_fidos/http_server.py`, `frontend/src/pages/PlayDesignerPage.tsx`, `frontend/src/play-designer/TemplateLibraryPanel.tsx`, `frontend/src/lib/api.ts`, `ui/play-designer*.js`, `ui/play-designer*.css`, `playbook/asset-registry.json`, `rules/play-design-rule-profiles.json`, `control/security-threat-model.json`, `control/play-designer-visual-baseline.json`, `tests/test_play_design_*.py`, `tests/test_play_designer_quality.py`, `tests/test_pilot_verification.py`, `tests/test_http_server.py`, `frontend/src/play-designer/TemplateLibraryPanel.test.tsx` | Local implementation and integration suite pass: 650 Python tests, 252 frontend tests, 97/97 eval families, control-plane validation, browser-evidence validation, deployment-contract validation, security/quality gates, synthetic pilot rehearsal, PDF structural/visual QA, and persisted release-bundle manifest recheck coverage; production provider setup, moderated pilot, cross-browser/accessibility matrix, and Stage 0 authorization remain gated |
| React frontend incremental migration — Today, Playbook, operational workbenches, and Play Designer | Separate React 19 + TypeScript application mounted at `/app` while the Python API and football-domain services remain authoritative; reusable tokens, descriptions, query hooks, workbench controls, and responsive role-aware navigation; Today command center; visual searchable Playbook; independently lazy-loaded Inbox, Roster, Analytics, Delivery, Film, Practice, Scouting, Game Plan, Player, Admin, and Reviews workbenches; dedicated Stage 25 specification acceptance route; full-screen Play Designer with an eight-step completion-aware tutorial, permanent contextual guidance, canonical registry, pointer/keyboard authoring, timing/playback, autosave/conflict handling, review/publish/branch, legality, history, comments, and export handoff; tab-scoped credentials; focus management; reduced motion; safe SPA/static serving; enforced bundle budgets; Docker and CI integration | `frontend/`, `frontend/src/components/OperationalWorkbench.tsx`, `frontend/src/hooks/useOperationalData.ts`, `frontend/src/pages/OperationsInboxPage.tsx`, `frontend/src/pages/RosterPage.tsx`, `frontend/src/pages/AnalyticsPage.tsx`, `frontend/src/pages/DeliveryPage.tsx`, `frontend/src/pages/FilmPage.tsx`, `frontend/src/pages/PracticePage.tsx`, `frontend/src/pages/ScoutingPage.tsx`, `frontend/src/pages/GamePlanPage.tsx`, `frontend/src/pages/PlayerPage.tsx`, `frontend/src/pages/AdminPage.tsx`, `frontend/src/pages/Stage25AcceptancePage.tsx`, `frontend/src/pages/ReviewsPage.tsx`, `frontend/src/pages/PlayDesignerPage.tsx`, `src/nfl_fidos/governance_reviews.py`, `src/nfl_fidos/http_server.py`, `tests/test_governance_review_api.py`, `tests/test_http_server.py`, `Dockerfile`, `.github/workflows/ci.yml`, `runbooks/frontend-migration.md` | Production build passes; 82/82 frontend tests and 566/566 Python tests pass. Each migrated workspace is a separate lazy chunk under the local 30 KiB route budget, combined CSS remains under 90 KiB, and authenticated desktop plus 820px-tablet QA passed against seeded organization data. Canonical authority boundaries prevent generic approval from bypassing workflow-specific approval services. Advanced visual/coediting parity, deployment, moderated pilot evidence, and the legacy feature-parity audit remain pending |
| Stage 2 ontology | Canonical terms, alias registry, relationship graph, naming standard, resolver integration, persistent team aliases, organization bundles, approval metadata, source-linked team-usage validation corpus, and authenticated API queries | `ontology/football-terms.json`, `ontology/alias-registry.json`, `ontology/team-terminology-validation-corpus.json`, `ontology/relationship-graph.json`, `ontology/naming-standard.json`, `contracts/team-terminology.schema.json`, `contracts/organization-terminology.schema.json`, `organization/terminology-bundle-template.json`, `src/nfl_fidos/organization_terminology.py`, `src/nfl_fidos/team_ontology.py`, `src/nfl_fidos/terminology_usage.py`, `src/nfl_fidos/api.py`, `tests/test_organization_terminology.py`, `tests/test_team_ontology.py`, `tests/test_terminology_usage.py`, `tests/test_api.py` | Canonical usage fixtures resolve and mismatches require review; real organization population remains owner-dependent |
| Stage 3 agents | Callable handoffs and permissions | `src/nfl_fidos/agent_contracts.py` | Permission and payload tests pass |
| Stage 3 local agent adapter rehearsal | Deterministic adapters for all 16 controlled agent roles, explicit activation rehearsal, persisted handoffs, value-free outputs, and no-provider/no-canonical-write boundary | `src/nfl_fidos/local_agent_adapters.py`, `scripts/agent_runtime_rehearsal.py`, `runbooks/local-agent-adapters.md`, `tests/test_local_agent_adapters.py`, `tests/test_agent_runtime_rehearsal.py` | All 16 roles dispatch successfully in a temporary workspace; provider-specific adapters and credentials remain deployment-dependent |
| Stage 3 agent runtime API rehearsal | Authenticated, tenant-scoped local validation dispatch/readback for controlled agent roles with explicit local-only enforcement | `src/nfl_fidos/api.py`, `src/nfl_fidos/access.py`, `runbooks/agent-runtime-api.md`, `tests/test_agent_runtime_api.py` | Owner and validator dispatch/readback, role denial, explicit local-only enforcement, and organization isolation pass; provider adapters and production activation remain deployment-dependent |
| Organization population readiness | Tenant-scoped checklist for all thirteen operating-bundle components, explicit blockers, required states, and non-fabricating dashboard/API surface | `src/nfl_fidos/organization_population_readiness.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `runbooks/organization-population-readiness.md`, `tests/test_organization_population_readiness.py`, `tests/test_organization_population_readiness_api.py` | Empty and fully populated synthetic tenants report the correct readiness state; cross-tenant access and synthetic validation are blocked |
| Synthetic organization operating-set rehearsal | Real package builders, synthetic owner-validation transitions, tenant persistence, population readiness, persisted component resolution, and complete 13-component bundle composition | `scripts/organization_operating_set_rehearsal.py`, `runbooks/organization-operating-set-rehearsal.md`, `tests/test_organization_operating_set_rehearsal.py` | All 13 components compose to `ready_for_owner_review`; approval remains required and activation/production remain false |
| Stage 4 player development | Role-specific lesson generation | `src/nfl_fidos/player_learning.py` | Lesson traceability tests pass |
| Stage 9 play data | Minimum play record and compiler | `contracts/play-record.schema.json`, `src/nfl_fidos/play_compiler.py` | Valid/invalid compiler tests pass |
| Stage 10 playbook views | Role-based render model | `src/nfl_fidos/playbook_view.py` | Role/version tests pass |
| Stage 11–12 practice | Drill and practice-plan structure | `src/nfl_fidos/practice.py` | Measurable evaluation tests pass |
| Stage 14–15 film/scouting | Film tags, self-scout, tendencies | `src/nfl_fidos/film.py`, `src/nfl_fidos/scouting.py` | Context/provenance tests pass |
| Stage 16 analytics | Denominator/context/confidence model | `src/nfl_fidos/analytics.py` | Bounds and calibration tests pass |
| Stage 17 game planning | Evidence-aware options and counters | `src/nfl_fidos/game_plan.py` | Human decision boundary tests pass |
| Stage 18 rules | Source-linked authority and escalation | `src/nfl_fidos/rules.py` | Authority/escalation tests pass |
| Stage 19 evidence | Claim classification and provenance | `src/nfl_fidos/evidence.py` | Sample/context qualification tests pass |
| Stage 20 governance | Regression, permissions, safety boundaries | `tests/`, contracts, control gate | 558 regression tests and control validator pass |
| Stage 21 data foundation | Versioned canonical records and append-only audit events | `src/nfl_fidos/repository.py` | Persistence round-trip, revision, and history tests pass |
| Stage 23 engineering foundation | Service facade connecting compiler, lessons, and handoffs | `src/nfl_fidos/service.py` | Publish, rejection, lesson, and handoff tests pass |
| Stages 6–8 scheme foundation | Compositional offense/defense/special-teams model and countermeasures | `src/nfl_fidos/scheme.py`, `contracts/scheme-model.schema.json` | Component completeness, duplicate-role, and countermeasure tests pass |
| Stages 6–9 integration | Play-to-scheme compatibility and red-team matrix | `src/nfl_fidos/compatibility.py`, `contracts/compatibility-result.schema.json`, `contracts/red-team-matrix.schema.json` | Alias normalization, mismatch rejection, and red-team tests pass |
| Stage 2 team-context foundation | Runtime ontology resolver and locked team terminology registry | `src/nfl_fidos/ontology.py`, `src/nfl_fidos/team_context.py` | Canonical, unresolved, team-alias, conflict, and ambiguity tests pass |
| Organization onboarding boundary | Program-owner-only NFL organization context registration, draft terminology-bundle initialization, explicit DEC-linked approval transition, tenancy, and approval boundary | `src/nfl_fidos/organization_onboarding.py`, `src/nfl_fidos/api.py`, `contracts/organization-onboarding.schema.json`, `ui/operator-dashboard.html`, `tests/test_organization_onboarding.py`, `tests/test_organization_onboarding_api.py` | Draft context and bundle persist organization-scoped; non-owners are denied; activation requires an explicit decision record and production remains disabled |
| Organization operating bundle | Composed organization/terminology/doctrine/play/player/staff/drill/special-teams/performance/media/scouting/analytics/game-plan readiness, scope consistency, owner review, authenticated API, dashboard surface, and non-activation boundary | `src/nfl_fidos/organization_operating_bundle.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `contracts/organization-operating-bundle.schema.json`, `runbooks/organization-operating-bundle.md`, `tests/test_organization_operating_bundle.py`, `tests/test_organization_operating_bundle_api.py`, `tests/test_operator_ui.py` | Synthetic composition, tenancy, role boundaries, API lifecycle, live served dashboard controls, and owner-approval boundary pass; real organization package population and deployment remain owner/external-state dependent |
| Stage 11 position drill corpus | NFL position-family drills with competency links, correction models, progression ladders, measurable KPIs, film angles, and safety controls | `development/position-drill-libraries.json`, `src/nfl_fidos/position_drill_library.py`, `tests/test_position_drill_library.py` | 10 position families and 20 validated drills (minimum two per family); organization-specific and seasonal expansion remains |
| Stage 11 seasonal/role drill variants | Ten position-linked variants covering offseason, preseason, regular-season, and postseason contexts with role context, load adaptation, safety controls, and evaluation focus | `development/seasonal-role-drill-variants.json`, `contracts/seasonal-drill-variant.schema.json`, `src/nfl_fidos/seasonal_role_drill_variants.py`, `tests/test_seasonal_role_drill_variants.py` | Variant corpus validates; organization-specific drill validation remains |
| Stage 11 organization drill validation | Organization-scoped selection of base or seasonal drills by position and season, authorized source references, tenancy enforcement, under-review status, and explicit program-owner validation transition | `src/nfl_fidos/organization_drill_validation.py`, `src/nfl_fidos/api.py`, `contracts/organization-drill-validation.schema.json`, `runbooks/organization-drill-validation.md`, `tests/test_organization_drill_validation.py`, `tests/test_organization_drill_validation_api.py` | Package and owner-transition API tests pass; real organization source authorization remains |
| Stages 6–7 scheme-family corpus | Four offensive and four defensive compositional families with personnel fit, strengths/weaknesses, counters, counter-counters, adaptation logic, installation requirements, and nuance | `scheme/scheme-bible.json`, `src/nfl_fidos/scheme_family_corpus.py`, `tests/test_scheme_family_corpus.py` | 8 scheme families validate with counter depth; full team doctrine lineage remains |
| Stage 18 rule-source refresh control | Version-aware candidate registry comparison, change review, DEC-linked owner approval, and non-promoting future-rule handling | `src/nfl_fidos/rule_refresh.py`, `contracts/rule-source-refresh.schema.json`, `rules/rule-refresh-review-template.json`, `tests/test_rule_refresh.py` | Candidate refreshes remain under jurisdiction review and cannot promote automatically |
| Stage 20 evaluation foundation | Named eval families and machine-readable suite results | `src/nfl_fidos/evals.py`, `control/eval-manifest.json`, `contracts/eval-result.schema.json` | 97/97 eval families pass; 558 regression tests pass |
| Stage 13 performance ingestion boundary | Authorized source-kind validation, organization/privacy scope, provenance, malformed-record rejection, health-signal escalation, and non-diagnostic/no-provider guarantees | `src/nfl_fidos/performance_ingestion.py`, `contracts/performance-ingestion.schema.json`, `runbooks/performance-ingestion.md`, `tests/test_performance_ingestion.py` | Authorized, invalid, and health-signal batch tests pass |
| Stage 21 database scale rehearsal | Bounded two-tenant synthetic bulk-write/read rehearsal, audit-history verification, and cross-tenant isolation checks | `scripts/database_scale_rehearsal.py`, `runbooks/database-scale-rehearsal.md`, `tests/test_database_scale_rehearsal.py` | Temporary scale rehearsal passes with no external state change |
| Stage 15 validated scouting workflow | API and dashboard creation path now constructs reports through the scouting intelligence validator, preserves analyst identity, uncertainty, evidence refs, and under-review state | `src/nfl_fidos/scouting_intelligence.py`, `src/nfl_fidos/api.py`, `src/nfl_fidos/scouting_workspace.py`, `ui/operator-dashboard.html`, `tests/test_scouting_api.py`, `tests/test_operator_ui.py` | Valid report creation and invalid evidence rejection tests pass |
| Stage 14 real media-tool rehearsal | Temporary synthetic-media generation, FFprobe metadata extraction, FFmpeg transcode, thumbnail, and segmentation checks with fail-closed tool detection | `scripts/media_tool_smoke.py`, `runbooks/media-tool-smoke.md`, `tests/test_media_tool_smoke.py` | Real local FFmpeg/FFprobe rehearsal passed; production media remains gated |
| Stage 14 managed media storage rehearsal | Temporary two-tenant authorized storage, digest integrity, path isolation, duplicate protection, source-boundary enforcement, and non-destructive retention planning | `scripts/media_storage_scale_rehearsal.py`, `runbooks/media-storage-scale-rehearsal.md`, `tests/test_media_storage_scale_rehearsal.py` | Temporary storage rehearsal passes with no external state change; managed external storage deployment remains pending |
| Stage 9 cross-unit play compiler corpus | Six offense, defense, and special-teams play fixtures with unit-specific core-role validation, provenance, and red-team checks | `playbook/play-family-corpus.json`, `src/nfl_fidos/play_compiler.py`, `src/nfl_fidos/play_family_corpus.py`, `contracts/play-record.schema.json`, `tests/test_play_family_corpus.py` | Cross-unit compilation and missing-role rejection tests pass; organization-specific playbook expansion remains |
| Stage 9 organization play corpus package | Tenant-scoped organization/team/season corpus compilation, authorized source-reference linkage, compiler validation, owner approval, authenticated API, and non-activating validation flags | `contracts/organization-play-corpus.schema.json`, `src/nfl_fidos/organization_play_corpus.py`, `src/nfl_fidos/api.py`, `runbooks/organization-play-corpus.md`, `tests/test_organization_play_corpus.py`, `tests/test_organization_play_corpus_api.py` | Corpus compiler, tenant API, role boundary, approval, and production-gate tests pass; real organization doctrine and source authorization remain pending |
| Stages 6–8 organization doctrine package | Tenant-scoped offensive/defensive scheme-family and special-teams reference selection, source linkage, compiler validation, owner review transition, authenticated API, and non-activating flags | `contracts/organization-doctrine.schema.json`, `src/nfl_fidos/organization_doctrine.py`, `src/nfl_fidos/api.py`, `runbooks/organization-doctrine.md`, `tests/test_organization_doctrine.py`, `tests/test_organization_doctrine_api.py` | Reference package, owner transition, role boundary, tenancy, and production-gate tests pass; real team doctrine and source authorization remain pending |
| Stage 5 organization staff review package | Tenant-scoped staff roster, role-dimension mapping, observable evidence-linked coaching evaluations, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-staff-review.schema.json`, `src/nfl_fidos/organization_staff_review.py`, `src/nfl_fidos/coach_development.py`, `src/nfl_fidos/api.py`, `runbooks/organization-staff-review.md`, `tests/test_organization_staff_review.py`, `tests/test_organization_staff_review_api.py` | Staff package, evaluation completeness, role boundary, tenancy, owner transition, and production-gate tests pass; real staff records and live review operations remain pending |
| Stage 4 organization player development package | Tenant-scoped player IDPs, measurable objectives, mastery evidence, privacy-filtered player access, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-player-development.schema.json`, `src/nfl_fidos/organization_player_development.py`, `src/nfl_fidos/development.py`, `src/nfl_fidos/api.py`, `runbooks/organization-player-development.md`, `tests/test_organization_player_development.py`, `tests/test_organization_player_development_api.py` | Player package, mastery/plan validation, own-record privacy, owner transition, tenancy, and production-gate tests pass; real player records and production coaching UX remain pending |
| Stage 15 organization scouting package | Tenant-scoped opponent profile, situational reports, source-reference linkage, matchup/evolution containers, analyst submission, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-scouting-package.schema.json`, `src/nfl_fidos/organization_scouting.py`, `src/nfl_fidos/scouting_intelligence.py`, `src/nfl_fidos/api.py`, `runbooks/organization-scouting.md`, `tests/test_organization_scouting.py`, `tests/test_organization_scouting_api.py` | Package compiler, source linkage, analyst/owner boundary, tenancy, and production-gate tests pass; live authorized source connectors and real opponent data remain pending |
| Stage 16 organization analytics package | Tenant-scoped metric observations, denominator/uncertainty context, source-linked reports, analyst submission, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-analytics-package.schema.json`, `src/nfl_fidos/organization_analytics.py`, `src/nfl_fidos/analytics_dictionary.py`, `src/nfl_fidos/api.py`, `runbooks/organization-analytics.md`, `tests/test_organization_analytics.py`, `tests/test_organization_analytics_api.py` | Observation/report compiler, lineage checks, role boundary, tenancy, owner transition, and production-gate tests pass; production adapters and empirical calibration remain pending |
| Stage 17 organization weekly game-plan package | Tenant-scoped weekly plan compilation, situational calls, counters, contingencies, ownership, player teaching outputs, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-game-plan-package.schema.json`, `src/nfl_fidos/organization_game_plan.py`, `src/nfl_fidos/game_plan_architecture.py`, `src/nfl_fidos/api.py`, `runbooks/organization-game-plan.md`, `tests/test_organization_game_plan.py`, `tests/test_organization_game_plan_api.py` | Plan compiler, teaching/trigger validation, role boundary, tenancy, owner transition, and production-gate tests pass; live weekly feeds, staff adoption, and rollout remain pending |
| Stage 8 organization special-teams personnel package | Tenant-scoped specialist/unit assignments, responsibilities, mastery evidence, authorized source linkage, program-owner validation, authenticated API, and non-activating flags | `contracts/organization-special-teams.schema.json`, `src/nfl_fidos/organization_special_teams.py`, `src/nfl_fidos/special_teams_bible.py`, `src/nfl_fidos/api.py`, `runbooks/organization-special-teams.md`, `tests/test_organization_special_teams.py`, `tests/test_organization_special_teams_api.py` | Unit-reference validation, evidence/source linkage, role boundary, tenancy, owner transition, and production-gate tests pass; live specialist/team records remain pending |
| Stage 13 organization performance package | Tenant-scoped non-diagnostic performance observations, readiness summaries, qualified-staff review flags, owner validation, authenticated API, and medical/production safeguards | `contracts/organization-performance-package.schema.json`, `src/nfl_fidos/organization_performance.py`, `src/nfl_fidos/performance_ingestion.py`, `src/nfl_fidos/athlete_performance.py`, `src/nfl_fidos/api.py`, `runbooks/organization-performance.md`, `tests/test_organization_performance.py`, `tests/test_organization_performance_api.py` | Medical-field rejection, observation/readiness validation, role boundary, tenancy, owner transition, and non-medical safeguards pass; provider deployment and qualified live staff operations remain pending |
| Stage 14 organization media review package | Tenant-scoped composition of registered media assets, bounded clips, role-scoped playlists, film observations, QA correction status, owner validation, and non-deployment safeguards | `contracts/organization-media-review-package.schema.json`, `src/nfl_fidos/organization_media_review.py`, `src/nfl_fidos/media.py`, `src/nfl_fidos/media_service.py`, `src/nfl_fidos/film_intelligence.py`, `src/nfl_fidos/api.py`, `runbooks/organization-media-review.md`, `tests/test_organization_media_review.py`, `tests/test_organization_media_review_api.py` | Integrity, tenancy, clip/playlist linkage, QA, approval, API, and non-activation tests pass; external storage, worker deployment, and real organization media operations remain pending |
| Stage 12 practice resource planning | Time-window facility/staff availability checks, shared-resource conflict detection, organization scope enforcement, and read-only external-calendar boundary | `src/nfl_fidos/practice_resources.py`, `src/nfl_fidos/resource_integration.py`, `src/nfl_fidos/practice_workspace.py`, `src/nfl_fidos/api.py`, `contracts/practice-resource-schedule.schema.json`, `contracts/resource-integration.schema.json`, `runbooks/practice-resource-planning.md`, `runbooks/practice-resource-integration.md`, `tests/test_practice_resources.py`, `tests/test_resource_integration.py`, `tests/test_practice_api.py` | Resource availability, overlap, tenancy, provider mode, API, and no-mutation tests pass |
| Stage 20 evaluation scenario corpus | 48 synthetic, labeled scenarios across all 12 governance risk domains with expected outcomes, promotion blockers, citations, and human-review boundaries | `governance/evaluation-scenario-corpus.json`, `src/nfl_fidos/evaluation_scenarios.py`, `tests/test_evaluation_scenarios.py` | Corpus coverage and nuanced-outcome review tests pass; empirical/live calibration remains |
| Stages 6–7 scheme lineage validation | Eight source-labeled validation fixtures map one lineage record to every offensive and defensive scheme family; all remain review-required and non-approved | `scheme/team-doctrine-lineage-validation.json`, `src/nfl_fidos/scheme_lineage.py`, `tests/test_scheme_lineage.py` | Lineage coverage and approval-boundary tests pass; real team doctrine remains owner/source dependent |
| Stage 18 rule-source freshness scheduler | Bounded official-NFL allowlist validation, stale-source detection, proposed review work, and explicit no-fetch/no-promote boundary | `src/nfl_fidos/rule_source_scheduler.py`, `scripts/schedule_rule_refresh.py`, `runbooks/rule-source-refresh.md`, `tests/test_rule_source_scheduler.py` | Current and stale-source scheduling tests pass; owner review remains required |
| Stages 18–19 source integration rehearsal | Real loopback HTTP transport, response hashing, freshness state, persisted refresh evidence, redirect allowlist rejection, and response-size bounds | `src/nfl_fidos/source_connectors.py`, `scripts/source_integration_rehearsal.py`, `runbooks/source-integration-rehearsal.md`, `tests/test_source_integration_rehearsal.py` | Synthetic local rehearsal passes; external licensed/official source operations remain gated |
| Authorized source operation boundary | Separate license/decision evidence, organization scope, HTTPS/domain allowlist, explicit fetch permission, and non-network authorization preflight | `src/nfl_fidos/source_authorization.py`, `contracts/source-authorization.schema.json`, `operations/source-authorization-template.json`, `scripts/source_authorization_preflight.py`, `runbooks/source-authorization.md`, `tests/test_source_authorization.py` | Authorization validation passes; live licensed/official source operations remain deployment- and owner-dependent |
| Authorized source registration API | Program-owner-only source registration after authorization validation, authorization evidence attachment, tenancy enforcement, and no-fetch/no-external-state guarantees | `src/nfl_fidos/api.py`, `src/nfl_fidos/source_authorization.py`, `runbooks/source-authorization.md`, `tests/test_authorized_source_api.py` | Authorized registration and rejection paths pass; live source refresh still requires approved external operations |
| Stage 23 deployment preflight | Value-free secret-source inspection, deployment-contract validation, Stage 0 gate check, and non-activating preflight CLI | `src/nfl_fidos/secret_source.py`, `src/nfl_fidos/deployment_preflight.py`, `scripts/deployment_preflight.py`, `contracts/secret-source.schema.json`, `runbooks/deployment-preflight.md`, `tests/test_deployment_preflight.py` | Validation preflight passes; production preflight correctly blocks on external secret source and Stage 0 gate |
| Stage 1/23 composed environment readiness | Composed deployment contract, secret/control gate, database/migration, evaluation, scheduler, and monitoring readiness report with explicit non-activation evidence | `src/nfl_fidos/deployment_environment_readiness.py`, `contracts/deployment-environment-readiness.schema.json`, `scripts/deployment_environment_readiness.py`, `runbooks/deployment-environment-readiness.md`, `control/deployment-environment-readiness-local-evidence.json`, `tests/test_deployment_environment_readiness.py` | Configured local readiness passes with migration version 1, 97/97 evals, scheduler and monitoring checks; unconfigured local and production environments still fail closed |
| Deployment infrastructure contract validation | Dependency-free Dockerfile-to-deployment-contract validation for image family, runtime command, healthcheck, volume, port, media tools, secret-file contract, and environment keys | `src/nfl_fidos/deployment_infrastructure.py`, `scripts/validate_deployment_infrastructure.py`, `runbooks/deployment-infrastructure-validation.md`, `tests/test_deployment_infrastructure.py`, `Dockerfile` | Static infrastructure validation passes; image build and provider deployment remain external deployment-owner actions |
| Deployment runtime rehearsal | Temporary real HTTP-server exercise covering health, control plane, dashboard, evaluations, malformed requests, unknown POSTs, SQLite creation, and database reopen | `scripts/deployment_runtime_rehearsal.py`, `runbooks/deployment-runtime-rehearsal.md`, `tests/test_deployment_runtime_rehearsal.py` | Runtime rehearsal passes with no activation or external state change; container/provider deployment remains pending |
| Stage 23 composed release preflight | Composed release artifacts, deployment contract/secret checks, operational readiness, independent evaluations, and non-activation safety boundary | `src/nfl_fidos/deployment_release_preflight.py`, `scripts/release_preflight.py`, `contracts/deployment-release-preflight.schema.json`, `runbooks/release-preflight.md`, `tests/test_deployment_release_preflight.py` | Composition tests pass; real deployment, external secrets, monitoring registration, and stakeholder rehearsal remain gated |
| Stage 22 dashboard interaction integrity | Added organization-scoped scouting and core play review/approval workspaces, corrected navigation anchors, validated the extended default play fixture and authenticated principal-derived actor path, validated every static JavaScript DOM binding, completed a read-only browser rehearsal, and machine-validated the evidence package | `ui/operator-dashboard.html`, `src/nfl_fidos/api.py`, `src/nfl_fidos/browser_evidence.py`, `scripts/dashboard_smoke.py`, `scripts/validate_browser_evidence.py`, `runbooks/dashboard-smoke.md`, `runbooks/browser-validation.md`, `runbooks/browser-evidence-validation.md`, `control/browser-validation-evidence.json`, `tests/test_operator_ui.py`, `tests/test_core_play_slice.py`, `tests/test_dashboard_smoke.py`, `tests/test_browser_evidence.py` | Local browser validation, evidence integrity, and fail-closed authentication smoke checks pass; deployment-environment usability validation and pilot-user validation remain |
| Stage 22 usability feedback workflow | Role-derived usability feedback submission, screen/task validation, outcome/severity/accessibility review flags, governance inspection, and evidence-linked pilot feedback storage | `src/nfl_fidos/usability_feedback.py`, `src/nfl_fidos/api.py`, `contracts/ux-usability-feedback.schema.json`, `runbooks/usability-feedback.md`, `tests/test_usability_feedback.py`, `tests/test_usability_feedback_api.py` | Feedback workflow passes least-privilege and validation tests; actual pilot-user participation remains pending |
| Stage 21 backup scheduling | Bounded freshness planning, source integrity verification, atomic backup execution, control-gated production boundary, and approval-gated retention execution | `src/nfl_fidos/backup_scheduler.py`, `src/nfl_fidos/media_retention_executor.py`, `scripts/schedule_backup.py`, `runbooks/database-backup-scheduling.md`, `runbooks/media-retention-execution.md`, `tests/test_backup_scheduler.py`, `tests/test_media_retention_executor.py`, `tests/test_media_retention_executor_api.py` | Scheduler and temporary retention execution tests pass; deployment database and production scale validation remain |
| Stage 24 delivery foundation | Wave readiness and release-candidate approval gates | `src/nfl_fidos/delivery.py`, delivery contracts | Wave blockers, eval status, and approval tests pass |
| Stage 24 synthetic pilot rehearsal | Non-live Wave 0 readiness, bounded role coverage, acceptance evidence, rollback preservation, and production-disablement rehearsal | `scripts/pilot_rehearsal.py`, `runbooks/pilot-rehearsal.md`, `tests/test_pilot_rehearsal.py` | Synthetic rehearsal passes; live pilot and real owner approval remain gated |
| Stage 24 pilot organization selection | Owner-controlled selection of an active, approved organization context for a named wave with role coverage and explicit non-live controls | `src/nfl_fidos/pilot_selection.py`, `src/nfl_fidos/api.py`, `contracts/pilot-selection.schema.json`, `ui/operator-dashboard.html`, `runbooks/pilot-organization-selection.md`, `tests/test_pilot_selection_api.py` | Selection validation and tenancy tests pass; real organization and live rollout remain gated |
| Stage 24 pilot delivery package | Composed selection, readiness, feature-flag, and rollback evidence with scope matching and non-live release controls | `src/nfl_fidos/pilot_delivery.py`, `src/nfl_fidos/api.py`, `contracts/pilot-delivery-package.schema.json`, `ui/operator-dashboard.html`, `runbooks/pilot-delivery-package.md`, `tests/test_pilot_delivery_api.py` | Package blocks failed/mismatched evidence and passes bounded composition; live rollout remains gated |
| Stage 0 exit evaluator | Executable structural, dependency, gap-audit, and owner-approval gate | `src/nfl_fidos/stage0.py`, `contracts/stage-0-gate-result.schema.json`, `tests/test_stage0.py` | Current registry is structurally valid and gap-audited; gate remains open pending explicit owner approval |
| Stage 0 owner approval evidence workflow | Authenticated program-owner submission and inspection of registry-linked approval evidence with non-activating safety flags, plus a value-free owner-review packet generator | `src/nfl_fidos/stage0_approval.py`, `src/nfl_fidos/stage0_owner_packet.py`, `scripts/stage0_owner_approval_preflight.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `runbooks/stage-0-owner-approval.md`, `tests/test_stage0_approval_api.py`, `tests/test_stage0_owner_packet.py` | Preflight packet and evidence workflow pass; real program-owner approval and control-plane advancement remain pending |
| Stage 1 system architecture | NFL-scoped component map, information flows, permissions, state, events, feedback loops, and authority boundaries | `architecture/system-architecture.json`, `src/nfl_fidos/architecture.py` | Architecture validator and structural tests pass |
| Stage 5 coach development | Coaching staff architecture, role mastery dimensions, development pathways, observable evaluation, and review boundaries | `src/nfl_fidos/coach_development.py` | Role coverage, measurable pathway, and bounded evaluation tests pass |
| Stages 6–7 scheme bibles | Offensive and defensive family dossiers with compositional fields, personnel fit, teaching cost, counters, counter-counters, adaptation, and nuance | `scheme/scheme-bible.json`, `src/nfl_fidos/scheme_bible.py` | Six controlled family dossiers validate across both units |
| Stage 8 special-teams bible | Kickoff, return, punt, FG/PAT, block, and hands-team units with roles, specialist mastery, situations, rules, practice, and scouting | `special_teams/special-teams-bible.json`, `src/nfl_fidos/special_teams_bible.py` | Six required units validate with global rule-authority controls |
| Stage 9 extended playbook architecture | Play families, extended play metadata, role extraction, dependencies, situational variants, checks, and human approval/publishing | `src/nfl_fidos/playbook_architecture.py`, `contracts/playbook-spec.schema.json` | Extended compiler, role-view, and approval tests pass |
| Stage 9 playbook authoring workspace | Tenant-scoped persisted drafts, compiler validation, role views, approval request, owner lock/publish, authenticated API, and interactive dashboard authoring controls | `src/nfl_fidos/playbook_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `contracts/playbook-authoring.schema.json`, `tests/test_playbook_workspace.py`, `tests/test_playbook_workspace_api.py` | Draft, rejection, role-view, approval lifecycle, tenancy, API, and UI contract tests pass |
| Stage 10 visual playbook foundation | Coordinate model, player/path notation, timeline animation, role views, accessibility, overlays, and human-reviewed what-if scenarios | `visual/notation-standard.json`, `src/nfl_fidos/visual_playbook.py`, `contracts/visual-play.schema.json` | Coordinate, timeline, accessibility, and scenario-isolation tests pass |
| Stage 11 drill library | Drill taxonomy, competency mapping, measurable KPIs, coaching cues, errors/corrections, progressions, film angles, and safety controls | `src/nfl_fidos/drill_library.py` | Linked drill evaluation and safety tests pass |
| Stage 12 practice architecture | Period taxonomy, objective mapping, staff/facility constraints, restrictions, reps, minutes, learning rationale, and load limits | `src/nfl_fidos/practice_architecture.py` | Practice construction and load-boundary tests pass |
| Practice attendance and participation loop | Roster- and practice-linked present/absent/limited/late/excused records, available-minute context, period linkage, aggregate summaries, human-review flags, authenticated role boundaries, and React authoring/inspection | `src/nfl_fidos/practice_attendance.py`, `src/nfl_fidos/api.py`, `frontend/src/pages/PracticePage.tsx`, `frontend/src/lib/api.ts`, `tests/test_practice_attendance.py`, `tests/test_practice_attendance_api.py`, `frontend/src/lib/api.operational.test.ts` | Attendance requires an organization practice and roster player; 576 Python and 86 frontend tests pass; medical/eligibility and production activation remain outside the record |
| Stage 13 performance bible | Performance domains, position demand profiles, bounded support plans, load/recovery context, audit provenance, and professional escalation | `performance/performance-domain-bible.json`, `src/nfl_fidos/performance_bible.py` | Domain coverage, health escalation, and medical-boundary tests pass |
| Stage 13 performance provider boundary | Read-only provider metadata, approved source provenance, bounded batch size, organization scope, non-diagnostic ingestion, and staff escalation | `src/nfl_fidos/performance_integration.py`, `src/nfl_fidos/performance_ingestion.py`, `src/nfl_fidos/api.py`, `contracts/performance-provider-integration.schema.json`, `runbooks/performance-provider-integration.md`, `tests/test_performance_integration.py`, `tests/test_performance_integration_api.py` | Provider, API, provenance, scope, no-medical-action, and no-external-mutation tests pass |
| Stage 14 film intelligence | Clip-traceable observations, tagging domains, confidence/classification, assignment grading, correction workflow, playlists, and QA | `src/nfl_fidos/film_intelligence.py`, `contracts/film-observation.schema.json` | Provenance, low-confidence inference, correction, playlist, and QA tests pass |
| Stage 15 scouting intelligence | Authorized opponent profiles, situational reports, evidence labels, sample/context rules, matchup models, and evolution warnings | `src/nfl_fidos/scouting_intelligence.py`, `contracts/opponent-profile.schema.json` | Authorization, claim-evidence, matchup, and adaptation tests pass |
| Stage 16 analytics dictionary | 12 controlled metric definitions spanning offense, defense, special teams, player, play, drive, and game-plan use cases; formula/denominator model, context dimensions, caveats, validation methods, consumers, uncertainty intervals, lineage, and reports | `analytics/metrics-dictionary.json`, `analytics/nfl-metric-validation-corpus.json`, `src/nfl_fidos/analytics_dictionary.py`, `src/nfl_fidos/analytics_corpus.py`, `contracts/metric-definition.schema.json` | Dictionary, bounded calculation, uncertainty, lineage, report, and corpus coverage tests pass |
| Stage 16 analytics provider boundary | Read-only provider validation, approved source lineage, bounded metric batches, uncertainty-preserving calculations, organization scope, and authenticated persistence | `src/nfl_fidos/analytics_integration.py`, `src/nfl_fidos/api.py`, `contracts/analytics-provider-integration.schema.json`, `runbooks/analytics-provider-integration.md`, `tests/test_analytics_integration.py`, `tests/test_analytics_integration_api.py` | Provider, denominator, lineage, uncertainty, tenancy, API, and no-external-mutation tests pass |
| Stage 17 game-plan architecture | Weekly plan schema, primary calls, situational plans, matchups, contingencies, triggers, counter-counter logic, ownership, and player teaching outputs | `src/nfl_fidos/game_plan_architecture.py`, `contracts/game-plan.schema.json` | Plan completeness, trigger ownership, countermeasure, and human-decision tests pass |
| Stage 17 game-plan collaboration | Organization-scoped evidence-linked review threads, staff comments, explicit decisions, authenticated API, and dashboard controls | `src/nfl_fidos/game_plan_collaboration.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `contracts/game-plan-review-thread.schema.json`, `runbooks/game-plan-collaboration.md`, `tests/test_game_plan_collaboration.py`, `tests/test_game_plan_collaboration_api.py` | Thread scope, evidence, role permissions, resolution, API, and non-publication boundaries pass |
| Stage 18 rules knowledge | Versioned NFL rule model, authoritative source registry, provenance validation, exceptions, situational rule context, and fact/strategy separation | `rules/rules-knowledge-model.json`, `rules/authoritative-source-registry.json`, `src/nfl_fidos/rules_knowledge.py`, `src/nfl_fidos/rule_sources.py`, `contracts/rule-knowledge-entry.schema.json` | Official NFL source registry, rule-model, authority, exception, and recommendation-boundary tests pass; future-version refresh remains |
| Stage 19 research protocol | Governed source registration, ingestion, normalization, citations, freshness/state labels, conflict resolution, and research packets | `knowledge/research-protocol.json`, `src/nfl_fidos/research_protocol.py`, `contracts/knowledge-item.schema.json` | Ingestion, canonical eligibility, citation, tier conflict, and research-packet tests pass |
| Stage 20 governance audit | Eval Bible, risk-domain matrix, failure policy, promotion blockers, audit events, observability evidence, and human approval requirements | `governance/eval-bible.json`, `src/nfl_fidos/governance_audit.py`, `contracts/governance-audit.schema.json` | Governance matrix and promotion-blocking tests pass |
| Stage 21 data architecture | ERD-style entity/relationship map, authoritative collections, identifiers, history, migrations, audit events, and tenancy controls | `data/data-architecture.json`, `src/nfl_fidos/data_architecture.py`, `contracts/data-architecture.schema.json` | Data architecture, relationship, audit, and tenancy tests pass |
| Stage 22 UX architecture | Information architecture, screen inventory, role journeys, interaction states, responsive outputs, accessibility, notifications, permissions-to-UI matrix, responsive design-system pass, and brand asset | `ux/ux-architecture.json`, `src/nfl_fidos/ux_architecture.py`, `contracts/ux-architecture.schema.json`, `ui/operator-dashboard.html`, `ui/assets/nfl-fidos-mark.svg`, `control/ux-ui-audit-evidence.json`, `NFL_FIDOS_TUTORIAL.md`, `tests/test_ux_ui_audit.py` | UX structure, state, permission-surface, accessibility, responsive UI, and local visual audit checks pass; production and pilot usability remain pending |
| Stage 23 engineering architecture | Repo map, runtime boundaries, API/agent/data contracts, testing, observability, monitoring contract, incident rehearsal, CI/CD, environments, migrations, flags, runbooks, and security | `engineering/engineering-architecture.json`, `monitoring/observability-contract.json`, `src/nfl_fidos/engineering_architecture.py`, `src/nfl_fidos/monitoring_contract.py`, `scripts/incident_rehearsal.py`, `runbooks/incident-rehearsal.md`, `tests/test_incident_rehearsal.py`, `control/incident-rehearsal-evidence.json`, `scripts/operational_rehearsal.py`, `contracts/engineering-architecture.schema.json` | Temporary failure/recovery rehearsal exports two events with zero failures and validates rollback; provider monitoring registration and production stakeholder rehearsal remain pending |
| Stage 24 MVP strategy | Vertical-slice waves, pilot users, priority/risk matrix, acceptance criteria, feature flags, pilot-readiness gate, rollout, rollback, and independent eval checkpoints | `delivery/mvp-strategy.json`, `delivery/pilot-readiness-template.json`, `src/nfl_fidos/mvp_strategy.py`, `src/nfl_fidos/pilot_readiness.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `contracts/mvp-strategy.schema.json`, `tests/test_pilot_readiness.py`, `tests/test_pilot_readiness_api.py` | MVP sequence, authenticated pilot-readiness evaluation, role coverage, wave blocking, approval, flag, rollback, and dependency tests pass; live pilot evidence remains |
| Stage 25 Master Codex specification | Compiled scope, locked principles, upstream artifacts, stage sequence, contracts, permissions, quality commands, coding standards, change control, acceptance, and traceability | `control/master-codex-build-spec.json`, `src/nfl_fidos/master_spec.py`, `contracts/master-codex-build-spec.schema.json` | Master spec covers all 26 stages and validates required implementation controls |
| Stage 25 specification acceptance evidence | Program-owner-only acceptance record, compiled-spec validation, evidence references, inspection API, non-activating safety flags, and a value-free owner-review packet generator | `src/nfl_fidos/master_spec_acceptance.py`, `src/nfl_fidos/stage25_acceptance_packet.py`, `scripts/stage25_acceptance_preflight.py`, `src/nfl_fidos/api.py`, `contracts/stage-25-spec-acceptance.schema.json`, `runbooks/stage-25-spec-acceptance.md`, `tests/test_master_spec_acceptance.py`, `tests/test_stage25_spec_acceptance_api.py`, `tests/test_stage25_acceptance_packet.py` | Preflight packet, workflow, and API tests pass; real program-owner acceptance remains pending |
| Deployment provider adapter boundary | Provider-neutral adapter metadata, approved read-only capabilities, non-secret credential references, healthcheck evidence, owner validation, authenticated API, and non-external safeguards | `contracts/provider-adapter-registration.schema.json`, `src/nfl_fidos/provider_adapter_registration.py`, `src/nfl_fidos/api.py`, `runbooks/provider-adapter-registration.md`, `tests/test_provider_adapter_registration.py`, `tests/test_provider_adapter_api.py` | Invalid modes/credentials/capabilities reject; analyst submission, owner validation, tenancy, API, and no-provider/no-external-state tests pass; provider-specific deployment remains pending |
| Wave 1 core vertical slice | Source-linked play review, role-specific teaching view, measurable drill, persisted approval, and audit history | `src/nfl_fidos/service.py`, `src/nfl_fidos/api.py`, `tests/test_core_play_slice.py` | 204 regression tests and EVAL-FAM-043 pass |
| Wave 2 evidence intelligence slice | Authorized film asset/clip, contextual observation, scouting report, metric lineage, QA, and review package | `src/nfl_fidos/service.py`, `tests/test_evidence_intelligence_slice.py` | 174 regression tests and EVAL-FAM-044 pass |
| Wave 3 weekly delivery slice | Weekly plan, rule/fact separation, governance audit, feature gates, and release-candidate readiness | `src/nfl_fidos/service.py`, `tests/test_weekly_delivery_slice.py` | 176 regression tests and EVAL-FAM-045 pass |
| Security and tenancy slice | Signed principals, role permissions, organization scope enforcement, and authenticated workflow API routes | `src/nfl_fidos/auth.py`, `src/nfl_fidos/api.py`, `tests/test_auth_tenancy.py` | 179 regression tests and EVAL-FAM-046 pass |
| Tenant repository slice | Organization-key enforcement, filtered reads, and scoped audit history for JSON and SQLite repositories | `src/nfl_fidos/tenant_repository.py`, `tests/test_tenant_repository.py` | 181 regression tests and EVAL-FAM-047 pass |
| Operator UX slice | Accessible dashboard for control state, eval health, governance visibility, and approval boundaries | `ui/operator-dashboard.html`, `src/nfl_fidos/http_server.py`, `tests/test_operator_ui.py` | 182 regression tests and EVAL-FAM-048 pass |
| Media ingestion slice | Authorized local media catalog, format/root checks, tenant scope, and SHA-256 integrity metadata | `src/nfl_fidos/media_ingestion.py`, `tests/test_media_observability.py` | 185 regression tests and EVAL-FAM-049 pass |
| Observability slice | Structured operation events, request identity, organization scope, latency, and failure evidence | `src/nfl_fidos/observability.py`, `tests/test_media_observability.py` | 185 regression tests and EVAL-FAM-050 pass |
| Migration slice | SQLite schema versioning, dry-run, snapshot, rollback, organization metadata, and history preservation | `src/nfl_fidos/migrations.py`, `scripts/migrate_sqlite.py`, `tests/test_migrations.py` | 187 regression tests and EVAL-FAM-051 pass |
| Film room slice | Organization-scoped search, annotation sessions, correction flags, source-linked quiz mode, and review state | `src/nfl_fidos/film_room.py`, `tests/test_film_room.py` | 190 regression tests and EVAL-FAM-052 pass |
| Deployment/runtime slice | Reproducible package metadata, environment validation, configured SQLite service entrypoint, and container contract | `pyproject.toml`, `src/nfl_fidos/config.py`, `src/nfl_fidos/server.py`, `Dockerfile`, `tests/test_config_runtime.py` | 193 regression tests and EVAL-FAM-053 pass |
| Ontology depth slice | Expanded NFL positions, personnel, formations, concepts, coverages, fronts, pressures, special teams, and situations | `ontology/football-terms.json`, `tests/test_ontology_context.py` | 55 eval families pass; canonical aliases remain unambiguous |
| Stage 3 agent organization bible | Structured mission boundaries, inputs/outputs, collaborators, authority, escalation, handoffs, prompts, and agent eval requirements | `agents/agent-organization-bible.json`, `src/nfl_fidos/agent_bible.py`, `tests/test_agent_bible.py` | 194 regression tests and EVAL-FAM-055 pass |
| Stage 4 player development bible | Position-family competency trees, evidence/assessment methods, mastery levels, IDP requirements, learning paths, quizzes, and safety controls | `development/player-development-bible.json`, `src/nfl_fidos/player_development_bible.py`, `tests/test_player_development_bible.py` | 195 regression tests and EVAL-FAM-056 pass |
| Stage 5 coaching staff bible | Staff role mastery dimensions, development pathway, observable evaluation, collaboration interfaces, and professional boundaries | `staff/coaching-staff-bible.json`, `src/nfl_fidos/staff_bible.py`, `tests/test_staff_bible.py` | 196 regression tests and EVAL-FAM-057 pass |
| Stages 6–7 scheme architecture | Offensive/defensive taxonomies, concept graphs, scheme fit criteria, installation requirements, and trigger-based counter/counter-counter libraries | `scheme/scheme-architecture.json`, `src/nfl_fidos/scheme_architecture.py`, `tests/test_scheme_architecture.py` | 197 regression tests and EVAL-FAM-058 pass |
| Stage 10 visual rendering | Accessible deterministic SVG role views with player labels, assignment paths, canonical/what-if separation, and review semantics | `src/nfl_fidos/visual_render.py`, `tests/test_visual_render.py` | 199 regression tests and EVAL-FAM-059 pass |
| Stage 19 knowledge graph | Organization-scoped nodes and edges with provenance, classification, context, confidence, conflict review, and canonical eligibility | `src/nfl_fidos/knowledge_graph.py`, `tests/test_knowledge_graph.py` | 201 regression tests and EVAL-FAM-060 pass |
| Film-room persistence slice | Repository-backed organization-scoped observation search and quiz-attempt persistence across service recreation | `src/nfl_fidos/film_room_service.py`, `tests/test_film_room_service.py` | 203 regression tests and EVAL-FAM-061 pass |
| Requirements traceability ledger | Machine-readable coverage of STAGE-0 through STAGE-25 with explicit evidence and remaining work, including repository reference validation | `control/requirements-traceability.json`, `src/nfl_fidos/traceability.py`, `scripts/validate_traceability.py`, `runbooks/traceability-validation.md`, `tests/test_traceability.py` | 479 evidence references resolve; traceability validator and EVAL-FAM-062 pass |
| Project audit checkpoint | Composed source-plan audit, traceability, evaluations, Stage 0 control state, and explicit remaining external blockers without claiming completion | `src/nfl_fidos/project_audit.py`, `scripts/project_audit.py`, `runbooks/project-audit.md`, `tests/test_project_audit.py` | Checkpoint reports foundation_verified with completion_claimed=false and preserves all remaining stage work |
| External action handoff | Value-free grouping of every remaining Master Plan requirement by accountable authority, required inputs, and non-activating safety state | `src/nfl_fidos/external_handoff.py`, `scripts/external_action_handoff.py`, `runbooks/external-action-handoff.md`, `tests/test_external_handoff.py` | Handoff covers all remaining ledger actions while production, stage advancement, and external state remain disabled |
| Film-room API slice | Authenticated organization-scoped observation search, quiz creation, and attempt submission | `src/nfl_fidos/api.py`, `tests/test_film_room_api.py` | 207 regression tests and EVAL-FAM-063 pass |
| Media catalog API slice | Authorized file cataloging, SHA-256 integrity metadata, bounded clip creation, and scoped listing | `src/nfl_fidos/media_service.py`, `src/nfl_fidos/api.py`, `tests/test_media_service.py`, `tests/test_media_api.py` | 211 regression tests and EVAL-FAM-064 pass |
| Media processing jobs | Durable queued/running/retryable/completed/failed media worker lifecycle with scoped API transitions | `src/nfl_fidos/media_jobs.py`, `src/nfl_fidos/api.py`, `tests/test_media_jobs.py`, `runbooks/media-ingestion.md` | 213 regression tests and EVAL-FAM-065 pass |
| Authorized media pipeline smoke | Temporary authorized ingest, managed storage, bounded probe worker, persisted output evidence, and cross-tenant isolation | `scripts/media_pipeline_smoke.py`, `runbooks/media-worker.md`, `tests/test_media_pipeline_smoke.py` | End-to-end media pipeline rehearsal passes without production media or credentials |
| Database operations | Verified SQLite backup, restore, integrity checks, and non-destructive retention planning | `src/nfl_fidos/database_operations.py`, `scripts/backup_sqlite.py`, `tests/test_database_operations.py`, `runbooks/database-backup.md` | Database operations regression test passes |
| Authorized source connectors | HTTPS allowlist registration, freshness visibility, refresh hashing, and failure evidence | `src/nfl_fidos/source_connectors.py`, `src/nfl_fidos/api.py`, `tests/test_source_connectors.py`, `tests/test_source_api.py` | 217 regression tests and EVAL-FAM-066 pass |
| Role-aware operator summary | Organization-scoped workspace counts, pending-review state, media jobs, stale sources, and role-limited sections | `src/nfl_fidos/operator_summary.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_operator_summary.py` | 217 regression tests and EVAL-FAM-067 pass |
| Approval inbox | Governance-role approval visibility with evidence refs, blockers, organization scope, and approval boundaries | `src/nfl_fidos/approval_inbox.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_approval_inbox.py` | 218 regression tests and EVAL-FAM-068 pass |
| Player Today workspace | Coach-created assignments and privacy-scoped player lessons, mastery, development plans, and quiz evidence | `src/nfl_fidos/player_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_player_workspace.py`, `tests/test_player_api.py` | 220 regression tests and EVAL-FAM-069 pass |
| Game-plan workspace | Organization-scoped staff review of plans, scouting, metrics, rules, delivery, releases, and blockers | `src/nfl_fidos/game_plan_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_game_plan_workspace.py`, `tests/test_game_plan_api.py` | 222 regression tests and EVAL-FAM-070 pass |
| Practice builder workspace | Coach-authored practice plans with objective mapping, periods, reps, load controls, and scoped review state | `src/nfl_fidos/practice_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_practice_workspace.py`, `tests/test_practice_api.py` | 224 regression tests and EVAL-FAM-071 pass |
| Scheme workspace | Organization-scoped compositional scheme save/review, unit filtering, and role boundary | `src/nfl_fidos/scheme_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_scheme_workspace.py`, `tests/test_scheme_api.py` | 226 regression tests and EVAL-FAM-072 pass |
| Analytics workspace | Analyst metric reports with denominator, lineage, uncertainty, situation filtering, and review state | `src/nfl_fidos/analytics_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_analytics_workspace.py`, `tests/test_analytics_api.py` | 228 regression tests and EVAL-FAM-073 pass |
| Scouting workspace | Opponent scouting reports, sample-size warnings, adaptation warnings, and role-scoped review surface | `src/nfl_fidos/scouting_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_scouting_workspace.py`, `tests/test_scouting_api.py` | 230 regression tests and EVAL-FAM-074 pass |
| Agent runtime | Active-only specialist dispatch, adapter boundary, auditable handoff, tenant-scoped run persistence, and safe missing-adapter state | `src/nfl_fidos/agent_runtime.py`, `tests/test_agent_runtime.py` | 233 regression tests and EVAL-FAM-075 pass |
| Operational readiness | Non-destructive runtime, database integrity, migration, control-plane, evaluation, and production-secret blocker checks | `src/nfl_fidos/operational_readiness.py`, `scripts/readiness_check.py`, `tests/test_operational_readiness.py` | 236 regression tests and EVAL-FAM-076 pass |
| Visual playbook workspace | Tenant-scoped visual play persistence, authenticated role retrieval, accessible deterministic SVG, and privacy boundary | `src/nfl_fidos/visual_workspace.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_visual_workspace.py` | 239 regression tests and EVAL-FAM-077 pass |
| Film annotation workflow | Persisted annotation sessions, source-linked observations, low-confidence correction state, and scoped API/UI | `src/nfl_fidos/film_room_service.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_film_room_api.py` | 240 regression tests and EVAL-FAM-079 pass |
| Film search index | SQLite FTS5 persistence with organization scope, context filters, and safe JSON fallback | `src/nfl_fidos/film_search.py`, `src/nfl_fidos/film_room_service.py`, `tests/test_film_search.py` | 242 regression tests and EVAL-FAM-080 pass |
| Film search scale rehearsal | Bounded two-tenant synthetic FTS indexing/search, persistence-after-reopen, filtered counts, and cross-tenant isolation evidence | `scripts/film_search_scale_rehearsal.py`, `runbooks/film-search-scale-rehearsal.md`, `tests/test_film_search_scale_rehearsal.py` | Temporary search rehearsal passes with no external state change; production search infrastructure capacity and deployment remain pending |
| HTTP runtime adapter | Testable configured server factory, structured JSON responses, body-size validation, malformed-request handling, and HTTP smoke coverage | `src/nfl_fidos/http_server.py`, `tests/test_http_server.py` | 244 regression tests and EVAL-FAM-081 pass |
| Media probe worker | Authorized path-bounded ffprobe worker, durable output evidence, unsupported-operation lifecycle, and metadata-only fallback | `src/nfl_fidos/media_worker.py`, `src/nfl_fidos/media_jobs.py`, `tests/test_media_worker.py` | 247 regression tests and EVAL-FAM-082 pass |
| Media worker runner | Bounded queued/retryable job claims, approved-root enforcement, probe/transform execution, persisted batch reports, authenticated owner control, and failure review state | `src/nfl_fidos/media_worker_runner.py`, `src/nfl_fidos/api.py`, `scripts/media_worker_runner.py`, `runbooks/media-worker-runner.md`, `tests/test_media_worker_runner.py` | Runner, root boundary, job lifecycle, API authorization, batch report, and no-external-mutation tests pass |
| Media content streaming | Authenticated organization-scoped full/partial byte delivery, invalid-range rejection, and threaded SQLite safety | `src/nfl_fidos/http_server.py`, `src/nfl_fidos/sqlite_repository.py`, `tests/test_media_stream.py` | 249 regression tests and EVAL-FAM-083 pass |
| Media transform lifecycle | Bounded ffmpeg command planning for transcode/segment/thumbnail, approved output roots, no-overwrite policy, and worker integration | `src/nfl_fidos/media_transform.py`, `src/nfl_fidos/media_worker.py`, `tests/test_media_transform.py` | 252 regression tests and EVAL-FAM-084 pass |
| Managed media storage | Atomic organization/asset-scoped copy, source provenance, digest evidence, no-overwrite policy, and non-destructive retention boundary | `src/nfl_fidos/media_storage.py`, `src/nfl_fidos/media_service.py`, `tests/test_media_storage.py` | 254 regression tests and EVAL-FAM-085 pass |
| Media retention planner | Owner-scoped dry-run retention review, expired/unknown classification, and explicit no-delete guarantee | `src/nfl_fidos/media_retention.py`, `src/nfl_fidos/api.py`, `tests/test_media_retention.py`, `tests/test_media_retention_api.py` | 257 regression tests and EVAL-FAM-086 pass |
| Source refresh batch | Bounded stale-only refresh orchestration with per-source failure evidence and aggregate partial-failure state | `src/nfl_fidos/source_connectors.py`, `src/nfl_fidos/api.py`, `tests/test_source_connectors.py` | 260 regression tests and EVAL-FAM-087 pass |
| Source refresh scheduler | Freshness-window due planning, hard bounds, persisted schedule reports, and explicit non-destructive behavior | `src/nfl_fidos/source_scheduler.py`, `src/nfl_fidos/api.py`, `tests/test_source_scheduler.py`, `EVAL-FAM-088` | 260 regression tests and EVAL-FAM-088 pass |
| Persisted film playlists | Organization-scoped clip playlist persistence, clip-reference validation, role-filtered reads, and dashboard creation surface | `contracts/film-playlist.schema.json`, `src/nfl_fidos/film_room_service.py`, `src/nfl_fidos/api.py`, `ui/operator-dashboard.html`, `tests/test_film_playlist_api.py`, `EVAL-FAM-089` | 262 regression tests and EVAL-FAM-089 pass |
| Media retention scheduler | Owner-scoped persisted retention scans with explicit review requirements and no deletion side effects | `src/nfl_fidos/media_retention_scheduler.py`, `src/nfl_fidos/api.py`, `tests/test_media_retention_scheduler.py`, `EVAL-FAM-090` | 264 regression tests and EVAL-FAM-090 pass |
| Managed media retention executor | Explicit owner-approved, dry-run-by-default execution boundary; managed-root containment, production Stage 0 gate, and auditable asset tombstones | `src/nfl_fidos/media_retention_executor.py`, `src/nfl_fidos/api.py`, `runbooks/media-retention-execution.md`, `tests/test_media_retention_executor.py`, `tests/test_media_retention_executor_api.py` | Validation execution and API gate tests pass; no production execution performed |
| Media transform orchestrator | Bounded queued transform execution, worker lifecycle reuse, persisted batch evidence, and safe failure boundaries | `src/nfl_fidos/media_transform_orchestrator.py`, `src/nfl_fidos/media_worker.py`, `src/nfl_fidos/api.py`, `tests/test_media_transform_orchestrator.py`, `EVAL-FAM-091` | 267 regression tests and EVAL-FAM-091 pass |
| Production media-tool readiness | Configurable ffmpeg/ffprobe binaries, production dependency checks, Docker provisioning, and container healthcheck | `src/nfl_fidos/config.py`, `src/nfl_fidos/operational_readiness.py`, `Dockerfile`, `tests/test_operational_readiness.py`, `EVAL-FAM-076` | Media tooling is an explicit readiness blocker when absent |
| Production secret and observability boundary | Mounted secret-file authentication, structured event sink export, bounded sink failures, readiness sink checks, and temporary monitoring registration rehearsal | `src/nfl_fidos/config.py`, `src/nfl_fidos/observability.py`, `src/nfl_fidos/observability_sink.py`, `src/nfl_fidos/monitoring_registration.py`, `src/nfl_fidos/api.py`, `src/nfl_fidos/http_server.py`, `scripts/monitoring_registration_rehearsal.py`, `runbooks/monitoring-registration.md`, `tests/test_observability_sink.py`, `tests/test_monitoring_registration_rehearsal.py` | Structured sink and alert coverage, production registration metadata, fail-closed missing reference, and no-external-registration rehearsal pass |
| Secret-manager mount adapter | Provider metadata, mounted version reference, value-free readiness evidence, fail-closed resolution, production length checks, preflight command, and temporary mount rehearsal | `src/nfl_fidos/secret_manager.py`, `src/nfl_fidos/secret_source.py`, `src/nfl_fidos/config.py`, `scripts/secret_source_preflight.py`, `scripts/secret_manager_mount_rehearsal.py`, `runbooks/secret-manager.md`, `tests/test_secret_manager.py`, `tests/test_secret_manager_mount_rehearsal.py` | Approved mount, missing metadata, unreadable mount, resolution, and value-redaction rehearsal tests pass; real provider deployment remains pending |
| Monitoring registration boundary | Provider-neutral sink validation, deployment registration evidence, alert-contract coverage, sink-parent health, non-activating preflight, and explicit external-registration boundary | `src/nfl_fidos/monitoring_registration.py`, `src/nfl_fidos/monitoring_contract.py`, `scripts/monitoring_registration_preflight.py`, `runbooks/monitoring-registration.md`, `tests/test_monitoring_registration.py` | Validation readiness, production fail-closed behavior, alert coverage, and no-external-state-change tests pass |
| Authorized HTTPS source fetcher | Registered-domain validation before fetch, bounded response size, timeout, redirect allowlist enforcement, and final-URI provenance | `src/nfl_fidos/source_connectors.py`, `tests/test_source_connectors.py`, `EVAL-FAM-092` | Redirect safety evaluation passes |
| Knowledge retrieval index | Organization-scoped SQLite FTS5 index with safe fallback, bounded search, classification/state filters, and provenance-preserving records | `src/nfl_fidos/knowledge_search.py`, `src/nfl_fidos/api.py`, `tests/test_knowledge_search.py`, `EVAL-FAM-093` | SQLite and JSON retrieval tests pass |
| External scheduler contract | Bounded dry-run planning, explicit execution flag, multi-operation orchestration, JSON evidence, and production Stage 0 gate enforcement | `src/nfl_fidos/scheduled_operations.py`, `scripts/scheduled_operations.py`, `runbooks/scheduled-operations.md`, `tests/test_scheduled_operations.py`, `EVAL-FAM-094` | Scheduler safety evaluation passes |
| Scheduler registration boundary | Provider-neutral registration contract, bounded job entrypoints, production reference requirement, dry-run default, and non-activating preflight | `operations/scheduler-registration.json`, `contracts/scheduler-registration.schema.json`, `src/nfl_fidos/scheduler_registration.py`, `scripts/scheduler_registration_preflight.py`, `runbooks/scheduler-registration.md`, `tests/test_scheduler_registration.py` | Validation preflight is ready; provider-specific registration remains deployment-owner work |
| Release artifact validator | Non-deploying required-artifact, evaluation, control-manifest, and human-approval gate validation | `src/nfl_fidos/release_validation.py`, `scripts/validate_release.py`, `runbooks/release-validation.md`, `tests/test_release_validation.py`, `EVAL-FAM-095` | Artifacts complete; release correctly blocked pending Stage 0 approval |
| Deployment topology contract | Design-only API, worker, scheduler, storage, secret, health, rollback, and non-activation controls | `deployment/nfl-fidos-deployment.json`, `contracts/deployment-contract.schema.json`, `src/nfl_fidos/deployment_contract.py`, `scripts/validate_deployment_contract.py`, `.github/workflows/ci.yml`, `tests/test_deployment_contract.py`, `EVAL-FAM-096` | Deployment contract and CI validator pass; contract remains non-activating |
| Visual playback surface | Accessible canonical timeline seek/play controls and explicit isolated what-if review details | `ui/operator-dashboard.html`, `tests/test_operator_ui.py`, `scripts/dashboard_smoke.py`, `runbooks/dashboard-smoke.md`, `runbooks/browser-validation.md`, `control/browser-validation-evidence.json` | Browser QA passed for the local reference service; deployment-environment validation remains pending |
| Media operator workspace | Organization-scoped authorized asset registration, bounded job submission, and media-job status inspection | `ui/operator-dashboard.html`, `tests/test_operator_ui.py`, `src/nfl_fidos/api.py` | Local browser QA confirms rendered controls, operational status, eval status, and invalid-token boundary; deployment-environment usability validation remains pending |
| Part XVI completion gates | Executable Definition-of-Done, blockers, and acceptance approval | `src/nfl_fidos/completion.py`, `contracts/feature-completion.schema.json` | Completion, blocker, and approval tests pass |
| Stage 3 agent lifecycle | Callable registry, activation, deactivation, and capability resolution | `src/nfl_fidos/agent_registry.py`, `contracts/agent-record.schema.json` | Agent lifecycle and capability tests pass |
| Part XIII/XVII governance | Decision ledger, change requests, impact analysis, and approvals | `src/nfl_fidos/change_control.py`, change/decision contracts | Governance state and approval-link tests pass |
| Stages 22–23 API foundation | Pure JSON router and stdlib HTTP adapter | `src/nfl_fidos/api.py`, `src/nfl_fidos/http_server.py`, `NFL_FIDOS_API.md` | API route, method, and error-contract tests pass |
| Stage 1 organization context | NFL organization, season, roster, staff, and terminology context | `src/nfl_fidos/organization.py`, `contracts/organization-context.schema.json` | NFL-scope, role, source, and person-resolution tests pass |
| Stage 13 athlete performance | Workload/quality observations and non-diagnostic readiness summaries | `src/nfl_fidos/athlete_performance.py`, performance contracts | Bounds, sparse-data, and safety escalation tests pass |
| Stage 8 special teams | Explicit unit, phase, operation, role, and situation plan | `src/nfl_fidos/special_teams.py`, `contracts/special-teams-plan.schema.json` | Special-teams validation tests pass |
| Stage 18 game management foundation | Context-complete situations and human-reviewed decision options | `src/nfl_fidos/game_management.py`, game situation/decision contracts | Situation bounds and decision review tests pass |
| Stage 19 knowledge foundation | Source hierarchy and provenance-aware knowledge claims | `src/nfl_fidos/knowledge.py`, `contracts/knowledge-claim.schema.json` | Source-tier, classification, uncertainty, and high-impact claim tests pass |
| Part VII workflows | Player development, weekly team, and scheme-selection orchestration | `src/nfl_fidos/workflows.py`, `contracts/workflow-result.schema.json` | Workflow composition and blocking-path tests pass |
| Part VI mastery framework | Player mastery records, IDPs, and coach mastery dimensions | `src/nfl_fidos/development.py`, mastery/development contracts | Progression, evidence, measured-objective, and review tests pass |
| Stage 14 media foundation | Film asset registration, bounded clips, and tag references | `src/nfl_fidos/media.py`, film asset/clip contracts | Media provenance and range tests pass |
| Stages 22–23 delivery foundation | Operator CLI for validation, evals, ontology, and play compilation | `src/nfl_fidos/cli.py`, `NFL_FIDOS_CLI.md` | JSON CLI smoke tests pass; 193 regression tests pass |
| Stage 21 database foundation | SQLite canonical-record adapter, tenancy, audit history, verified backup/restore, logical SHA-256 fingerprints, and collision-safe operations | `src/nfl_fidos/sqlite_repository.py`, `src/nfl_fidos/tenant_repository.py`, `src/nfl_fidos/database_operations.py`, `scripts/validate_database_operations.py`, `scripts/operational_rehearsal.py`, `runbooks/database-backup.md`, `runbooks/operational-rehearsal.md` | Temporary migration, backup/restore, readiness, and tenancy rehearsal passes; deployment scheduling and scale validation remain |
| Stage 20 security foundation | Role/resource authorization and locked-artifact approval | `src/nfl_fidos/access.py`, `contracts/access-decision.schema.json` | Access and approval boundary tests pass |

## Current verification command

```text
set PYTHONPATH=src
npm ci --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
python -m unittest discover -s tests
python scripts/validate_control_plane.py
python scripts/run_evals.py
python scripts/pilot_rehearsal.py --skip-evals
python scripts/validate_browser_evidence.py
python scripts/validate_deployment_contract.py
```

Latest local verification: 650 regression tests and 90 frontend tests passed, the React production bundle compiled, 97/97 eval families passed, the control plane and master-plan traceability audit validated, and the enforced generated CSS budget passed at 92.12 kB. Today, Playbook, the full-screen Play Designer, and the new Inbox, Roster, Analytics, Delivery, Collaboration, Film, Practice, Scouting, Game Plan, Player, Admin, Reviews, and Stage 25 acceptance workspaces were exercised through route and asset verification. Verification includes organization collaboration SSE replay with player visibility filtering, shared Play Designer cursor overlays, encrypted collaboration offline outbox and thread/reply idempotency, revision-aware remote edit handoff with field-level three-way merge, approved Film server-path asset registration with source-root validation, file hashing, provenance, and Film-authoring authorization, authenticated Film `index` jobs with searchable stream metadata, collaboration thread/reply/assignment/resolution and tenant-scope API coverage, authenticated Play Designer SSE wiring, frame-linked Film tracking and bounded voice-note API coverage, Play Designer visual diff/guarded merge, multi-play export, role-filtered teaching/player view request coverage, encrypted offline draft recovery, encrypted player-learning cache recovery, Practice roster/Playbook/drill catalog linkage, release dependency manifests, release snapshot approval/rollback, delivery task scheduling/completion, roster privacy filtering, report lineage, server-backed tendency exploration with dimension filters, sample/confidence context, source evidence, contradiction gates, and game-plan review handoff, player offline approved-content caching, and Stage 25 specification inspection plus owner-only acceptance contract coverage. These are local, non-activating checks; they do not substitute for owner approval, real organization data, provider deployment, a full cross-browser/accessibility matrix, or moderated pilot evidence.

Implementation addendum (2026-08-25): the collaboration hub is now a dedicated React route at `/app/collaboration` with API-backed threads, replies, assignments, notifications, activity, and presence. Play Designer now consumes the authenticated bounded SSE event stream with reconnecting status and event-driven invalidation, in addition to its short-poll fallback; active staff cursor positions render as accessible shared-field overlays, and thread/reply mutations persist in an encrypted organization-scoped outbox for reconnect delivery. Thread and reply identifiers are idempotent on the server so dropped responses do not duplicate those records. Film `/app/film` now exposes voice-note records and frame-linked player tracking from the Film Intelligence Studio. Play Designer Review now exposes server-backed visual snapshot comparison plus guarded branch merge with element-level conflict reporting, and its export dialog can compose multi-play PDF/HTML/JSON/CSV packets while correctly restricting SVG/PNG to one design. Practice now connects roster and Playbook catalogs to period assignments. Game Plan Release Room snapshots now hash a dependency manifest for linked plays, film, scouting, practice, roster, analytics, delivery, and source references; unresolved references remain visible as `needs_review`. Open collaboration threads are also promoted into the Unified Operations Inbox as accountable review work. These additions remain subject to managed media storage, moderated pilot, provider deployment, and Stage 0 owner-approval gates.

The project intentionally remains in `STAGE-0 / STAGE-0A` until the capability registry is exhaustive, gaps and redundancies are reviewed, and the owner approves the Stage 0 exit gate. The Play Designer implementation is feature-complete for the locally testable scope; the overall program is not production-authorized and still requires the external and human gates listed below.

## Latest verification addendum

The export pipeline now has explicit layout metadata and verified multi-item composition for paginated call-sheet tables, two-column wristbands, and 2x2/3x2 play-card PDF/HTML grids; SVG/PNG remain correctly restricted to single-design output.

The latest local evidence now includes organization-wide collaboration SSE replay with player visibility filtering, shared Play Designer cursor overlays, encrypted Play Designer collaboration outbox with reconnect delivery and idempotent thread/reply writes, revision-aware remote edit handoff with field-level three-way merging for disjoint edits and explicit conflict review for overlapping edits, encrypted Play Designer and Player Learning Hub offline caches, role-filtered Play Designer teaching views, catalog-backed Practice period position-group selectors connected to roster and drill records, approved Film asset registration with source-root and provenance controls, Film `index` jobs that persist bounded searchable stream metadata, Film Studio evidence marks linked directly to canonical Playbook calls, the Scouting Tendency Explorer with explicit trend/contradiction/source handling and collaboration review handoff, Game Plan Release Room frozen source-plan field comparison, Delivery Center five-audience packet readiness, blocker reporting, reviewable packet assembly, and Operations Inbox delivery-packet routing, the Admin route's persisted pilot selection/package/usability record inspection, the dedicated Stage 25 acceptance route and API contract, server-read release-bundle manifest integrity inspection in Play Designer history, 252/252 frontend tests, 643/643 Python tests, and a passing production build. The external and human-gated items below remain intentionally open.

Player authoring parity addendum (2026-08-25): staff assignment creation now resolves targets from the organization-scoped roster and suggests approved Playbook, Film, and Practice artifacts by assignment type, while preserving manual IDs for approved records outside the catalog. Player-role reads remain disabled for the staff-only catalogs.

Roster authoring parity addendum (2026-08-25): Depth Chart and Personnel Package creation now provide organization-scoped roster multi-selects with availability, position, and role context, preserve selected order for starter-to-reserve slots, and retain manual ID entry for approved imports.

Analytics authoring parity addendum (2026-08-25): Outcome Report creation now provides a source-linked multi-select of organization metric observations with visible rate/sample context, while preserving the existing manual observation-ID path and the uncertainty/lineage guardrails.

Delivery authoring parity addendum (2026-08-25): game-week responsibilities and packet records now suggest organization release snapshots, practice plans, and packet artifacts as linked records, while preserving manual references and the existing governed delivery API.

Scouting authoring parity addendum (2026-08-25): situation report creation now suggests organization Film observations and clips as evidence references, while preserving manual source refs and the existing sample-size, confidence, contradiction, and human-review gates.

Release authoring parity addendum (2026-08-25): immutable Game Plan snapshot creation now suggests source-linked scouting, analytics, rule, delivery, and release-candidate artifacts, while preserving manual references and the existing dependency hash, approval, rollback, and diff controls.

Admin parity addendum (2026-08-25): the React Admin governance route now exposes non-activating pilot readiness evaluation, approved pilot organization selection, pilot delivery-package composition, and role-scoped usability/accessibility evidence submission through the canonical Python API. It also loads and inspects persisted selections, packages, and UX evidence alongside readiness reports, with explicit non-activation boundaries. Authenticated browser verification against an isolated local reference service confirmed organization context rendering, all four pilot governance record classes, form controls, safety notices, and zero browser console errors; local deployment-environment readiness also passed with synthetic local secret and observability configuration while preserving production-disabled controls.

Stage 25 React governance addendum (2026-08-25): `/app/admin/stage-25` is now a dedicated compiled-specification review and acceptance-evidence workspace. It loads the organization-scoped specification and prior acceptance records, displays validation status and safety flags, exposes the program-owner-only acceptance form, and keeps production implementation and automatic stage advancement disabled. The route and API contract are covered by the 82-test frontend suite; the actual owner decision remains pending.

Current verification correction (2026-08-25): the frontend suite now passes 84/84 tests after adding the organization population-readiness route and API contract; Python remains 566/566 and the production build passes.

Current verification correction (2026-08-25): the frontend suite now passes 85/85 tests and the Python suite passes 571/571 tests after adding roster-linked Practice Attendance; the production build and static asset/deep-link check pass.

Population readiness React addendum (2026-08-25): `/app/admin/population-readiness` now exposes the canonical organization population-readiness endpoint as a dedicated, season-aware matrix. It shows all thirteen required operating-bundle components, scope/season/state readiness, persisted record references, explicit blockers, and read-only activation flags; the page cannot create packages, alter permissions, call providers, advance stages, or enable production.

Outcome analytics loop addendum (2026-08-25): Analytics now has a dedicated organization-scoped intended-versus-actual outcome record through `GET/POST /v1/analytics/outcomes`. Outcome records preserve the intended play, practice period, game-plan decision, scouting claim, or player assignment; observed result; success/sample counts; situation context; linked play/practice/film/game-plan evidence; Wilson 95% uncertainty; confidence; generalization eligibility; and explainable human-review flags. The React Analytics workbench separates Outcomes and Design → outcome views from metric observations and reports and provides a governed outcome recorder. Verification now passes 86/86 frontend tests and 576/576 Python tests with a passing production build; provider deployment, real organization data, and owner authorization remain pending.

Film workflow-link addendum (2026-08-25): Film observations now normalize and persist governed `linked_record_refs` for Playbook, Scouting, Player Development, Game Plan, and Analytics targets. Telestration, tracking, and evidence-tag authoring can attach these links; Film inspectors expose one-click workspace navigation with the record query, and Scouting, Player, Game Plan, and Analytics initialize the requested record context. The Film Studio panel is lazy-loaded so the main Film route remains within the 30 KiB budget at 19.61 KiB; verification now passes 89/89 frontend tests and 578/578 Python tests with a passing production build.

Practice outcome addendum (2026-08-25): the Practice workbench now exposes a lazy-loaded Rep outcomes view that records an intended `practice_period` against observed result, successful-rep count, sample size, period install context, linked plays/drills, optional Film observation IDs, and coach notes through the Analytics outcome API. Performance staff have an explicit bounded `record_outcome` permission; the feature does not alter player status or activate a practice. The main Practice route remains 28.25 KiB and the recorder chunk is 4.98 KiB; verification now passes 89/89 frontend tests and 579/579 Python tests with a passing production build.

Delivery notification addendum (2026-08-25): creating a Game-Week Delivery responsibility now persists a deterministic organization-scoped unread notification addressed to the assigned owner, including category, due time, linked task ID, and `/app/delivery?record=...` deep link. The Operations Inbox can aggregate the notification without external provider delivery, and the Delivery page honors the record query for direct task inspection. Verification remains 89/89 frontend tests, 579/579 Python tests, and a passing production build; external notification providers remain intentionally unconfigured.

Scouting tendency addendum (2026-08-25): the Scouting workbench now queries `GET /v1/scouting/tendency-explorer` when the Explorer tab is active. The organization-scoped service normalizes down, distance, field zone, personnel, formation, motion, front, coverage, and pressure dimensions; groups claims with sample/confidence context; preserves source clips/evidence; detects explicit and stance-derived contradictions; and returns explainable low-sample, missing-evidence, low-confidence, contradiction, and staff-review gates. The React explorer retains its local interaction fallback if the server query is unavailable, and the existing collaboration handoff keeps game-plan claims under human review. The Scouting route is 20.59 KiB; verification now passes 90/90 frontend tests and 583/583 Python tests with a passing production build.

Play Designer modernization addendum (2026-08-25): the top-priority React stream now includes an organization-backed concept-template library with eight offense/defense starter packages, relative geometry application, layer insertion, save-current-play template capture, and palette-connected search/filter/preview controls. Timeline normalization preserves pre-snap motion down to -5,000 ms and canonicalizes event aliases. Immutable version diffs now return both snapshot designs so the Review panel can display an accessible, non-interactive visual overlay of compared paths and personnel. Teaching/player views now include a filtered field diagram, context-player de-emphasis, progressive step reveal, and active-assignment replay controls. Evidence includes `playbook/concept-templates.json`, `contracts/play-concept-template.schema.json`, `src/nfl_fidos/play_design_service.py`, `src/nfl_fidos/play_timeline.py`, `frontend/src/play-designer/TemplateLibraryPanel.tsx`, `frontend/src/play-designer/TeachingDiagram.tsx`, and `frontend/src/play-designer/PlayDesignerCanvas.tsx`. Current verification: 116 frontend tests pass across 27 files; 23 Play Designer service/API/export tests pass; TypeScript typecheck passes; and the production Play Designer route chunk is 89.48 kB under the local 90 kB ceiling. This does not close the Master Codex goal: production deployment/provider setup, moderated pilot evidence, full parity audit, complete advanced collaboration/export/legality depth, and Stage 0 owner authorization remain gated.

Export addendum (2026-08-25): every generated Play Designer artifact now carries an auditable source manifest and manifest hash. The manifest records design ID, version, immutable snapshot, content checksum, renderer checksum, status, release ID, and approval state; signed artifacts include the manifest hash in the HMAC-covered fields. The export dialog surfaces the source lock before download.

Audience export addendum (2026-08-25): the React export flow now exposes coach/full-call, player, and position-group audience selection and passes the selected role through the organization-scoped export API, reusing the same canonical visibility rules as the teaching view.

Wristband layout addendum (2026-08-25): server-rendered wristband exports now provide standard two-column, compact three-column, and four-column sideline-strip layouts with explicit capacities, sizing, and truncation rules; invalid layout/artifact combinations fail validation before rendering.

Export preflight addendum (2026-08-26): `/v1/playbook/designs/export/preflight` now performs a non-rendering, organization-scoped export gate that shares effective-layout resolution with the renderer, returns structured per-design validation issues, and computes the exact source manifest hash that will be attached to a final artifact. The React export dialog invalidates stale checks whenever the packet, format, layout, or audience changes; artifact generation remains disabled until a matching preflight is valid. Focused Play Designer backend tests now pass 26/26, the full frontend suite passes 117/117 across 27 files, TypeScript typecheck passes, and the production build passes; full Python regression and moderated pilot evidence remain separate gates.

Install handout addendum (2026-08-26): PDF install-sheet exports now render a dedicated coaching handout with field diagram, branded metadata, assignment ledger, player/position ownership, landmark/timing cues, and teaching notes; role-scoped and black-and-white modes remain supported. The existing CSV install export remains available for structured downstream workflows.

Position authoring addendum (2026-08-26): the selected-player inspector now exposes a position-aware authoring toolkit connected to the full asset registry and concept-template library. Role profiles rank compatible routes, motions, runs, protections/blocks, coverages, rushes, stunts, fits, reads, checks, and teaching cues; choosing an asset activates the existing canvas tool, while suggested templates layer through the canonical materializer. Verification now passes 125 frontend tests across 30 files, TypeScript typecheck, and the production build. This improves the coach workflow but does not close the broader production, pilot, parity, or Stage 0 gates.

Visual authoring addendum (2026-08-26): assignment inspection now exposes arrow/line meaning, end/start/both/none arrowheads, smooth versus sharp path geometry, solid/dashed/dotted treatment, line weight, and line-cap controls. Those values are stored on the canonical assignment and rendered by the SVG canvas during normal editing and synchronized playback. The feature is covered by the inspector test suite; the frontend remains at 125 passing tests across 30 files with passing typecheck and production build.

Action materialization addendum (2026-08-26): the position toolkit now provides one-click starting-action generation as well as manual draw mode. `frontend/src/play-designer/actionMaterializer.ts` creates bounded position-relative routes, motions, runs, blocks/protections, coverage, rush, stunt, fit, and fallback paths with player/asset ownership, assignment and teaching text, route depth and landmarks, timeline phases, pre-snap motion timing, and visual line metadata. The generated element enters the normal reducer, so it remains editable, undoable, versionable, validatable, collaborative, and exportable. The frontend suite passes 125/125 tests across 30 files.

Geometry authoring addendum (2026-08-26): selected assignments can snap their endpoints to canonical hashes, line of scrimmage, five-, ten-, and fifteen-yard landmarks, or the goal line. Editing Depth (yards) now changes the actual endpoint using unit-aware direction while preserving the authored start and intermediate handles. Verification remains green for the focused geometry, inspector, materializer, and full frontend build checks; the wider deployment, pilot, security, and owner-approval gates remain open.

Defensive authoring addendum (2026-08-27): selected defensive assignments now
expose a grouped responsibility-preset catalog covering spill/box/force/cutback
fits, deep-third/quarter-match/hook-curl/robber/man-trail/bracket coverage,
edge and A-gap pressure, TEX/ET stunts, and sky/spin rotations. Presets write
structured fit, coverage, rush, stunt, rotation, leverage, phase, objective,
responsibility, and diagram semantics into the canonical element while keeping
the action editable and sending final enforcement through the server validator.
Explicit frontend fields now include `fit_rule`, `coverage`, `rush_lane`,
`blitz_path`, `stunt`, and `rotation`. Verification: 137 frontend tests across
33 files, typecheck, and production build pass. This is a defensive authoring
accelerator, not evidence that the remaining front/strength, coverage-shell,
rotation-sequencing, rule-profile, pilot, deployment, or owner-approval gates are
complete.

Release verification correction (2026-08-27): the full frontend suite passes
137/137 across 33 files, the production Play Designer route entry is 45.18 KiB
after heavy designer modules were moved behind lazy boundaries, and the full
Python regression suite passes 594/594. Typecheck, production build, static
asset/deep-link checks, and the enforced designer route-size check are green.
This is local engineering evidence only; target deployment, moderated pilot,
provider setup, and owner authorization remain open.

Geometry semantics addendum (2026-08-27): Play Designer assignment handles now
carry accessible start/stem/break/finish roles, assignment inspection provides
unit-aware angle presets that mutate the final endpoint, and timed intersecting
routes receive visible possible-collision feedback. The collision cue is an
authoring aid and does not bypass server legality severity or approved coach
overrides. Verification: 137 frontend tests across 33 files, typecheck,
production build, and 593 Python regression tests pass.

Defensive exchange addendum (2026-08-27): defensive rush, stunt, and rotation
assignments now support reciprocal partner linking and explicit exchange roles
for penetrate/loop, rush/replace, drop/replace, carry/transfer, and
rotate/replace relationships. The data is stored on both canonical assignments
for timeline, teaching, validation, review, and export consumers. Verification:
137 frontend tests across 33 files, typecheck, production build, and 593 Python
regression tests pass.

Route corridor intent addendum (2026-08-28): intersecting timed routes now
produce an explainable pair report in the selected-route inspector. Coaches can
mark a crossing as needs review, intentional, or avoid, and record the teaching
reason. Intentional status requires both routes to opt in, so accidental route
collisions remain visible. Verification: 163 frontend tests across 42 files,
passing typecheck/build, and a 45.88 KiB Play Designer route entry. This is an
authoring aid; server legality and approval remain authoritative.

### Defensive teaching context addendum (2026-08-28)

Role-filtered teaching steps now preserve and display defensive gap, exchange,
replacement-zone, trigger, and sequence context. Player views receive their
own filtered responsibility while coach views retain the full-call context;
accessible read-through text includes the same information. Focused service,
frontend teaching, typecheck, and production-build verification pass. This does
not close production deployment, pilot, or owner-approval gates.

### Phase-level exchange mastery addendum (2026-08-28)

Teaching role-view steps now expose independent mastery state derived from
organization-scoped mastery records, allowing exchange and replacement phases to
be tracked separately while preserving canonical step IDs and practice linkage.
Focused Python mastery/teaching tests, full frontend tests, typecheck, and build
verification pass. This does not close production deployment, pilot, or approval
gates.

### Practice responsibility outcome addendum (2026-08-28)

Practice and Analytics outcome records now preserve optional canonical assignment,
teaching-step, and responsibility-phase linkage. This connects defensive read,
exchange, replacement, and finish performance to the play, practice period,
drill, film evidence, and phase-level mastery loop. Full Python and frontend
regressions, typecheck, and build verification pass; production data and pilot
gates remain open.

## Remaining major areas

### Export fidelity addendum (2026-08-28)

SVG and HTML export now retain alternate route branches, branch conditions, and
line style/weight/cap semantics, while accessible export text describes the
conditional path timing. The deterministic local visual baseline was updated to
the new renderer checksum and the quality gate passes. This remains local
renderer evidence; printer/device validation and target-environment deployment
are still required.

PDF and PNG renderers now preserve alternate branch geometry alongside the SVG
and HTML renderers. The PDF path applies alternate-path styling and the raster
path renders branch segments when the optional imaging dependency is available;
the minimal fallback remains valid. Focused export and quality gates pass; real
printer/device validation remains open.

- Program-owner submission and review of Stage 0 exit approval; the stage manifest must remain at `STAGE-0 / STAGE-0A` until separately authorized.
- Owner acceptance of the compiled Stage 25 specification and population of an approved organization-specific terminology/doctrine/source corpus.
- Production model/tool adapters, live authorized NFL/team sources, provider credentials, managed storage, search infrastructure, and external monitoring/secret-manager deployment.
- Real organization learning, staff, specialist, performance, scouting, and weekly game-plan records with qualified human operations.
- Larger empirical evaluation corpus and calibration against real-world/production data.
- Moderated coordinator, coach, and player pilot sessions using approved organization terminology, roster, and play data; tablet, production-browser, screen-reader, keyboard-only, contrast, reduced-motion, and print-accessibility verification with measured usability outcomes.
- Advanced React parity beyond the completed operational workbenches: provider-managed media storage/deployment beyond the approved local server-path catalog, and a formal feature-parity audit before any legacy dashboard retirement. Multi-item publishing/layout composition is now locally implemented with explicit packet layouts, correct pagination, and layout-aware export metadata; true multi-user edit convergence is also implemented and locally verified for disjoint field edits with explicit overlap conflicts.
- Deployment configuration, secret-manager/database/monitoring/provider registration, production migration and backup setup, rollback rehearsal in the target environment, and release approval.
- Stage 0 owner authorization and Stage 25 specification acceptance; no code path should auto-advance either gate.

Variant history addendum (2026-08-28): persisted multi-look variant batches are
now restorable through the organization-scoped read endpoint
`GET /v1/playbook/designs/variants`, with optional `source_design_id` filtering.
The Play Designer workspace payload carries the same newest-first review
history, preserving source lineage, draft children, transformation recipes,
immutable source revision, and human-review-required status. This closes the
local refresh/discoverability gap; approval, publishing, provider-scale
administration, and pilot validation remain separately gated.

Feature-parity addendum (2026-08-28): the repository now includes
`control/feature-parity-manifest.json` and the dependency-free
`scripts/audit_feature_parity.py` audit. The manifest maps all 22 legacy
dashboard anchors to the React route/file that replaces or consolidates each
surface; the audit verifies anchor presence, route tokens, source files, unique
IDs, and the non-authorized retirement decision. The local structural result is
`ready_for_human_review` with 11 migrated and 11 consolidated entries, while
`retirement_authorized` remains false. Behavioral parity review, deployment
validation, accessibility evidence, and the separately authorized legacy
dashboard retirement decision remain open.

Authenticated synthetic Play Designer rehearsal addendum (2026-08-28):
`scripts/play_designer_http_rehearsal.py` now starts an ephemeral local HTTP
server with the documented demo secret and reads the seeded organization
through the real authenticated API routes. Workspace loading, version history,
NFL legality, QB player view rendering, and immutable published-release
metadata all passed for `PD-DEMO-OFF-DAGGER`. The rehearsal shuts down its
server and reports `external_state_changed: false`; it is local synthetic
evidence only and does not replace browser, deployment, pilot, or owner
authorization evidence.

Governed template lineage UI addendum (2026-08-29): the React Play Designer
Concepts panel now connects organization-owned template lineage impact reports,
bounded assignment-field proposals, and program-owner-only approval/propagation
controls to the canonical API. The UI displays descendant depth, inherited and
local override counts, proposal status, decision identity, and affected-package
review state. The source fingerprint is rechecked by the server, system
templates remain immutable, and child-local assignments remain preserved. Local
verification passes the focused lineage interaction suite, TypeScript
typecheck, and the production frontend build; provider-scale administration,
multi-browser/network validation, pilot evidence, and owner authorization remain
open.

Export geometry safety addendum (2026-08-29): Play Designer export preflight
now fail-closes malformed or out-of-bounds player, primary-path, and branch
coordinates against the canonical 100 x 53.33 field. Errors preserve exact
source paths and prevent clipped geometry from reaching rendered artifacts.
Focused export coverage and the full Python regression suite pass; printer,
device, and deployment-environment certification remain pending.

Draft/export geometry consistency addendum (2026-08-29): alternate route
branches now use the same canonical shape and field-bounds validation contract
as primary play paths. Draft checks report deterministic branch paths for short,
malformed, or out-of-bounds geometry, and export preflight independently
fail-closes the corresponding artifact risk. Focused play-creation/export tests
pass; physical device and deployment validation remain pending.

Rule-profile consistency addendum (2026-08-29): the structural Play Designer
validator now follows the selected game format for player-count validation,
including 5-on-5 flag designs and explicitly configured youth formats. The
legacy offensive legality pass no longer applies the seven-player tackle
formation rule to flag designs; profile-specific checks remain in the
explainable advanced legality report. This closes a validation-pipeline
inconsistency without claiming that local youth, NFHS, or flag variants are
fully authoritative until their adopted rule sources are supplied. Focused
Play Designer creation, service, API, and export coverage passes; real rulebook
adoption and human officiating review remain external acceptance work.

Rule-profile UI provenance addendum (2026-08-29): the React Play Designer now
loads the controlled rule-profile catalog through the organization-scoped API
and uses the server response for profile labels, local-adoption behavior, and
source/rule-reference display in the inspector. A bounded fallback keeps the
editor usable during loading or offline recovery, while server legality remains
authoritative. Focused API and inspector coverage passes; deployment-network,
browser, accessibility, and locally adopted rulebook validation remain open.

Asset registry contract addendum (2026-08-29): the professional catalog
validator now requires all 13 authoring families, including motion and block,
and rejects orphaned deprecated/retired replacement references or malformed
formation, personnel, and rule-profile compatibility lists before they reach
the editor palette. The canonical 128-asset registry passes the hardened
contract; organization-specific catalog administration and deployment-scale
validation remain open.

Media job boundary addendum (2026-08-29): media processing job creation now
fails closed for malformed IDs, operations, payloads, requesters, and retry
limits, returning structured invalid records instead of allowing type errors to
reach the worker. Existing path authorization, bounded ffprobe/transform
execution, retry state, and output lineage remain intact. Focused media-worker
coverage and the full Python regression suite pass; external media tooling,
managed storage, and deployment-worker certification remain open.

Export selection integrity addendum (2026-08-29): Play Designer preflight and
rendering now share one organization-scoped design loader that rejects blank,
non-string, duplicate, and unknown play IDs before a packet is assembled. This
keeps source manifests, pagination, signatures, and printed artifacts aligned
with the staff selection. Focused export coverage and the full Python suite
pass; printer/device and deployment-environment certification remain open.

Tenant audit isolation addendum (2026-08-29): organization-scoped audit history
now filters by the complete `(collection, record_id)` identity instead of the
record ID alone. This prevents a same-ID collision across collections from
exposing another organization’s event. A dedicated collision regression test
passes, and the full Python suite now totals 666 passing tests; production
database deployment, independent tenant-isolation testing, and operational
security review remain open.

Gap ownership map addendum (2026-08-29): the structured Play Designer
assignment graph now emits a canonical defensive gap-ownership payload with
assigned, unassigned, and conflicted entries, preserving player, assignment,
responsibility, exchange, and path context for canvas, teaching, and export
consumers. The payload never selects a winner for conflicting owners; it keeps
the unresolved state visible for coach review. Focused play-creation, service,
and API coverage passes; visual browser/device certification remains pending.

Route-corridor diagnostics addendum (2026-08-29): advanced legality findings
now include deterministic geometric collision corridors with intersection
coordinates and the source segment indexes for each overlapping route pair.
Intentional crossings continue to require documentation, while policy=error
still produces a blocking finding. This gives canvas, teaching, and export
surfaces actionable geometry instead of only route IDs; focused legality and
full regression validation remain green, with physical device certification
still pending.

Coverage-shell authority addendum (2026-08-29): the server-side assignment
graph now emits a canonical coverage-shell map alongside gap ownership. Each
declared zone preserves assigned, unassigned, or conflicted status plus player,
path, timing, exchange, rotation sequence, trigger, vacated-zone, and
replacement-defender context. This keeps API, teaching, and export consumers
aligned with the interactive shell editor; focused Play Designer coverage and
full regression validation remain green, while deployment-device certification
remains pending.

Offensive protection integrity addendum (2026-08-29): structural Play
Designer validation now recognizes the professional block/pull/trap/wrap/fold/
combo/insert/arc/screen primitive catalog and protection modes. Targeted
primitives, combo partners and targets, and non-screen protection threats must
be explicit; block, partner, and protection references must resolve to an
assignment in the same play. Invalid primitive, self-reference, missing-target,
and stale-reference cases are covered by focused tests; organization-specific
coaching terminology and production officiating review remain external.

Route semantics integrity addendum (2026-08-29): structural Play Designer
validation now checks the editor's controlled route-family, break, finish, and
option vocabularies, bounds stem and break depths to 0–60 yards, and flags
break-depth metadata without a declared break type. This keeps direct geometry
editing and semantic route metadata aligned before review, publication, or
export; focused route and full regression validation remain required for each
future vocabulary extension.

Route branch parity addendum (2026-08-29): the same controlled route semantics
and depth bounds are now applied to alternate route branches, while omitted
branch fields remain eligible to inherit the parent route contract during
materialization. This prevents a malformed option path from bypassing the
primary route validator; focused branch coverage and the full regression suite
pass.

Timeline synchronization addendum (2026-08-29): timeline validation now
checks event-to-element timing overlap, optional QB-read target references and
target-window overlap, and explicit synchronization groups for timing gaps.
These checks preserve the existing event vocabulary and report coach-review
warnings where team timing conventions vary, giving playback, teaching, and
export consumers actionable synchronization evidence.

Assignment graph semantic-context addendum (2026-08-29): graph nodes now carry
the authored route family, break and depth contract, blocking/protection
primitive, responsibility, technique, landmark, gap, zone, target, exchange,
and timing context in addition to IDs and edges. This keeps teaching, export,
analytics, and future collaboration consumers from having to reconstruct
football meaning from geometry alone.

Assignment graph relationship addendum (2026-08-29): graph edges now include
explicit block-target, combo-partner, and protection-threat relationships in
addition to generic target, exchange, prerequisite, and player edges. The
relationship vocabulary is preserved in the typed frontend contract so
downstream teaching, export, analytics, and collaboration surfaces can walk
the authored protection graph directly.

Player assignment coverage addendum (2026-08-29): the authoritative graph now
emits a per-player assignment summary for every player icon, including
position, assignment count and IDs, assignment kinds, target references, and
assigned/unassigned status with aggregate counts. This creates a shared quality
signal for position-aware authoring, teaching, practice linkage, and release
readiness without inferring coverage from canvas pixels.

Position-options API addendum (2026-08-29): the organization-scoped Play
Designer service now ranks selectable registry assets and templates for a
requested player position and unit, applying formation, personnel, rule-profile,
compatibility, lifecycle, and position-family preferences. The authenticated
`/v1/playbook/designs/position-options` route returns bounded candidates with
explainable scores and reasons for coach-facing recommendations; focused service
and API tests pass, while organization-specific terminology remains pending.

Position-options editor integration addendum (2026-08-28): the selected-player
inspector now requests the authoritative position-options contract with the
current formation, personnel, and rule-profile context. The Position Toolkit
uses the server-ranked asset and template candidates when available, displays
the catalog recommendation rationale, and falls back to the local registry
during loading or offline conditions. API, inspector, and toolkit regression
coverage passes; live organization terminology and device-level certification
remain pending.

Route-handle deletion integrity addendum (2026-08-28): direct keyboard and
double-click removal of primary or alternate route handles now updates the
remaining route geometry and recomputes synchronized stem/break depth metadata,
including inherited branch semantics. This prevents stale route contracts from
reaching legality validation, teaching views, or exports after a coach edits a
path. Focused route/canvas coverage passes; broader device and production
workflow certification remains pending.

Route-handle visual semantics addendum (2026-08-28): selected primary route
handles now display their role and inferred geometric depth directly on the
field, including START, STEM, BREAK, and FINISH captions. The overlay follows
the same canonical points used by drag/keyboard editing and remains
non-interactive so it does not interfere with pointer targeting; focused canvas
coverage passes, while visual regression and device certification remain
pending.

Named defensive exchange authoring addendum (2026-08-28): the two-assignment
defensive exchange panel now exposes named TEX, ET, cross-dog, rush-replace,
and carry-transfer presets. Applying a preset writes reciprocal roles plus the
relationship-level concept label and exchange phase to both assignments, while
the existing generic role and replacement-zone controls remain available.
Inspector regression coverage verifies a TEX authoring action end to end;
organization terminology and live coordinator review remain pending.

Named exchange validation addendum (2026-08-28): the assignment graph now
validates named TEX/ET and cross-dog concepts for reciprocal concept metadata,
penetrate/loop role pairing, required trigger and communication cues, and
position-compatible partner families. Mismatches remain explainable coach
review warnings rather than silently selecting a winner, preserving local
terminology flexibility while blocking semantic drift from downstream
teaching, export, and release consumers. Full Python regression coverage
passes; live coordinator review and organization-specific position taxonomy
remain pending.

Named exchange UI guard addendum (2026-08-28): the defensive two-assignment
authoring panel now performs immediate position-family compatibility feedback
for TEX, ET, and cross-dog selections. Incompatible pairs receive an
accessible coach-review warning before the reciprocal preset is applied, while
the server-side validator remains authoritative and preserves the warning for
review. Focused exchange/inspector coverage passes; organization-specific
position aliases and live coordinator validation remain pending.

Exchange responsibility authoring addendum (2026-08-28): named TEX and ET
authoring now exposes stunt direction, penetration lane, and loop-landmark
controls. Applying the pair writes lane metadata to the penetration side and
landmark metadata to the looping side; the assignment graph warns when either
required responsibility is missing. This makes the exchange actionable for
timeline, teaching, and export consumers; organization-specific lane language
and live coordinator review remain pending.

Alternate route geometry integrity addendum (2026-08-29): exact coordinate
edits, midpoint insertion, and handle removal in the inspector now use the
same branch geometry synchronizer as canvas edits. Alternate paths preserve
inherited route family, break, finish, and timing semantics while recomputing
stem/break depth metadata after a geometry change, preventing branch contracts
from drifting before validation, teaching, or export. Focused inspector and
route-authoring regression coverage passes; device-level and organization
workflow certification remain pending.

Profile-aware personnel matching addendum (2026-08-29): advanced legality
personnel constraints now normalize case, spaces, and hyphens and match
position, role, personnel-group, and explicitly authored player aliases. This
keeps formation counts reliable when a program uses equivalent roster language
and retains explainable mismatch findings for unresolved labels; local league
adoption and human officiating review remain external.

Server-side defensive front integrity addendum (2026-08-29): when a design
authors defensive front metadata, the assignment graph now validates unique
front slots, complete technique/alignment relationships, and controlled
technique/alignment vocabularies. These findings align the server contract with
the interactive front editor so duplicate or incomplete front data cannot be
silently carried into teaching, release, or export; local scheme terminology
and human coordinator review remain external.

Server-side coverage-shell integrity addendum (2026-08-29): advanced legality
now includes rotation destinations in declared shell ownership, reports
unassigned declared zones, flags duplicate coverage/rotation owners without an
explicit exchange or shared-ownership explanation, and identifies rotations
with no destination responsibility. This keeps the interactive shell map and
release gate aligned; scheme-specific shared-zone doctrine and human
coordinator review remain external.

Server-side rotation sequencing addendum (2026-08-29): post-snap rotation
assignments now receive authoritative checks for positive sequence order,
duplicate order conflicts, trigger declaration, and replacement-defender
references. This preserves deterministic shell teaching and prevents stale
replacement links from reaching release or export; team-specific simultaneous
rotation doctrine remains reviewable rather than inferred.

Protection graph authority addendum (2026-08-29): professional blocking and
protection fields now activate the assignment graph even when a design does
not also contain a generic objective, target, or dependency field. Graph nodes
preserve primitive, protection mode, partner, threat, slide, and scan-order
metadata alongside their relationship edges, keeping protection-only authoring
available to teaching, analytics, collaboration, and export consumers.

Protection relationship integrity addendum (2026-08-29): the assignment graph
now validates every block-target, combo-partner, and protection-threat edge it
emits, including self-reference rejection and stale-reference guidance. This
prevents protection diagrams from presenting relationships that cannot be
resolved within the authored play.
