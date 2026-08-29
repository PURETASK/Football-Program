import { beforeEach, expect, vi } from 'vitest';

import type { AppSession, PracticePlan } from '../types';
import { fetchPlayPositionOptions, fetchPlayRuleProfiles } from './api';
import { appendCollaborationComment, approvePlayLegalityOverride, createCollaborationThread, createDeliveryPacket, createPilotDeliveryPackage, createPlayTemplate, createPlayVariants, createPlayVariantReleaseBundle, evaluatePilotReadiness, exportPlayDesign, fetchAdminWorkspace, fetchCollaborationWorkspace, fetchCollaborationStream, fetchOrganizationPopulationReadiness, fetchPlayAssets, fetchPlayCollaborationStream, fetchPlayVariantBatches, fetchPlayVariantReleaseBundle, fetchStage25Acceptance, fetchPracticeAttendance, markCollaborationNotificationsRead, createFilmClip, createFilmObservation, createFilmVoiceNote, createGamePlanReleaseSnapshot, createPracticePlan, fetchFilmWorkspace, fetchMediaProcessingJob, fetchMediaProcessingJobs, fetchOperationsInbox, fetchPlayRoleView, fetchPlayVersionDiff, fetchPracticeDrills, fetchScoutingTendencies, markOperationsNotificationsRead, mergePlayBranch, preflightPlayDesignExport, recordAnalyticsOutcome, recordPlayMastery, recordPracticeAttendance, registerFilmAsset, requestPlayLegalityOverride, reviewGovernanceItem, selectPilotOrganization, submitPlayQuiz, submitStage25Acceptance, submitUsabilityFeedback, validatePlayDesignDraft } from './api';

const SESSION: AppSession = {
  organizationId: 'ORG-TEST-001',
  token: 'test-token',
  role: 'program_owner',
  subject: 'OWNER-TEST',
};

function response(data: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify({ status: status < 400 ? 'ok' : 'error', data }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  }));
}

