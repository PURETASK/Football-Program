# NFL FIDOS JSON API

The API is available through the pure router in `src/nfl_fidos/api.py` and an optional standard-library HTTP adapter in `src/nfl_fidos/http_server.py`.

Routes:

- `GET /health`
- `GET /v1/control`
- `GET /v1/control/stage-25-acceptance?organization_id=ORG-...` to inspect the compiled Master Codex specification and prior owner acceptance evidence (Bearer auth; organization-scoped)
- `POST /v1/control/stage-25-acceptance` with `{organization_id, acceptance_id, rationale, evidence_refs, accepted_at}` for program-owner-only, non-activating specification acceptance evidence
- `GET /v1/evals`
- `GET /v1/ontology/resolve?organization_id=ORG-...&term=shotgun` (Bearer auth; organization-scoped canonical/alias resolution)
- `GET /v1/ontology/related?organization_id=ORG-...&term_id=TERM-...&relationship_type=...` (Bearer auth; organization-scoped relationship query)
- `GET /v1/ontology/team-aliases?organization_id=ORG-...&team_id=TEAM-...` (Bearer auth; organization-scoped team terminology)
- `POST /v1/ontology/team-aliases` with `{organization_id, team_id, alias, term_id, reason, source_refs, approval_ref}` (program-owner Bearer auth; persists an auditable locked team alias)
- `GET /v1/film/search?organization_id=ORG-...&query=...&team=...&opponent=...&domain=...&label=...&confidence=...` (Bearer auth; organization-scoped)
- `GET /v1/knowledge/search?organization_id=ORG-...&query=...&classification=...&state=...&collection=...&limit=...` (Bearer auth; organization-scoped, provenance-preserving)
- `GET /v1/media/assets?organization_id=ORG-...` and `GET /v1/media/clips?organization_id=ORG-...&team=...&opponent=...` (Bearer auth; organization-scoped)
- `POST /v1/plays/compile` with a minimum play record JSON body
- `POST /v1/workflows/core-play`
- `POST /v1/workflows/core-play/{play_id}/approve`
- `POST /v1/workflows/evidence-intelligence`
- `POST /v1/workflows/weekly-delivery`
- `POST /v1/film/observations` with `{organization_id, observation}` (Film-authoring permission for coach staff, analysts, and program owners; Bearer auth); `observation.linked_record_refs` accepts governed `{record_type, record_id, label}` links for Playbook, Scouting, Player Development, Game Plan, and Analytics so frame evidence retains downstream workflow lineage
- `POST /v1/film/quizzes` with `{organization_id, quiz_id, title, role, clip_ids, questions}` (coach permission; Bearer auth)
- `POST /v1/film/quizzes/{quiz_id}/attempts` with `{organization_id, attempt_id, participant, answers}` (Bearer auth)
- `POST /v1/media/assets` with authorized local file metadata and approved storage roots (Film-authoring permission for coach staff, analysts, and program owners; Bearer auth)
- `POST /v1/media/clips` with `{organization_id, clip_id, asset_id, start_seconds, end_seconds, team, opponent, situation}` (Film-authoring permission for coach staff, analysts, and program owners; Bearer auth)
- `GET /v1/media/jobs?organization_id=ORG-...&status=...` (Bearer auth; organization-scoped)
- `POST /v1/media/jobs` to enqueue `probe`, `transcode`, `segment`, `thumbnail`, or `index` work (Film-authoring permission for coach staff, analysts, and program owners; Bearer auth). `index` jobs build bounded ffprobe-backed stream metadata and searchable fields, persist output evidence, and never publish or decode media content.
- `POST /v1/media/jobs/{job_id}/claim`, `/complete`, and `/fail` for worker lifecycle transitions (Bearer auth)
- `GET /v1/sources?organization_id=ORG-...` to inspect registered source freshness (Bearer auth)
- `POST /v1/sources` to register an owner-approved HTTPS source and authorized domain list
- `POST /v1/sources/{source_id}/refresh` to record a governed source refresh (analyst permission; Bearer auth)
- `GET /v1/operator/summary?organization_id=ORG-...&include_evals=true` for role-aware workspace state and pending-review counts (Bearer auth)
- `POST /v1/delivery/tasks` creates an organization-scoped game-week responsibility and an unread owner notification with a safe Delivery Center deep link; the notification is internal/inbox-visible and does not send externally
- `GET /v1/governance/inbox?organization_id=ORG-...` for program-owner/validator approval evidence and pending records (Bearer auth)
- `GET /v1/agents/runs?organization_id=ORG-...` for tenant-scoped controlled agent-run history (Bearer auth; governance permission)
- `POST /v1/agents/runs` with `{organization_id, run_id, agent_id, family, capability, workflow_id, payload, local_validation:true}` for program-owner/validator local validation only; no provider call, canonical write, or production activation is permitted
- `GET /v1/organizations/population-readiness?organization_id=ORG-...&season=...` for a tenant-scoped checklist of the thirteen operating-bundle components and their blockers (Bearer auth; governance permission)
- `GET /v1/delivery/pilot-readiness?organization_id=ORG-...` and `POST /v1/delivery/pilot-readiness` for non-live pilot readiness evidence; POST evaluates a named wave, users, completed capabilities, acceptance evidence, feature flags, and rollback state without enabling production
- `GET /v1/delivery/pilot-organization?organization_id=ORG-...` and `POST /v1/delivery/pilot-organization` for program-owner-only bounded organization selection after approved organization context and terminology checks
- `GET /v1/delivery/pilot-package?organization_id=ORG-...` and `POST /v1/delivery/pilot-package` for program-owner-only composition of selection, readiness, and rollback evidence into a non-live pilot delivery package
- `GET /v1/ux/usability-feedback?organization_id=ORG-...` and `GET /v1/ux/usability-feedback/summary?organization_id=ORG-...` for role-scoped usability evidence inspection; `POST /v1/ux/usability-feedback` records role-derived pilot/accessibility findings without changing permissions, releases, or stage state
- `GET /v1/player/today?organization_id=ORG-...&player_id=PLAYER-...` for the player’s privacy-scoped Today workspace
- `POST /v1/player/assignments` for coach-created, source-linked player assignments
- `GET /v1/game-plan/workspace?organization_id=ORG-...&week=WEEK-...` for scoped staff game-plan review
- `GET /v1/practice/workspace?organization_id=ORG-...&week=WEEK-...` for scoped practice plans and load state
- `POST /v1/practice/plans` for coach-authored practice plans with objective and load controls
- `GET /v1/practice/attendance?organization_id=ORG-...&practice_id=PRACTICE-...` for roster-linked participation records and status summaries
- `POST /v1/practice/attendance` with `{organization_id, attendance_id, practice_id, player_id, status, minutes_available, period_ids, note, source_refs}` for coach/performance/owner attendance records; the practice and player must exist in the organization, and the response never changes medical status or eligibility
- `GET /v1/schemes/workspace?organization_id=ORG-...&unit=offense|defense` for scoped scheme review
- `POST /v1/schemes` for coach/analyst-authored compositional scheme records
- `GET /v1/analytics/workspace?organization_id=ORG-...&situation=...` for metric lineage and uncertainty review
- `POST /v1/analytics/reports` for analyst-authored, reviewable metric reports
- `GET /v1/analytics/outcomes?organization_id=ORG-...&intended_record_id=...` for intended-versus-actual outcome records, sample aggregation, result counts, and human-review state
- `POST /v1/analytics/outcomes` with `{organization_id, outcome_id, intended_record_type, intended_record_id, actual_result, success_count, sample_size, context, evidence_refs, linked_play_id, practice_id, film_observation_ids, game_plan_id, notes}` for organization-scoped outcome capture; the service calculates success rate, confidence, Wilson uncertainty, generalization eligibility, and explainable review flags, while invalid or evidence-free records are not persisted
- `GET /v1/scouting/workspace?organization_id=ORG-...&opponent=...` for opponent profiles, reports, matchup models, and adaptation warnings
- `GET /v1/scouting/tendency-explorer?organization_id=ORG-...&opponent=...&down=...&distance=...&field_zone=...&personnel=...&formation=...&motion=...&front=...&coverage=...&pressure=...` for tenant-scoped tendency claims with normalized situation dimensions, sample/confidence context, trend and contradiction handling, source/evidence links, and explainable human-review gates
- `POST /v1/scouting/reports` for analyst-authored, reviewable opponent scouting reports
- `GET /v1/playbook/visual?organization_id=ORG-...&visual_id=VISUAL-...&role=...` for authorized deterministic SVG role views
- `POST /v1/playbook/designs/export` accepts `design_ids`, `kind`, `format`, optional `layout`, role, branding, and black-white settings; layouts include `table`, `wristband_2col`, `grid_2x2`, and `grid_3x2`, with SVG/PNG restricted to single-design output
- `GET /v1/playbook/designs/variants?organization_id=ORG-...&source_design_id=DESIGN-...` returns persisted organization-scoped multi-look variant batches and draft child designs, optionally filtered to one source play, with a computed per-child review readiness summary; this is read-only and does not approve or publish variants
- `POST /v1/playbook/visuals` for coach-authored validated visual play records
- `POST /v1/playbook/visuals/{visual_id}/what-if` for separate, human-review-required scenarios that cannot replace canonical visuals
- `GET /v1/film/annotation-sessions?organization_id=ORG-...` for authorized annotation-session review state
- `POST /v1/film/annotation-sessions` and `POST /v1/film/annotation-sessions/{session_id}/annotations` for persisted film annotation and correction workflows
- `GET /v1/film/playlists?organization_id=ORG-...` and `POST /v1/film/playlists` for organization-scoped, role-filtered clip playlists
- `GET /v1/media/assets/{asset_id}/content?organization_id=ORG-...` for authenticated full or HTTP byte-range media delivery
- `GET /v1/media/retention-plan?organization_id=ORG-...&retention_days=...` for owner-scoped, non-destructive media retention review
- `POST /v1/media/retention-scan` for owner-scoped, persisted, non-destructive retention review execution
- `POST /v1/media/retention-execute` for program-owner-approved, dry-run-by-default managed-media retention execution; production execution remains blocked by the Stage 0 manifest
- `POST /v1/media/transform-batch` for bounded, organization-scoped execution of queued transcode, segment, and thumbnail jobs
- `POST /v1/sources/refresh-all` for bounded stale-only authorized source refresh with per-source failure evidence
- `POST /v1/sources/scheduled-refresh` for freshness-window-based bounded refresh planning and persisted batch execution

The router returns `{status, data, error}` JSON envelopes. Invalid play records return HTTP 422 with compiler issues; unknown routes and unsupported methods are explicit errors.