describe('operational API wiring', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('requests authoritative asset compatibility for the current play context', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ assets: [{ id: 'ASSET-POST' }] }));
    const assets = await fetchPlayAssets(SESSION, { unit: 'offense', formation: 'shotgun_trips', personnel: '11', rule_profile: 'nfl' });
    expect(assets).toEqual([{ id: 'ASSET-POST' }]);
    const path = String(fetchMock.mock.calls[0][0]);
    expect(path).toContain('unit=offense');
    expect(path).toContain('context_formation=shotgun_trips');
    expect(path).toContain('personnel=11');
    expect(path).toContain('rule_profile=nfl');
  });

  it('loads rule profiles from the authoritative API for inspector selection', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ profiles: [{ id: 'flag', label: 'NFL FLAG', requires_local_rules: true }] }));
    const profiles = await fetchPlayRuleProfiles(SESSION);
    expect(profiles).toEqual([{ id: 'flag', label: 'NFL FLAG', requires_local_rules: true }]);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/rule-profiles?organization_id=ORG-TEST-001');
  });

  it('loads position-aware options with the full play context', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ position: 'WR', unit: 'offense', family: 'eligible', status: 'ready', assets: [], templates: [] }));
    const options = await fetchPlayPositionOptions(SESSION, 'WR', { unit: 'offense', formation: 'shotgun_trips', personnel: '11', rule_profile: 'nfl' });
    expect(options.family).toBe('eligible');
    const path = String(fetchMock.mock.calls[0][0]);
    expect(path).toContain('/v1/playbook/designs/position-options?');
    expect(path).toContain('organization_id=ORG-TEST-001');
    expect(path).toContain('position=WR');
    expect(path).toContain('formation=shotgun_trips');
    expect(path).toContain('personnel=11');
    expect(path).toContain('rule_profile=nfl');
    expect((fetchMock.mock.calls[0][1]?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('posts the current unsaved play to the non-persisting validation route', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({
      design_id: 'DESIGN-DRAFT', rule_profile: 'nfl', status: 'valid', issues: [], overrides: [], draft: true, persisted: false,
      draft_checksum: 'abc', normalized_design: { id: 'DESIGN-DRAFT' }, assignment_graph: { version: '1.0', nodes: [], edges: [], findings: [], summary: { node_count: 0, edge_count: 0, blocking_count: 0, warning_count: 0 } },
    }));
    const report = await validatePlayDesignDraft(SESSION, { id: 'DESIGN-DRAFT', unit: 'offense' });
    expect(report.draft).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/validate');
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design: { id: 'DESIGN-DRAFT', unit: 'offense' } });
  });

  it('captures a saved play as an organization template', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'TPL-ORG-1', scope: 'organization' }, 201));
    const template = await createPlayTemplate(SESSION, { designId: 'DESIGN-1', name: 'Third-down package', tags: ['third-down'] });
    expect(template.scope).toBe('organization');
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/templates');
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'DESIGN-1', name: 'Third-down package', tags: ['third-down'] });
  });

  it('posts a bounded multi-look variant batch with explicit patches', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'VARIANT-BATCH-1', count: 2, variant_ids: ['P-1', 'P-2'], variants: [], source_design_id: 'DESIGN-1', status: 'created' }, 201));
    const batch = await createPlayVariants(SESSION, { designId: 'DESIGN-1', variants: [{ label: 'Cover 3', patch: { coverage: 'cover_3' } }, { label: 'Quarters', patch: { coverage: 'quarters' } }] });
    expect(batch.count).toBe(2);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/variants');
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body));
    expect(body).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'DESIGN-1' });
    expect(body.variants).toEqual([{ label: 'Cover 3', patch: { coverage: 'cover_3' } }, { label: 'Quarters', patch: { coverage: 'quarters' } }]);
  });

  it('loads persisted variant-batch history with an optional source-play filter', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ organization_id: 'ORG-TEST-001', source_design_id: 'DESIGN-1', count: 1, batches: [] }));
    const history = await fetchPlayVariantBatches(SESSION, 'DESIGN-1');
    expect(history.count).toBe(1);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/variants?organization_id=ORG-TEST-001&source_design_id=DESIGN-1');
    expect((fetchMock.mock.calls[0][1]?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('creates an owner-governed immutable variant release bundle', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'VARIANT-RELEASE-BATCH-1', batch_id: 'BATCH-1', status: 'frozen', immutable: true, manifest_hash: 'abc', production_activation: false }, 201));
    const bundle = await createPlayVariantReleaseBundle(SESSION, 'BATCH-1', 'DECISION-1');
    expect(bundle.immutable).toBe(true);
    expect(bundle.production_activation).toBe(false);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/variants/create-release-bundle');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', batch_id: 'BATCH-1', decision_ref: 'DECISION-1' });
  });

  it('reads a release bundle with organization scope and integrity evidence', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'VARIANT-RELEASE-BATCH/1', status: 'frozen', immutable: true, manifest_hash: 'abc', production_activation: false, integrity: { valid: true } }));
    const bundle = await fetchPlayVariantReleaseBundle(SESSION, 'VARIANT-RELEASE-BATCH/1');
    expect(bundle.integrity.valid).toBe(true);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/variants/release-bundles/VARIANT-RELEASE-BATCH%2F1?organization_id=ORG-TEST-001');
  });

  it('loads the complete Film Room in parallel from its five organization-scoped endpoints', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const path = String(input);
      if (path.startsWith('/v1/media/assets')) return response({ assets: [{ id: 'FILM-1' }] });
      if (path.startsWith('/v1/media/clips')) return response({ clips: [{ id: 'CLIP-1' }] });
      if (path.startsWith('/v1/film/search')) return response({ results: [{ id: 'FILM-OBS-1' }] });
      if (path.startsWith('/v1/film/playlists')) return response({ playlists: [{ id: 'PLAYLIST-1' }] });
      if (path.startsWith('/v1/film/annotation-sessions')) return response({ sessions: [{ id: 'SESSION-1' }] });
      if (path.startsWith('/v1/film/voice-notes')) return response({ voice_notes: [{ id: 'VOICE-1' }] });
      return response({}, 404);
    });

    const workspace = await fetchFilmWorkspace(SESSION);

    expect(workspace.assets).toHaveLength(1);
    expect(workspace.clips).toHaveLength(1);
    expect(workspace.observations).toHaveLength(1);
    expect(workspace.playlists).toHaveLength(1);
    expect(workspace.sessions).toHaveLength(1);
    expect(workspace.voice_notes).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledTimes(6);
    for (const [path, options] of fetchMock.mock.calls) {
      expect(String(path)).toContain('organization_id=ORG-TEST-001');
      expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
    }
  });

  it('loads organization-scoped media worker jobs with an optional status filter', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ jobs: [{ id: 'MEDIA-JOB-1', operation: 'thumbnail', status: 'retryable', last_error: { code: 'MEDIA-THUMBNAIL-FAILED' } }] }));
    const jobs = await fetchMediaProcessingJobs(SESSION, 'retryable');
    expect(jobs.jobs[0].operation).toBe('thumbnail');
    const path = String(fetchMock.mock.calls[0][0]);
    expect(path).toContain('/v1/media/jobs?');
    expect(path).toContain('organization_id=ORG-TEST-001');
    expect(path).toContain('status=retryable');
  });

  it('loads a single media job with persisted outputs and batch history', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ job: { id: 'MEDIA-JOB-1' }, outputs: [{ id: 'MEDIA-OUTPUT-1' }], batches: [{ id: 'MEDIA-BATCH-1' }] }));
    const detail = await fetchMediaProcessingJob(SESSION, 'MEDIA-JOB-1');
    expect(detail.job.id).toBe('MEDIA-JOB-1');
    expect(detail.outputs).toHaveLength(1);
    expect(detail.batches).toHaveLength(1);
    expect(String(fetchMock.mock.calls[0][0])).toBe('/v1/media/jobs/MEDIA-JOB-1?organization_id=ORG-TEST-001');
  });

  it('loads persisted pilot and usability governance records into the Admin workspace', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const path = String(input);
      if (path.startsWith('/v1/organizations/context?')) return response({ contexts: [], terminology_bundles: [] });
      if (path.startsWith('/v1/sources?')) return response({ sources: [] });
      if (path.startsWith('/v1/control/stage-0-approval?')) return response({ gate: {}, approvals: [], production_implementation_allowed: false, stage_advance_authorized: false });
      if (path.startsWith('/v1/delivery/pilot-readiness?')) return response({ reports: [], human_review_required: true, production_implementation_allowed: false });
      if (path.startsWith('/v1/delivery/pilot-organization?')) return response({ selections: [{ id: 'PILOT-SEL-1' }] });
      if (path.startsWith('/v1/delivery/pilot-package?')) return response({ packages: [{ id: 'PILOT-PKG-1' }] });
      if (path.startsWith('/v1/ux/usability-feedback?')) return response({ feedback: [{ id: 'UX-1' }] });
      return response({}, 404);
    });

    const workspace = await fetchAdminWorkspace(SESSION);

    expect(workspace.pilotSelections).toEqual([{ id: 'PILOT-SEL-1' }]);
    expect(workspace.pilotPackages).toEqual([{ id: 'PILOT-PKG-1' }]);
    expect(workspace.usabilityFeedback).toEqual([{ id: 'UX-1' }]);
    expect(fetchMock).toHaveBeenCalledTimes(7);
    for (const [path, options] of fetchMock.mock.calls) {
      expect(String(path)).toContain('organization_id=ORG-TEST-001');
      expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
    }
  });

  it('loads and submits Stage 25 specification acceptance without activation', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const path = String(input);
      if (path.startsWith('/v1/control/stage-25-acceptance?')) return response({ organization_id: 'ORG-TEST-001', spec: { id: 'SPEC-1', spec_id: 'SPEC-1', version: '1.0', validation: { status: 'valid' } }, acceptances: [{ id: 'ACCEPTANCE-STAGE25-1', status: 'accepted' }], production_implementation_allowed: false, stage_advance_authorized: false });
      return response({ id: 'ACCEPTANCE-STAGE25-2', decision: 'accepted', production_implementation_allowed: false, stage_advance_authorized: false }, 201);
    });

    const workspace = await fetchStage25Acceptance(SESSION);
    expect(workspace.spec.version).toBe('1.0');
    expect(workspace.acceptances).toHaveLength(1);
    expect(workspace.production_implementation_allowed).toBe(false);

    await submitStage25Acceptance(SESSION, {
      acceptanceId: 'ACCEPTANCE-STAGE25-2',
      rationale: 'Reviewed the compiled specification.',
      evidenceRefs: ['control/master-codex-build-spec.json'],
      acceptedAt: '2026-08-25T09:00:00Z',
    });
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/control/stage-25-acceptance');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({
      organization_id: 'ORG-TEST-001',
      acceptance_id: 'ACCEPTANCE-STAGE25-2',
      rationale: 'Reviewed the compiled specification.',
      evidence_refs: ['control/master-codex-build-spec.json'],
      accepted_at: '2026-08-25T09:00:00Z',
    });
    expect((fetchMock.mock.calls[1][1]?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('loads organization population readiness with season and tenant scope', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({
      organization_id: 'ORG-TEST-001',
      season: '2026',
      status: 'population_incomplete',
      components: [{ component: 'roster', ready: false, required_status: 'validated' }],
      ready_component_count: 0,
      required_component_count: 13,
      blockers: [{ code: 'POPULATION-MISSING', component: 'roster', message: 'No roster package' }],
      owner_review_required: true,
      activation_performed: false,
      production_implementation_allowed: false,
      external_state_changed: false,
    }));

    const readiness = await fetchOrganizationPopulationReadiness(SESSION, '2026');
    expect(readiness.status).toBe('population_incomplete');
    expect(readiness.required_component_count).toBe(13);
    expect(readiness.activation_performed).toBe(false);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/organizations/population-readiness?organization_id=ORG-TEST-001&season=2026');
    expect((fetchMock.mock.calls[0][1]?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('loads and records roster-linked practice attendance', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, options) => {
      if (String(input).startsWith('/v1/practice/attendance?')) return response({ organization_id: 'ORG-TEST-001', practice_id: 'PRACTICE-1', records: [{ id: 'ATTENDANCE-1', player_id: 'PLAYER-1', status: 'limited' }], counts: { present: 0, limited: 1 }, total: 1, limited_or_absent: [{ id: 'ATTENDANCE-1' }], human_review_required: true, production_implementation_allowed: false });
      return response({ id: 'ATTENDANCE-2', player_id: 'PLAYER-2', status: 'present' }, 201);
    });

    const workspace = await fetchPracticeAttendance(SESSION, 'PRACTICE-1');
    expect(workspace.total).toBe(1);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/practice/attendance?organization_id=ORG-TEST-001&practice_id=PRACTICE-1');
    await recordPracticeAttendance(SESSION, { attendanceId: 'ATTENDANCE-2', practiceId: 'PRACTICE-1', playerId: 'PLAYER-2', status: 'present', periodIds: ['PERIOD-1'], note: 'On time', sourceRefs: ['CHECKIN-1'], minutesAvailable: 60 });
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/practice/attendance');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', attendance_id: 'ATTENDANCE-2', practice_id: 'PRACTICE-1', player_id: 'PLAYER-2', status: 'present', minutes_available: 60, period_ids: ['PERIOD-1'] });
  });

  it('serializes intended-versus-actual analytics outcomes with linked evidence', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'OUTCOME-1', status: 'recorded' }, 201));
    await recordAnalyticsOutcome(SESSION, { outcomeId: 'OUTCOME-1', intendedRecordType: 'play_design', intendedRecordId: 'PLAY-1', actualResult: 'partial', successCount: 3, sampleSize: 8, context: { situation: 'third_down' }, evidenceRefs: ['FILM-OBS-1'], linkedPlayId: 'PLAY-1', practiceId: 'PRACTICE-1', filmObservationIds: ['FILM-OBS-1'], notes: 'Execution varied.' });
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/analytics/outcomes');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', outcome_id: 'OUTCOME-1', intended_record_type: 'play_design', intended_record_id: 'PLAY-1', actual_result: 'partial', success_count: 3, sample_size: 8, evidence_refs: ['FILM-OBS-1'], film_observation_ids: ['FILM-OBS-1'] });
  });

  it('serializes the dynamic practice plan into the required backend contract', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'PRACTICE-TEST-1', status: 'draft' }, 201));
    const plan: PracticePlan = {
      id: 'PRACTICE-TEST-1',
      team_context: 'TEAM-TEST',
      season_phase: 'regular_season',
      week_context: 'WEEK-4',
      objective: 'Install pressure answers',
      opponent_priorities: ['sim pressure'],
      periods: [{ id: 'PERIOD-1', type: 'team', objective: 'Pressure answers', owner: 'OC', players: ['offense'], minutes: 12, reps: 10, learning_rationale: 'Decision speed', load_rationale: 'Controlled volume' }],
      staff_available: ['OC'],
      facility_constraints: [],
      load_controls: { max_total_minutes: 60, max_reps_by_position: { QB: 30 } },
      restrictions: [],
      status: 'draft',
    };

    await createPracticePlan(SESSION, plan);

    const [path, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(String(options?.body));
    expect(path).toBe('/v1/practice/plans');
    expect(body.organization_id).toBe('ORG-TEST-001');
    expect(body.practice_id).toBe('PRACTICE-TEST-1');
    expect(body.periods[0].learning_rationale).toBe('Decision speed');
    expect(body.load_controls.max_total_minutes).toBe(60);
  });

  it('serializes delivery packet assembly with canonical audience and week fields', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'DELIVERY-PACKET-1', status: 'blocked' }, 201));

    await createDeliveryPacket(SESSION, { packetId: 'DELIVERY-PACKET-1', packetType: 'coach_packet', week: 'WEEK-1', linkedRecords: ['GAMEPLAN-1'] });

    const [path, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(String(options?.body));
    expect(path).toBe('/v1/delivery/packets');
    expect(body.organization_id).toBe('ORG-TEST-001');
    expect(body.packet_type).toBe('coach_packet');
    expect(body.week).toBe('WEEK-1');
    expect(body.linked_records).toEqual(['GAMEPLAN-1']);
  });

  it('serializes a bounded Film Studio clip with the required media context', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'CLIP-TEST-1', status: 'ready' }, 201));

    await createFilmClip(SESSION, { clipId: 'CLIP-TEST-1', assetId: 'FILM-ASSET-1', startSeconds: 12.25, endSeconds: 18.5, team: 'TEAM-1', opponent: 'OPP-1', situation: '3rd and medium' });

    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/media/clips');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', clip_id: 'CLIP-TEST-1', asset_id: 'FILM-ASSET-1', start_seconds: 12.25, end_seconds: 18.5, situation: '3rd and medium' });
  });

  it('serializes approved managed Film asset registration with source roots and provenance', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'FILM-ASSET-1', status: 'registered' }, 201));

    await registerFilmAsset(SESSION, { assetId: 'FILM-ASSET-1', filePath: 'C:\\approved\\week-1.mp4', durationSeconds: 90, sourceKind: 'licensed_film', sourceRef: 'LICENSE-1', capturedAt: '2026-08-25', teamContext: 'TEAM-1', allowedRoots: ['C:\\approved'] });

    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/media/assets');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', asset_id: 'FILM-ASSET-1', file_path: 'C:\\approved\\week-1.mp4', allowed_roots: ['C:\\approved'], source: { kind: 'licensed_film', ref: 'LICENSE-1' } });
  });

  it('serializes a frame-linked bounded voice note without losing provenance', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'VOICE-NOTE-1', status: 'ready_for_review' }, 201));
    await createFilmVoiceNote(SESSION, { noteId: 'VOICE-NOTE-1', clipId: 'CLIP-1', frameSeconds: 8.25, mimeType: 'audio/webm', audioData: 'data:audio/webm;base64,AAE=', transcript: 'Watch the safety rotation.' });
    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/film/voice-notes');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', note_id: 'VOICE-NOTE-1', clip_id: 'CLIP-1', frame_seconds: 8.25, transcript: 'Watch the safety rotation.' });
  });

  it('serializes Film evidence links to downstream coaching workspaces', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'FILM-OBS-1', status: 'ready_for_review' }, 201));
    await createFilmObservation(SESSION, { id: 'FILM-OBS-1', clip_id: 'CLIP-1', asset_id: 'FILM-ASSET-1', domain: 'coverage', label: 'late rotation', confidence: 'moderate', classification: 'observed', evidence: 'Safety rotates late.', linked_record_refs: [{ record_type: 'scouting', record_id: 'SCOUT-REPORT-1', label: 'Third-down report' }, { record_type: 'game_plan', record_id: 'GAMEPLAN-1', label: 'Weekly answer' }] });
    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/film/observations');
    expect(JSON.parse(String(options?.body))).toMatchObject({ observation: { linked_record_refs: [{ record_type: 'scouting', record_id: 'SCOUT-REPORT-1', label: 'Third-down report' }, { record_type: 'game_plan', record_id: 'GAMEPLAN-1', label: 'Weekly answer' }] } });
  });

  it('queries the server-backed Scouting Tendency Explorer with every selected dimension', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ organization_id: 'ORG-TEST-001', opponent: 'OPP-1', filters: { down: '3', coverage: 'match' }, records: [], total: 0, sample_size_total: 0, review_gate_counts: {}, human_review_required: false, production_implementation_allowed: false }));
    await fetchScoutingTendencies(SESSION, { down: '3', distance: 'all', coverage: 'match' }, 'OPP-1');
    const path = String(fetchMock.mock.calls[0][0]);
    expect(path).toContain('/v1/scouting/tendency-explorer?');
    expect(path).toContain('organization_id=ORG-TEST-001');
    expect(path).toContain('opponent=OPP-1');
    expect(path).toContain('down=3');
    expect(path).toContain('coverage=match');
    expect(path).not.toContain('distance=all');
  });

  it('records inbox decisions only through the guarded governance review endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'DEC-GOV-1', decision: 'returned' }));

    await reviewGovernanceItem(SESSION, {
      collection: 'game_plans',
      recordId: 'GAMEPLAN-1',
      decision: 'returned',
      decisionRef: 'DEC-GOV-1',
      rationale: 'Attach the missing source evidence.',
    });

    const [path, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(String(options?.body));
    expect(path).toBe('/v1/governance/inbox/review');
    expect(body).toMatchObject({
      organization_id: 'ORG-TEST-001',
      collection: 'game_plans',
      record_id: 'GAMEPLAN-1',
      decision: 'returned',
    });
    expect(body.rationale).toContain('missing source evidence');
  });

  it('loads and updates the organization-scoped operations inbox', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const path = String(input);
      if (path.startsWith('/v1/operations/inbox?')) return response({ count: 1, items: [{ id: 'INBOX-1' }], counts: { unread_notifications: 1 } });
      return response({ marked_count: 1, notification_ids: ['NOTIFY-1'] });
    });

    const inbox = await fetchOperationsInbox(SESSION, { category: 'notification', unread_only: 'true' });
    await markOperationsNotificationsRead(SESSION, ['NOTIFY-1']);

    expect(inbox.count).toBe(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('organization_id=ORG-TEST-001');
    expect(String(fetchMock.mock.calls[0][0])).toContain('unread_only=true');
    const [path, options] = fetchMock.mock.calls[1];
    expect(path).toBe('/v1/operations/inbox/notifications/read');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', notification_ids: ['NOTIFY-1'] });
  });

  it('wires collaboration threads, replies, workspace reads, and notification acknowledgement', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const path = String(input);
      if (path.startsWith('/v1/collaboration/workspace?')) return response({ counts: { open_threads: 1, assigned_to_me: 1, unread_notifications: 1, active_presence: 2 }, threads: [], notifications: [], activity: [], presence: [] });
      return response({ id: 'COLLAB-THREAD-1', status: 'open' });
    });

    await fetchCollaborationWorkspace(SESSION, { assigned_to: 'me' });
    await createCollaborationThread(SESSION, { threadId: 'COLLAB-THREAD-1', title: 'Review pressure', body: 'Need an answer.', entityType: 'game_plan', entityId: 'GAMEPLAN-1', deepLink: '/game-plan', assignee: 'COACH-1', mentions: ['ANALYST-1'] });
    await appendCollaborationComment(SESSION, { threadId: 'COLLAB-THREAD-1', commentId: 'COMMENT-1', body: 'Film supports it.', mentions: ['COACH-1'] });
    await markCollaborationNotificationsRead(SESSION, ['NOTIFY-1']);

    expect(String(fetchMock.mock.calls[0][0])).toContain('assigned_to=me');
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/collaboration/threads');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', entity_type: 'game_plan', assignee: 'COACH-1' });
    expect(fetchMock.mock.calls[2][0]).toBe('/v1/collaboration/comments');
    expect(fetchMock.mock.calls[3][0]).toBe('/v1/collaboration/notifications/read');
  });

  it('loads an organization-scoped immutable play version comparison', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({
      design_id: 'PLAY-1',
      base_snapshot_id: 'SNAP-1',
      compare_snapshot_id: 'SNAP-2',
      diff: { changed_fields: ['formation'], players: { added: [], removed: [], changed: [] }, elements: { added: [], removed: [], changed: [] }, timeline_changed: true },
    }));

    const diff = await fetchPlayVersionDiff(SESSION, 'PLAY-1', 'SNAP-1', 'SNAP-2');

    expect(diff.design_id).toBe('PLAY-1');
    const [path, options] = fetchMock.mock.calls[0];
    expect(String(path)).toContain('/v1/playbook/designs/PLAY-1/diff?');
    expect(String(path)).toContain('organization_id=ORG-TEST-001');
    expect(String(path)).toContain('base_snapshot_id=SNAP-1');
    expect(String(path)).toContain('compare_snapshot_id=SNAP-2');
    expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('submits a governed legality override request with evidence and expiry', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'OVERRIDE-1', status: 'pending_owner_approval' }, 201));

    const result = await requestPlayLegalityOverride(SESSION, { designId: 'PLAY-1', issueCode: 'LEGALITY-ELIGIBILITY', rationale: 'Local league rulebook permits this declared exception.', decisionRef: 'DEC-LEGALITY-1', evidenceRefs: ['RULEBOOK-1', 'FILM-CLIP-1'], expiresAt: '2026-09-01T16:00:00.000Z' });

    expect(result).toMatchObject({ id: 'OVERRIDE-1', status: 'pending_owner_approval' });
    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/playbook/designs/legality/override');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'PLAY-1', issue_code: 'LEGALITY-ELIGIBILITY', decision_ref: 'DEC-LEGALITY-1', evidence_refs: ['RULEBOOK-1', 'FILM-CLIP-1'], expires_at: '2026-09-01T16:00:00.000Z' });

    fetchMock.mockImplementation(() => response({ id: 'OVERRIDE-1', status: 'approved' }, 200));
    const approval = await approvePlayLegalityOverride(SESSION, { designId: 'PLAY-1', overrideId: 'OVERRIDE-1', decisionRef: 'APPROVAL-LEGALITY-1' });
    expect(approval).toMatchObject({ id: 'OVERRIDE-1', status: 'approved' });
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/playbook/designs/legality/override/approve');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'PLAY-1', override_id: 'OVERRIDE-1', decision_ref: 'APPROVAL-LEGALITY-1' });
  });

  it('loads a role-filtered teaching view with progressive reveal parameters', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'VIEW-PLAY-1-QB-player', play_id: 'PLAY-1', role: 'QB', mode: 'player', steps: [], quizzes: [], mastery: { attempts: [], summary: {} }, read_reveal: [], players: [], context_players: [], elements: [] }));

    const view = await fetchPlayRoleView(SESSION, 'PLAY-1', 'QB', 'player', 2);

    expect(view.id).toBe('VIEW-PLAY-1-QB-player');
    const [path, options] = fetchMock.mock.calls[0];
    expect(String(path)).toContain('/v1/playbook/designs/PLAY-1/role-view?');
    expect(String(path)).toContain('organization_id=ORG-TEST-001');
    expect(String(path)).toContain('role=QB');
    expect(String(path)).toContain('mode=player');
    expect(String(path)).toContain('step=2');
    expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('records teaching mastery and quiz attempts through guarded endpoints', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input) === '/v1/playbook/designs/mastery') return response({ id: 'MASTERY-1', status: 'mastered' }, 201);
      return response({ quiz_id: 'QUIZ-1', correct: true, score: 1 }, 201);
    });

    await recordPlayMastery(SESSION, { designId: 'PLAY-1', role: 'QB', stepId: 'STEP-1', score: 1, result: 'mastered', practiceRef: 'PRACTICE-1' });
    await submitPlayQuiz(SESSION, { designId: 'PLAY-1', role: 'QB', quizId: 'QUIZ-1', answer: 'read safety', practiceRef: 'PRACTICE-1' });

    expect(fetchMock.mock.calls[0][0]).toBe('/v1/playbook/designs/mastery');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'PLAY-1', role: 'QB', step_id: 'STEP-1', score: 1, result: 'mastered', practice_ref: 'PRACTICE-1' });
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/playbook/designs/quiz');
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'PLAY-1', role: 'QB', quiz_id: 'QUIZ-1', answer: 'read safety', practice_ref: 'PRACTICE-1' });
  });

  it('serializes a guarded branch merge with the current revision', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ status: 'merged', branch_id: 'PLAY-1-BRANCH-A', design: { id: 'PLAY-1' } }));

    const result = await mergePlayBranch(SESSION, 'PLAY-1', 'PLAY-1-BRANCH-A', 7);

    expect(result.status).toBe('merged');
    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/playbook/designs/versioning/merge');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_id: 'PLAY-1', branch_id: 'PLAY-1-BRANCH-A', expected_revision: 7 });
  });

  it('includes evidence dependencies in a game-plan release snapshot request', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'RELEASE-SNAPSHOT-1', status: 'pending_approval', dependency_manifest: { status: 'ready' } }, 201));

    await createGamePlanReleaseSnapshot(SESSION, { snapshotId: 'RELEASE-SNAPSHOT-1', planId: 'GAMEPLAN-1', week: 'WEEK-1', note: 'Ready for staff teaching', artifactRefs: ['PLAY-1', 'SCOUT-1', 'FILM-1'] });

    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/game-plan/release-room/snapshots');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', plan_id: 'GAMEPLAN-1', artifact_refs: ['PLAY-1', 'SCOUT-1', 'FILM-1'] });
  });

  it('serializes multi-play packet exports while preserving the selected artifact mode', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ filename: 'call-sheet.pdf', content_base64: 'AA==', mime_type: 'application/pdf', bytes: 1, sha256: 'hash' }));

    await exportPlayDesign(SESSION, ['PLAY-1', 'PLAY-2', 'PLAY-3'], 'call_sheet', 'pdf', true, 'table', 'QB');

    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/playbook/designs/export');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_ids: ['PLAY-1', 'PLAY-2', 'PLAY-3'], kind: 'call_sheet', format: 'pdf', layout: 'table', black_white: true, role: 'QB' });
  });

  it('serializes export preflight requests without requesting rendered content', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ kind: 'wristband', format: 'pdf', layout: 'wristband_3col', role: 'QB', design_count: 2, can_render: true, validation: { status: 'valid', issues: [] }, source_manifest_hash: 'manifest-hash', source_manifest: [] }));

    const result = await preflightPlayDesignExport(SESSION, ['PLAY-1', 'PLAY-2'], 'wristband', 'pdf', 'wristband_3col', 'QB');

    expect(result.can_render).toBe(true);
    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/v1/playbook/designs/export/preflight');
    expect(JSON.parse(String(options?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', design_ids: ['PLAY-1', 'PLAY-2'], kind: 'wristband', format: 'pdf', layout: 'wristband_3col', role: 'QB' });
  });

  it('opens the authenticated bounded Play Designer event stream from the last sequence', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.resolve(new Response('', { status: 200, headers: { 'Content-Type': 'text/event-stream' } })));

    await fetchPlayCollaborationStream(SESSION, 'PLAY/1', 12);

    const [path, options] = fetchMock.mock.calls[0];
    expect(String(path)).toContain('/v1/playbook/designs/PLAY%2F1/events/stream?');
    expect(String(path)).toContain('organization_id=ORG-TEST-001');
    expect(String(path)).toContain('since=12');
    expect(String(path)).toContain('timeout=25');
    expect((options?.headers as Record<string, string>).Accept).toBe('text/event-stream');
    expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('opens the organization collaboration event stream from the last sequence', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.resolve(new Response('', { status: 200, headers: { 'Content-Type': 'text/event-stream' } })));

    await fetchCollaborationStream(SESSION, 8);

    const [path, options] = fetchMock.mock.calls[0];
    expect(String(path)).toContain('/v1/collaboration/events/stream?');
    expect(String(path)).toContain('organization_id=ORG-TEST-001');
    expect(String(path)).toContain('since=8');
    expect(String(path)).toContain('timeout=25');
    expect((options?.headers as Record<string, string>).Accept).toBe('text/event-stream');
    expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('loads position-filtered canonical practice drills for the install builder', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ organization_id: 'ORG-TEST-001', status: 'ready', drills: [{ id: 'DRILL-1' }] }));

    const drills = await fetchPracticeDrills(SESSION, { position_group: 'QB', search: 'pressure' });

    expect(drills.drills).toHaveLength(1);
    const [path, options] = fetchMock.mock.calls[0];
    expect(String(path)).toContain('/v1/practice/drills?');
    expect(String(path)).toContain('position_group=QB');
    expect(String(path)).toContain('search=pressure');
    expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('serializes non-activating pilot and usability governance workflows', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => response({ id: 'GOVERNANCE-1', status: 'recorded' }, 201));

    await evaluatePilotReadiness(SESSION, {
      waveId: 'WAVE-001',
      pilotUsers: [{ id: 'PLAYER-1', role: 'player' }],
      completedCapabilities: ['CAP-1'],
      acceptanceEvidence: ['TEST-1'],
      featureFlags: { production_recommendations: false },
      rollbackTested: true,
    });
    await selectPilotOrganization(SESSION, { selectionId: 'PILOT-SEL-1', waveId: 'WAVE-001', pilotUsers: [{ id: 'PLAYER-1', role: 'player' }], decisionRef: 'DEC-PILOT-1' });
    await createPilotDeliveryPackage(SESSION, { packageId: 'PILOT-PKG-1', selectionId: 'PILOT-SEL-1', readinessReportId: 'PILOT-READINESS-1', rollback: { status: 'passed', external_state_changed: false } });
    await submitUsabilityFeedback(SESSION, { feedbackId: 'UX-1', sessionId: 'SESSION-1', screenId: 'SCREEN-GOVERNANCE', taskId: 'TASK-1', outcome: 'completed', severity: 'note', feedbackText: 'Clear workflow.', submittedAt: '2026-08-25T12:00:00Z', evidenceRefs: ['BROWSER-1'], accessibilityIssue: false });

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock.mock.calls[0][0]).toBe('/v1/delivery/pilot-readiness');
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', wave_id: 'WAVE-001', rollback_tested: true, feature_flags: { production_recommendations: false } });
    expect(fetchMock.mock.calls[1][0]).toBe('/v1/delivery/pilot-organization');
    expect(fetchMock.mock.calls[2][0]).toBe('/v1/delivery/pilot-package');
    expect(fetchMock.mock.calls[3][0]).toBe('/v1/ux/usability-feedback');
    expect(JSON.parse(String(fetchMock.mock.calls[3][1]?.body))).toMatchObject({ organization_id: 'ORG-TEST-001', feedback_id: 'UX-1', screen_id: 'SCREEN-GOVERNANCE', accessibility_issue: false });
  });
});
