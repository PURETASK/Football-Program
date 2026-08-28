import type {
  ApiEnvelope,
  AdminWorkspaceData,
  AnalyticsWorkspaceData,
  AppSession,
  CollaborationActivity,
  CollaborationThread,
  CollaborationWorkspaceData,
  ExportArtifact,
  ExportPreflight,
  FilmAnnotationSession,
  FilmAsset,
  FilmClip,
  FilmObservation,
  FilmPlaylist,
  FilmVoiceNote,
  FilmWorkspaceData,
  MediaProcessingJobsData,
  MediaProcessingJobDetailData,
  FootballRecord,
  GamePlanData,
  GamePlanThread,
  GamePlanThreadWorkspace,
  GamePlanReleaseRoomData,
  GamePlanReleaseSnapshot,
  GamePlanWorkspaceData,
  GovernanceInboxData,
  OperatorSummary,
  OrganizationContextData,
  OrganizationPopulationReadinessData,
  OperationsInboxData,
  RosterPlayer,
  RosterWorkspaceData,
  DepthChart,
  DeliveryTask,
  DeliveryWorkspaceData,
  PersonnelPackage,
  PilotReadinessData,
  PlayAsset,
  PlayComment,
  PlayDesignDiff,
  PlayDesign,
  PlayDraftValidationReport,
  PlayLegalityReport,
  PlayMasteryResponse,
  PlayMergeResult,
  PlayPresence,
  PlayRoleView,
  PlayTemplate,
  PlayVersionHistory,
  PlayerTodayData,
  PracticePlan,
  PracticeAttendanceRecord,
  PracticeAttendanceWorkspaceData,
  PracticeDrillWorkspaceData,
  PracticeWorkspaceData,
  ScoutingTendencyExplorerData,
  ScoutingWorkspaceData,
  Stage25AcceptanceData,
  StageZeroData,
} from '../types';

export class ApiError extends Error {
  readonly status: number;
  readonly data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  path: string,
  session: AppSession,
  options: { method?: 'GET' | 'POST'; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const response = await fetch(path, {
    method: options.method ?? 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${session.token}`,
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
  const payload = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok) {
    throw new ApiError(payload.error || `Request failed with status ${response.status}`, response.status, payload.data);
  }
  return payload.data;
}

function organizationParams(session: AppSession, values: Record<string, string> = {}): URLSearchParams {
  return new URLSearchParams({ organization_id: session.organizationId, ...values });
}

function organizationBody(session: AppSession, values: Record<string, unknown>): Record<string, unknown> {
  return { organization_id: session.organizationId, ...values };
}

export function fetchOperatorSummary(session: AppSession, signal?: AbortSignal): Promise<OperatorSummary> {
  const params = new URLSearchParams({
    organization_id: session.organizationId,
    include_evals: 'false',
  });
  return request<OperatorSummary>(`/v1/operator/summary?${params}`, session, { signal });
}

export async function fetchPlayDesigns(session: AppSession, signal?: AbortSignal): Promise<PlayDesign[]> {
  const params = organizationParams(session);
  const payload = await request<{ designs: PlayDesign[] }>(`/v1/playbook/designs?${params}`, session, { signal });
  return payload.designs ?? [];
}

export async function fetchPlayAssets(session: AppSession, context?: Pick<PlayDesign, 'unit' | 'formation' | 'personnel' | 'rule_profile'>, signal?: AbortSignal): Promise<PlayAsset[]> {
  const params = organizationParams(session, {
    ...(context?.unit ? { unit: context.unit } : {}),
    ...(context?.formation ? { context_formation: context.formation } : {}),
    ...(context?.personnel ? { personnel: context.personnel } : {}),
    ...(context?.rule_profile ? { rule_profile: context.rule_profile } : {}),
  });
  const payload = await request<{ assets: PlayAsset[] }>(`/v1/playbook/designs/assets?${params}`, session, { signal });
  return payload.assets ?? [];
}

export async function fetchPlayTemplates(session: AppSession, signal?: AbortSignal): Promise<PlayTemplate[]> {
  const params = organizationParams(session);
  const payload = await request<{ templates: PlayTemplate[] }>(`/v1/playbook/designs/templates?${params}`, session, { signal });
  return payload.templates ?? [];
}

export function createPlayTemplate(session: AppSession, input: { designId: string; name: string; description?: string; tags?: string[]; templateKind?: string; layer?: string; elementIds?: string[]; parentTemplateId?: string }): Promise<PlayTemplate> {
  return request<PlayTemplate>('/v1/playbook/designs/templates', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_id: input.designId,
      name: input.name,
      description: input.description ?? '',
      tags: input.tags ?? [],
      template_kind: input.templateKind ?? 'custom',
      layer: input.layer ?? 'complete_call',
      ...(input.elementIds?.length ? { element_ids: input.elementIds } : {}),
      ...(input.parentTemplateId ? { parent_template_id: input.parentTemplateId } : {}),
    }),
  });
}

export interface PlayVariantBatchReview { ready: boolean; ready_count: number; blocked_count: number; items: Array<{ design_id: string; state: string; ready: boolean; validation_status?: string; lifecycle?: string; approval_state?: string; reasons: string[] }> }
export interface PlayVariantBatchResult { id: string; source_design_id: string; variant_ids: string[]; variants: PlayDesign[]; count: number; status: string; human_review_required?: boolean; review?: PlayVariantBatchReview; release_bundle?: Pick<PlayVariantReleaseBundle, 'id' | 'status' | 'immutable' | 'manifest_hash' | 'created_at' | 'production_activation'> & { integrity_valid?: boolean } }

export interface PlayVariantBatchHistory { organization_id: string; source_design_id?: string | null; batches: PlayVariantBatchResult[]; count: number }

export function fetchPlayVariantBatches(session: AppSession, sourceDesignId?: string, signal?: AbortSignal): Promise<PlayVariantBatchHistory> {
  const params = new URLSearchParams({ organization_id: session.organizationId });
  if (sourceDesignId) params.set('source_design_id', sourceDesignId);
  return request<PlayVariantBatchHistory>(`/v1/playbook/designs/variants?${params}`, session, { signal });
}

export function createPlayVariants(session: AppSession, input: { designId: string; variants: Array<{ label: string; patch: Partial<Pick<PlayDesign, 'formation' | 'front' | 'coverage' | 'personnel' | 'concept' | 'rule_profile'>>; assignment_patches?: Array<{ element_id: string; patch: Record<string, unknown> }> }>; batchId?: string }): Promise<PlayVariantBatchResult> {
  return request('/v1/playbook/designs/variants', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: input.designId, variants: input.variants, ...(input.batchId ? { batch_id: input.batchId } : {}) }),
  });
}

export function requestPlayVariantBatchReview(session: AppSession, batchId: string, decisionRef: string): Promise<PlayVariantBatchResult> {
  return request<PlayVariantBatchResult>('/v1/playbook/designs/variants/request-review', session, {
    method: 'POST',
    body: organizationBody(session, { batch_id: batchId, decision_ref: decisionRef }),
  });
}

export function approvePlayVariantBatchReview(session: AppSession, batchId: string, decisionRef: string): Promise<PlayVariantBatchResult> {
  return request<PlayVariantBatchResult>('/v1/playbook/designs/variants/approve-review', session, {
    method: 'POST',
    body: organizationBody(session, { batch_id: batchId, decision_ref: decisionRef }),
  });
}

export interface PlayVariantReleaseBundle {
  id: string;
  organization_id: string;
  batch_id: string;
  status: 'frozen' | string;
  immutable: boolean;
  manifest_hash: string;
  created_at: string;
  production_activation: boolean;
}

export function createPlayVariantReleaseBundle(session: AppSession, batchId: string, decisionRef: string): Promise<PlayVariantReleaseBundle> {
  return request<PlayVariantReleaseBundle>('/v1/playbook/designs/variants/create-release-bundle', session, {
    method: 'POST',
    body: organizationBody(session, { batch_id: batchId, decision_ref: decisionRef }),
  });
}

export function fetchPlayVariantReleaseBundle(session: AppSession, bundleId: string, signal?: AbortSignal): Promise<PlayVariantReleaseBundle & { integrity: { valid: boolean; expected_manifest_hash?: string; declared_manifest_hash?: string } }> {
  return request(`/v1/playbook/designs/variants/release-bundles/${encodeURIComponent(bundleId)}?organization_id=${encodeURIComponent(session.organizationId)}`, session, { signal });
}

export function savePlayDesign(session: AppSession, design: PlayDesign, expectedRevision?: number): Promise<PlayDesign> {
  return request<PlayDesign>('/v1/playbook/designs', session, {
    method: 'POST',
    body: organizationBody(session, { design, expected_revision: expectedRevision }),
  });
}

export function validatePlayDesignDraft(session: AppSession, design: PlayDesign, signal?: AbortSignal): Promise<PlayDraftValidationReport> {
  return request<PlayDraftValidationReport>('/v1/playbook/designs/validate', session, {
    method: 'POST',
    body: organizationBody(session, { design }),
    signal,
  });
}

export function requestPlayReview(session: AppSession, designId: string, decisionRef: string): Promise<PlayDesign> {
  return request<PlayDesign>('/v1/playbook/designs/request-review', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, decision_ref: decisionRef }),
  });
}

export function publishPlayDesign(session: AppSession, designId: string, decisionRef: string): Promise<PlayDesign> {
  return request<PlayDesign>('/v1/playbook/designs/publish', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, decision_ref: decisionRef }),
  });
}

export function branchPlayDesign(session: AppSession, designId: string, branchId: string): Promise<PlayDesign> {
  return request<PlayDesign>('/v1/playbook/designs/branch', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, branch_id: branchId }),
  });
}

export function mergePlayBranch(session: AppSession, designId: string, branchId: string, expectedRevision?: number): Promise<PlayMergeResult> {
  return request<PlayMergeResult>('/v1/playbook/designs/versioning/merge', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, branch_id: branchId, expected_revision: expectedRevision }),
  });
}

export function fetchPlayVersions(session: AppSession, designId: string, signal?: AbortSignal): Promise<PlayVersionHistory> {
  const params = organizationParams(session);
  return request<PlayVersionHistory>(`/v1/playbook/designs/${encodeURIComponent(designId)}/versions?${params}`, session, { signal });
}

export function fetchPlayVersionDiff(session: AppSession, designId: string, baseSnapshotId: string, compareSnapshotId: string, signal?: AbortSignal): Promise<PlayDesignDiff> {
  const params = organizationParams(session, { base_snapshot_id: baseSnapshotId, compare_snapshot_id: compareSnapshotId });
  return request<PlayDesignDiff>(`/v1/playbook/designs/${encodeURIComponent(designId)}/diff?${params}`, session, { signal });
}

export function fetchPlayLegality(session: AppSession, designId: string, signal?: AbortSignal): Promise<PlayLegalityReport> {
  const params = organizationParams(session);
  return request<PlayLegalityReport>(`/v1/playbook/designs/${encodeURIComponent(designId)}/legality?${params}`, session, { signal });
}

export function requestPlayLegalityOverride(session: AppSession, values: {
  designId: string;
  issueCode: string;
  rationale: string;
  decisionRef: string;
  evidenceRefs: string[];
  expiresAt: string;
}): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/v1/playbook/designs/legality/override', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_id: values.designId,
      issue_code: values.issueCode,
      rationale: values.rationale,
      decision_ref: values.decisionRef,
      evidence_refs: values.evidenceRefs,
      expires_at: values.expiresAt,
    }),
  });
}

export function approvePlayLegalityOverride(session: AppSession, values: { designId: string; overrideId: string; decisionRef: string }): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/v1/playbook/designs/legality/override/approve', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: values.designId, override_id: values.overrideId, decision_ref: values.decisionRef }),
  });
}

export function fetchPlayRoleView(
  session: AppSession,
  designId: string,
  role: string,
  mode: 'player' | 'position_group' | 'coach' = 'player',
  step?: number,
  signal?: AbortSignal,
): Promise<PlayRoleView> {
  const values: Record<string, string> = { role, mode };
  if (step !== undefined) values.step = String(Math.max(0, Math.floor(step)));
  const params = organizationParams(session, values);
  return request<PlayRoleView>(`/v1/playbook/designs/${encodeURIComponent(designId)}/role-view?${params}`, session, { signal });
}

export function fetchPlayMastery(session: AppSession, designId: string, role?: string, userId?: string, signal?: AbortSignal): Promise<PlayMasteryResponse> {
  const values: Record<string, string> = {};
  if (role) values.role = role;
  if (userId) values.user_id = userId;
  const params = organizationParams(session, values);
  return request<PlayMasteryResponse>(`/v1/playbook/designs/${encodeURIComponent(designId)}/mastery?${params}`, session, { signal });
}

export function recordPlayMastery(session: AppSession, values: {
  designId: string;
  role: string;
  stepId: string;
  score: number;
  result?: 'attempted' | 'passed' | 'mastered' | 'needs_review';
  practiceRef?: string;
  notes?: string;
  attemptId?: string;
  userId?: string;
}): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/v1/playbook/designs/mastery', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_id: values.designId,
      role: values.role,
      step_id: values.stepId,
      score: values.score,
      result: values.result ?? 'mastered',
      practice_ref: values.practiceRef,
      notes: values.notes ?? '',
      attempt_id: values.attemptId,
      user_id: values.userId,
    }),
  });
}

export function submitPlayQuiz(session: AppSession, values: {
  designId: string;
  role: string;
  quizId: string;
  answer: unknown;
  practiceRef?: string;
  userId?: string;
}): Promise<{ quiz_id?: string; correct?: boolean; score?: number; mastery?: Record<string, unknown> }> {
  return request<{ quiz_id?: string; correct?: boolean; score?: number; mastery?: Record<string, unknown> }>('/v1/playbook/designs/quiz', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_id: values.designId,
      role: values.role,
      quiz_id: values.quizId,
      answer: values.answer,
      practice_ref: values.practiceRef,
      user_id: values.userId,
    }),
  });
}

export async function fetchPlayComments(session: AppSession, designId: string, signal?: AbortSignal): Promise<PlayComment[]> {
  const params = organizationParams(session);
  const payload = await request<PlayComment[] | { comments: PlayComment[] }>(
    `/v1/playbook/designs/${encodeURIComponent(designId)}/comments?${params}`,
    session,
    { signal },
  );
  return Array.isArray(payload) ? payload : payload.comments ?? [];
}

export function addPlayComment(session: AppSession, designId: string, text: string, elementId?: string): Promise<PlayComment> {
  return request<PlayComment>('/v1/playbook/designs/comments', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, text, element_id: elementId }),
  });
}

export async function fetchPlayPresence(session: AppSession, designId: string, signal?: AbortSignal): Promise<PlayPresence[]> {
  const params = organizationParams(session);
  const payload = await request<{ presence: PlayPresence[] }>(
    `/v1/playbook/designs/${encodeURIComponent(designId)}/presence?${params}`,
    session,
    { signal },
  );
  return payload.presence ?? [];
}

export function updatePlayPresence(
  session: AppSession,
  designId: string,
  sessionId: string,
  cursor?: { x: number; y: number },
): Promise<PlayPresence> {
  return request<PlayPresence>('/v1/playbook/designs/presence', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_id: designId,
      session_id: sessionId,
      display_name: session.subject ?? session.role,
      color: '#4cd6fa',
      cursor,
    }),
  });
}

export function leavePlayPresence(session: AppSession, designId: string, sessionId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/v1/playbook/designs/presence/leave', session, {
    method: 'POST',
    body: organizationBody(session, { design_id: designId, session_id: sessionId }),
  });
}

export function fetchPlayCollaborationStream(session: AppSession, designId: string, since = 0, signal?: AbortSignal): Promise<Response> {
  const params = organizationParams(session, { since: String(Math.max(0, since)), timeout: '25' });
  return fetch(`/v1/playbook/designs/${encodeURIComponent(designId)}/events/stream?${params}`, {
    headers: { Accept: 'text/event-stream', Authorization: `Bearer ${session.token}` },
    signal,
  });
}

export function exportPlayDesign(
  session: AppSession,
  designIds: string[],
  kind: string,
  format: string,
  blackWhite = false,
  layout = 'single',
  role?: string,
): Promise<ExportArtifact> {
  return request<ExportArtifact>('/v1/playbook/designs/export', session, {
    method: 'POST',
    body: organizationBody(session, {
      design_ids: designIds,
      kind,
      format,
      black_white: blackWhite,
      layout,
      role: role && role !== 'coach' ? role : undefined,
      branding: { team_name: 'Team Playbook', organization_name: 'NFL FIDOS' },
    }),
  });
}

export function preflightPlayDesignExport(
  session: AppSession,
  designIds: string[],
  kind: string,
  format: string,
  layout = 'single',
  role?: string,
  signal?: AbortSignal,
): Promise<ExportPreflight> {
  return request<ExportPreflight>('/v1/playbook/designs/export/preflight', session, {
    method: 'POST',
    signal,
    body: organizationBody(session, {
      design_ids: designIds,
      kind,
      format,
      layout,
      role: role && role !== 'coach' ? role : undefined,
    }),
  });
}

export async function fetchFilmWorkspace(session: AppSession, query = '', signal?: AbortSignal): Promise<FilmWorkspaceData> {
  const params = organizationParams(session);
  const searchParams = organizationParams(session, query ? { query } : {});
  const [assets, clips, observations, playlists, sessions, voiceNotes] = await Promise.all([
    request<{ assets: FilmWorkspaceData['assets'] }>(`/v1/media/assets?${params}`, session, { signal }),
    request<{ clips: FilmWorkspaceData['clips'] }>(`/v1/media/clips?${params}`, session, { signal }),
    request<{ results: FilmObservation[] }>(`/v1/film/search?${searchParams}`, session, { signal }),
    request<{ playlists: FilmPlaylist[] }>(`/v1/film/playlists?${params}`, session, { signal }),
    request<{ sessions: FilmAnnotationSession[] }>(`/v1/film/annotation-sessions?${params}`, session, { signal }),
    request<{ voice_notes: FilmVoiceNote[] }>(`/v1/film/voice-notes?${params}`, session, { signal }),
  ]);
  return {
    assets: assets.assets ?? [],
    clips: clips.clips ?? [],
    observations: observations.results ?? [],
    playlists: playlists.playlists ?? [],
    sessions: sessions.sessions ?? [],
    voice_notes: voiceNotes.voice_notes ?? [],
  };
}

export async function fetchMediaProcessingJobs(session: AppSession, status = '', signal?: AbortSignal): Promise<MediaProcessingJobsData> {
  const params = new URLSearchParams({ organization_id: session.organizationId });
  if (status) params.set('status', status);
  return request<MediaProcessingJobsData>(`/v1/media/jobs?${params}`, session, { signal });
}

export async function fetchMediaProcessingJob(session: AppSession, jobId: string, signal?: AbortSignal): Promise<MediaProcessingJobDetailData> {
  const params = new URLSearchParams({ organization_id: session.organizationId });
  return request<MediaProcessingJobDetailData>(`/v1/media/jobs/${encodeURIComponent(jobId)}?${params}`, session, { signal });
}

export function createFilmPlaylist(session: AppSession, values: {
  playlistId: string;
  name: string;
  purpose: string;
  clipIds: string[];
  accessRoles: string[];
}): Promise<FilmPlaylist> {
  return request<FilmPlaylist>('/v1/film/playlists', session, {
    method: 'POST',
    body: organizationBody(session, {
      playlist_id: values.playlistId,
      name: values.name,
      purpose: values.purpose,
      clip_ids: values.clipIds,
      filters: {},
      access_roles: values.accessRoles,
    }),
  });
}

export function registerFilmAsset(session: AppSession, values: {
  assetId: string;
  filePath: string;
  durationSeconds: number;
  sourceKind: string;
  sourceRef: string;
  capturedAt: string;
  teamContext: string;
  allowedRoots: string[];
}): Promise<FilmAsset> {
  return request<FilmAsset>('/v1/media/assets', session, {
    method: 'POST',
    body: organizationBody(session, {
      asset_id: values.assetId,
      file_path: values.filePath,
      duration_seconds: values.durationSeconds,
      source: { kind: values.sourceKind, ref: values.sourceRef },
      captured_at: values.capturedAt,
      team_context: values.teamContext,
      allowed_roots: values.allowedRoots,
    }),
  });
}

export function createFilmAnnotationSession(session: AppSession, values: {
  sessionId: string;
  clipId: string;
  allowedDomains: string[];
  sourceRefs: string[];
}): Promise<FilmAnnotationSession> {
  return request<FilmAnnotationSession>('/v1/film/annotation-sessions', session, {
    method: 'POST',
    body: organizationBody(session, {
      session_id: values.sessionId,
      clip_id: values.clipId,
      allowed_domains: values.allowedDomains,
      source_refs: values.sourceRefs,
    }),
  });
}

export function createFilmObservation(session: AppSession, observation: FilmObservation): Promise<FilmObservation> {
  return request<FilmObservation>('/v1/film/observations', session, {
    method: 'POST',
    body: organizationBody(session, { observation }),
  });
}

export function createFilmClip(session: AppSession, values: {
  clipId: string;
  assetId: string;
  startSeconds: number;
  endSeconds: number;
  team: string;
  opponent: string;
  situation: string;
}): Promise<FilmClip> {
  return request<FilmClip>('/v1/media/clips', session, {
    method: 'POST',
    body: organizationBody(session, {
      clip_id: values.clipId,
      asset_id: values.assetId,
      start_seconds: values.startSeconds,
      end_seconds: values.endSeconds,
      team: values.team,
      opponent: values.opponent,
      situation: values.situation,
    }),
  });
}

export function createFilmVoiceNote(session: AppSession, values: {
  noteId: string;
  clipId: string;
  frameSeconds: number;
  mimeType: string;
  audioData: string;
  transcript: string;
  accessRoles?: string[];
}): Promise<FilmVoiceNote> {
  return request<FilmVoiceNote>('/v1/film/voice-notes', session, {
    method: 'POST',
    body: organizationBody(session, {
      note_id: values.noteId,
      clip_id: values.clipId,
      frame_seconds: values.frameSeconds,
      mime_type: values.mimeType,
      audio_data: values.audioData,
      transcript: values.transcript,
      access_roles: values.accessRoles ?? ['program_owner', 'coach_staff', 'analyst'],
    }),
  });
}

export function appendFilmAnnotation(session: AppSession, sessionId: string, observation: FilmObservation): Promise<FilmAnnotationSession> {
  return request<FilmAnnotationSession>(`/v1/film/annotation-sessions/${encodeURIComponent(sessionId)}/annotations`, session, {
    method: 'POST',
    body: organizationBody(session, { observation }),
  });
}

export function fetchPracticeWorkspace(session: AppSession, week = '', signal?: AbortSignal): Promise<PracticeWorkspaceData> {
  const params = organizationParams(session, week ? { week } : {});
  return request<PracticeWorkspaceData>(`/v1/practice/workspace?${params}`, session, { signal });
}

export function fetchPracticeAttendance(session: AppSession, practiceId = '', signal?: AbortSignal): Promise<PracticeAttendanceWorkspaceData> {
  const params = organizationParams(session, practiceId ? { practice_id: practiceId } : {});
  return request<PracticeAttendanceWorkspaceData>(`/v1/practice/attendance?${params}`, session, { signal });
}

export function recordPracticeAttendance(session: AppSession, values: {
  attendanceId: string;
  practiceId: string;
  playerId: string;
  status: string;
  minutesAvailable?: number;
  periodIds: string[];
  note: string;
  sourceRefs: string[];
}): Promise<PracticeAttendanceRecord> {
  return request<PracticeAttendanceRecord>('/v1/practice/attendance', session, {
    method: 'POST',
    body: organizationBody(session, {
      attendance_id: values.attendanceId,
      practice_id: values.practiceId,
      player_id: values.playerId,
      status: values.status,
      minutes_available: values.minutesAvailable,
      period_ids: values.periodIds,
      note: values.note,
      source_refs: values.sourceRefs,
    }),
  });
}

export async function fetchPracticeDrills(session: AppSession, filters: Record<string, string> = {}, signal?: AbortSignal): Promise<PracticeDrillWorkspaceData> {
  const params = organizationParams(session, filters);
  const payload = await request<PracticeDrillWorkspaceData>(`/v1/practice/drills?${params}`, session, { signal });
  return { ...payload, drills: payload.drills ?? [] };
}

export function createPracticePlan(session: AppSession, plan: PracticePlan): Promise<PracticePlan> {
  return request<PracticePlan>('/v1/practice/plans', session, {
    method: 'POST',
    body: organizationBody(session, {
      practice_id: plan.id,
      team_context: plan.team_context,
      season_phase: plan.season_phase,
      week_context: plan.week_context,
      objective: plan.objective,
      opponent_priorities: plan.opponent_priorities ?? [],
      periods: plan.periods ?? [],
      staff_available: plan.staff_available ?? [],
      facility_constraints: plan.facility_constraints ?? [],
      load_controls: plan.load_controls ?? {},
      restrictions: plan.restrictions ?? [],
      roster_ids: plan.roster_ids ?? [],
      install_items: plan.install_items ?? [],
      attendance_policy: plan.attendance_policy ?? 'staff_recorded',
      practice_card_preferences: plan.practice_card_preferences ?? {},
    }),
  });
}

export function fetchScoutingWorkspace(session: AppSession, opponent = '', signal?: AbortSignal): Promise<ScoutingWorkspaceData> {
  const params = organizationParams(session, opponent ? { opponent } : {});
  return request<ScoutingWorkspaceData>(`/v1/scouting/workspace?${params}`, session, { signal });
}

export function fetchScoutingTendencies(session: AppSession, filters: Record<string, string>, opponent = '', signal?: AbortSignal): Promise<ScoutingTendencyExplorerData> {
  const selected = Object.fromEntries(Object.entries(filters).filter(([, value]) => value && value !== 'all'));
  const params = organizationParams(session, opponent ? { opponent, ...selected } : selected);
  return request<ScoutingTendencyExplorerData>(`/v1/scouting/tendency-explorer?${params}`, session, { signal });
}

export function createScoutingReport(session: AppSession, report: FootballRecord): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/scouting/reports', session, {
    method: 'POST',
    body: organizationBody(session, { report }),
  });
}

export async function fetchGamePlanData(session: AppSession, week = '', signal?: AbortSignal): Promise<GamePlanData> {
  const workspaceParams = organizationParams(session, week ? { week } : {});
  const threadParams = organizationParams(session);
  const [workspace, collaboration] = await Promise.all([
    request<GamePlanWorkspaceData>(`/v1/game-plan/workspace?${workspaceParams}`, session, { signal }),
    request<GamePlanThreadWorkspace>(`/v1/game-plan/threads?${threadParams}`, session, { signal }),
  ]);
  return { workspace, collaboration };
}

export function fetchGamePlanReleaseRoom(session: AppSession, week = '', signal?: AbortSignal): Promise<GamePlanReleaseRoomData> {
  const params = organizationParams(session, week ? { week } : {});
  return request<GamePlanReleaseRoomData>(`/v1/game-plan/release-room?${params}`, session, { signal });
}

export function fetchAnalyticsWorkspace(session: AppSession, situation = '', signal?: AbortSignal): Promise<AnalyticsWorkspaceData> {
  const params = organizationParams(session, situation ? { situation } : {});
  return request<AnalyticsWorkspaceData>(`/v1/analytics/workspace?${params}`, session, { signal });
}

export function createAnalyticsReport(session: AppSession, values: { reportId: string; audience: string; metricObservations: FootballRecord[]; context: Record<string, unknown>; caveats: string[] }): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/analytics/reports', session, {
    method: 'POST',
    body: organizationBody(session, { report_id: values.reportId, audience: values.audience, metric_observations: values.metricObservations, context: values.context, caveats: values.caveats }),
  });
}

export function recordAnalyticsOutcome(session: AppSession, values: {
  outcomeId: string;
  intendedRecordType: string;
  intendedRecordId: string;
  actualResult: string;
  successCount: number;
  sampleSize: number;
  context: Record<string, unknown>;
  evidenceRefs: string[];
  linkedPlayId?: string;
  linkedAssignmentId?: string;
  teachingStepId?: string;
  responsibilityPhase?: string;
  practiceId?: string;
  filmObservationIds: string[];
  gamePlanId?: string;
  notes: string;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/analytics/outcomes', session, {
    method: 'POST',
    body: organizationBody(session, {
      outcome_id: values.outcomeId,
      intended_record_type: values.intendedRecordType,
      intended_record_id: values.intendedRecordId,
      actual_result: values.actualResult,
      success_count: values.successCount,
      sample_size: values.sampleSize,
      context: values.context,
      evidence_refs: values.evidenceRefs,
      linked_play_id: values.linkedPlayId,
      linked_assignment_id: values.linkedAssignmentId,
      teaching_step_id: values.teachingStepId,
      responsibility_phase: values.responsibilityPhase,
      practice_id: values.practiceId,
      film_observation_ids: values.filmObservationIds,
      game_plan_id: values.gamePlanId,
      notes: values.notes,
    }),
  });
}

export function fetchDeliveryWorkspace(session: AppSession, week = '', signal?: AbortSignal): Promise<DeliveryWorkspaceData> {
  const params = organizationParams(session, week ? { week } : {});
  return request<DeliveryWorkspaceData>(`/v1/delivery/workspace?${params}`, session, { signal });
}

export function createDeliveryTask(session: AppSession, values: { taskId: string; title: string; category: string; owner: string; dueAt: string; week: string; linkedRecords: string[]; priority: string }): Promise<DeliveryTask> {
  return request<DeliveryTask>('/v1/delivery/tasks', session, { method: 'POST', body: organizationBody(session, { task_id: values.taskId, title: values.title, category: values.category, owner: values.owner, due_at: values.dueAt, week: values.week, linked_records: values.linkedRecords, priority: values.priority }) });
}

export function createDeliveryPacket(session: AppSession, values: { packetId: string; packetType: string; week: string; linkedRecords: string[] }): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/delivery/packets', session, { method: 'POST', body: organizationBody(session, { packet_id: values.packetId, packet_type: values.packetType, week: values.week, linked_records: values.linkedRecords }) });
}

export function completeDeliveryTask(session: AppSession, taskId: string, note = ''): Promise<DeliveryTask> {
  return request<DeliveryTask>('/v1/delivery/tasks/complete', session, { method: 'POST', body: organizationBody(session, { task_id: taskId, note }) });
}

export function createGamePlanReleaseSnapshot(session: AppSession, values: { snapshotId: string; planId: string; week: string; note: string; artifactRefs?: string[] }): Promise<GamePlanReleaseSnapshot> {
  return request<GamePlanReleaseSnapshot>('/v1/game-plan/release-room/snapshots', session, {
    method: 'POST',
    body: organizationBody(session, { snapshot_id: values.snapshotId, plan_id: values.planId, week: values.week, note: values.note, artifact_refs: values.artifactRefs ?? [] }),
  });
}

export function approveGamePlanReleaseSnapshot(session: AppSession, snapshotId: string, decisionRef: string): Promise<GamePlanReleaseSnapshot> {
  return request<GamePlanReleaseSnapshot>('/v1/game-plan/release-room/approve', session, {
    method: 'POST',
    body: organizationBody(session, { snapshot_id: snapshotId, decision_ref: decisionRef }),
  });
}

export function rollbackGamePlanReleaseSnapshot(session: AppSession, snapshotId: string, decisionRef: string): Promise<GamePlanReleaseSnapshot> {
  return request<GamePlanReleaseSnapshot>('/v1/game-plan/release-room/rollback', session, {
    method: 'POST',
    body: organizationBody(session, { snapshot_id: snapshotId, decision_ref: decisionRef }),
  });
}

export function createGamePlanThread(session: AppSession, values: {
  threadId: string;
  planId: string;
  week: string;
  topic: string;
  comment: string;
  evidenceRefs: string[];
}): Promise<GamePlanThread> {
  return request<GamePlanThread>('/v1/game-plan/threads', session, {
    method: 'POST',
    body: organizationBody(session, {
      thread_id: values.threadId,
      plan_id: values.planId,
      week: values.week,
      topic: values.topic,
      comment: values.comment,
      evidence_refs: values.evidenceRefs,
    }),
  });
}

export function commentOnGamePlanThread(session: AppSession, values: {
  threadId: string;
  commentId: string;
  comment: string;
  evidenceRefs: string[];
}): Promise<GamePlanThread> {
  return request<GamePlanThread>('/v1/game-plan/threads/comments', session, {
    method: 'POST',
    body: organizationBody(session, {
      thread_id: values.threadId,
      comment_id: values.commentId,
      comment: values.comment,
      evidence_refs: values.evidenceRefs,
    }),
  });
}

export function resolveGamePlanThread(session: AppSession, values: {
  threadId: string;
  decision: 'accepted' | 'deferred' | 'rejected';
  decisionRef: string;
  rationale: string;
}): Promise<GamePlanThread> {
  return request<GamePlanThread>('/v1/game-plan/threads/resolve', session, {
    method: 'POST',
    body: organizationBody(session, {
      thread_id: values.threadId,
      decision: values.decision,
      decision_ref: values.decisionRef,
      rationale: values.rationale,
    }),
  });
}

export function fetchPlayerToday(session: AppSession, playerId: string, signal?: AbortSignal): Promise<PlayerTodayData> {
  const params = organizationParams(session, { player_id: playerId });
  return request<PlayerTodayData>(`/v1/player/today?${params}`, session, { signal });
}

export function createPlayerAssignment(session: AppSession, values: {
  assignmentId: string;
  playerId: string;
  title: string;
  assignmentType: string;
  artifactId: string;
  dueDate?: string;
  sourceRefs: string[];
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/player/assignments', session, {
    method: 'POST',
    body: organizationBody(session, {
      assignment_id: values.assignmentId,
      player_id: values.playerId,
      title: values.title,
      assignment_type: values.assignmentType,
      artifact_id: values.artifactId,
      due_date: values.dueDate,
      source_refs: values.sourceRefs,
    }),
  });
}

export async function fetchAdminWorkspace(session: AppSession, signal?: AbortSignal): Promise<AdminWorkspaceData> {
  const params = organizationParams(session);
  const [organization, sourcePayload, stageZero, pilot, pilotOrganization, pilotPackage, usability] = await Promise.all([
    request<OrganizationContextData>(`/v1/organizations/context?${params}`, session, { signal }),
    request<{ sources: FootballRecord[] }>(`/v1/sources?${params}`, session, { signal }),
    request<StageZeroData>(`/v1/control/stage-0-approval?${params}`, session, { signal }),
    request<PilotReadinessData>(`/v1/delivery/pilot-readiness?${params}`, session, { signal }),
    request<{ selections: FootballRecord[] }>(`/v1/delivery/pilot-organization?${params}`, session, { signal }),
    request<{ packages: FootballRecord[] }>(`/v1/delivery/pilot-package?${params}`, session, { signal }),
    request<{ feedback: FootballRecord[] }>(`/v1/ux/usability-feedback?${params}`, session, { signal }),
  ]);
  return {
    organization,
    sources: sourcePayload.sources ?? [],
    stageZero,
    pilot,
    pilotSelections: pilotOrganization.selections ?? [],
    pilotPackages: pilotPackage.packages ?? [],
    usabilityFeedback: usability.feedback ?? [],
  };
}

export function fetchStage25Acceptance(session: AppSession, signal?: AbortSignal): Promise<Stage25AcceptanceData> {
  const params = organizationParams(session);
  return request<Stage25AcceptanceData>(`/v1/control/stage-25-acceptance?${params}`, session, { signal });
}

export function fetchOrganizationPopulationReadiness(session: AppSession, season = '2026', signal?: AbortSignal): Promise<OrganizationPopulationReadinessData> {
  const params = organizationParams(session, { season });
  return request<OrganizationPopulationReadinessData>(`/v1/organizations/population-readiness?${params}`, session, { signal });
}

export function approveOrganizationContext(session: AppSession, decisionRef: string): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/organizations/context/approve', session, {
    method: 'POST',
    body: organizationBody(session, { decision_ref: decisionRef }),
  });
}

export function registerKnowledgeSource(session: AppSession, values: {
  sourceId: string;
  tier: string;
  kind: string;
  uri: string;
  capturedAt: string;
  effectivePeriod: string;
  citationLocation: string;
  allowedDomains: string[];
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/sources', session, {
    method: 'POST',
    body: organizationBody(session, {
      source_id: values.sourceId,
      tier: values.tier,
      kind: values.kind,
      uri: values.uri,
      captured_at: values.capturedAt,
      effective_period: values.effectivePeriod,
      citation_location: values.citationLocation,
      allowed_domains: values.allowedDomains,
    }),
  });
}

export function refreshKnowledgeSource(session: AppSession, sourceId: string): Promise<FootballRecord> {
  return request<FootballRecord>(`/v1/sources/${encodeURIComponent(sourceId)}/refresh`, session, {
    method: 'POST',
    body: organizationBody(session, {}),
  });
}

export function submitStageZeroApproval(session: AppSession, values: {
  approvalId: string;
  rationale: string;
  evidenceRefs: string[];
  approvedAt: string;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/control/stage-0-approval', session, {
    method: 'POST',
    body: organizationBody(session, {
      approval_id: values.approvalId,
      rationale: values.rationale,
      evidence_refs: values.evidenceRefs,
      approved_at: values.approvedAt,
    }),
  });
}

export function submitStage25Acceptance(session: AppSession, values: {
  acceptanceId: string;
  rationale: string;
  evidenceRefs: string[];
  acceptedAt: string;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/control/stage-25-acceptance', session, {
    method: 'POST',
    body: organizationBody(session, {
      acceptance_id: values.acceptanceId,
      rationale: values.rationale,
      evidence_refs: values.evidenceRefs,
      accepted_at: values.acceptedAt,
    }),
  });
}

export function evaluatePilotReadiness(session: AppSession, values: {
  waveId: string;
  pilotUsers: Array<Record<string, unknown>>;
  completedCapabilities: string[];
  acceptanceEvidence: string[];
  featureFlags: Record<string, unknown>;
  rollbackTested: boolean;
  ownerApproval?: Record<string, unknown>;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/delivery/pilot-readiness', session, {
    method: 'POST',
    body: organizationBody(session, {
      wave_id: values.waveId,
      pilot_users: values.pilotUsers,
      completed_capabilities: values.completedCapabilities,
      acceptance_evidence: values.acceptanceEvidence,
      feature_flags: values.featureFlags,
      rollback_tested: values.rollbackTested,
      owner_approval: values.ownerApproval,
    }),
  });
}

export function selectPilotOrganization(session: AppSession, values: {
  selectionId: string;
  waveId: string;
  pilotUsers: Array<Record<string, unknown>>;
  decisionRef: string;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/delivery/pilot-organization', session, {
    method: 'POST',
    body: organizationBody(session, {
      selection_id: values.selectionId,
      wave_id: values.waveId,
      pilot_users: values.pilotUsers,
      decision_ref: values.decisionRef,
    }),
  });
}

export function createPilotDeliveryPackage(session: AppSession, values: {
  packageId: string;
  selectionId: string;
  readinessReportId: string;
  rollback: Record<string, unknown>;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/delivery/pilot-package', session, {
    method: 'POST',
    body: organizationBody(session, {
      package_id: values.packageId,
      selection_id: values.selectionId,
      readiness_report_id: values.readinessReportId,
      rollback: values.rollback,
    }),
  });
}

export function submitUsabilityFeedback(session: AppSession, values: {
  feedbackId: string;
  sessionId: string;
  screenId: string;
  taskId: string;
  outcome: string;
  severity: string;
  feedbackText: string;
  submittedAt: string;
  evidenceRefs: string[];
  accessibilityIssue: boolean;
  durationSeconds?: number;
  satisfactionScore?: number;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/ux/usability-feedback', session, {
    method: 'POST',
    body: organizationBody(session, {
      feedback_id: values.feedbackId,
      session_id: values.sessionId,
      screen_id: values.screenId,
      task_id: values.taskId,
      outcome: values.outcome,
      severity: values.severity,
      feedback_text: values.feedbackText,
      submitted_at: values.submittedAt,
      evidence_refs: values.evidenceRefs,
      accessibility_issue: values.accessibilityIssue,
      duration_seconds: values.durationSeconds,
      satisfaction_score: values.satisfactionScore,
    }),
  });
}

export function fetchGovernanceInbox(session: AppSession, signal?: AbortSignal): Promise<GovernanceInboxData> {
  const params = organizationParams(session);
  return request<GovernanceInboxData>(`/v1/governance/inbox?${params}`, session, { signal });
}

export function reviewGovernanceItem(session: AppSession, values: {
  collection: string;
  recordId: string;
  decision: 'returned' | 'rejected' | 'approved';
  decisionRef: string;
  rationale: string;
}): Promise<FootballRecord> {
  return request<FootballRecord>('/v1/governance/inbox/review', session, {
    method: 'POST',
    body: organizationBody(session, {
      collection: values.collection,
      record_id: values.recordId,
      decision: values.decision,
      decision_ref: values.decisionRef,
      rationale: values.rationale,
    }),
  });
}

export function fetchOperationsInbox(session: AppSession, filters: Record<string, string> = {}, signal?: AbortSignal): Promise<OperationsInboxData> {
  const params = organizationParams(session, filters);
  return request<OperationsInboxData>(`/v1/operations/inbox?${params}`, session, { signal });
}

export function markOperationsNotificationsRead(session: AppSession, notificationIds: string[]): Promise<{ marked_count: number; notification_ids: string[] }> {
  return request<{ marked_count: number; notification_ids: string[] }>('/v1/operations/inbox/notifications/read', session, {
    method: 'POST',
    body: organizationBody(session, { notification_ids: notificationIds }),
  });
}

export function fetchCollaborationWorkspace(session: AppSession, filters: Record<string, string> = {}, signal?: AbortSignal): Promise<CollaborationWorkspaceData> {
  const params = organizationParams(session, filters);
  return request<CollaborationWorkspaceData>(`/v1/collaboration/workspace?${params}`, session, { signal });
}

export function fetchCollaborationStream(session: AppSession, since = 0, signal?: AbortSignal): Promise<Response> {
  const params = organizationParams(session, { since: String(Math.max(0, since)), timeout: '25' });
  return fetch(`/v1/collaboration/events/stream?${params}`, {
    headers: { Accept: 'text/event-stream', Authorization: `Bearer ${session.token}` },
    signal,
  });
}

export function createCollaborationThread(session: AppSession, values: {
  threadId: string;
  title: string;
  body: string;
  entityType: string;
  entityId: string;
  deepLink: string;
  assignee?: string;
  mentions?: string[];
  participants?: string[];
  priority?: string;
  dueAt?: string;
}): Promise<CollaborationThread> {
  return request<CollaborationThread>('/v1/collaboration/threads', session, {
    method: 'POST',
    body: organizationBody(session, {
      thread_id: values.threadId,
      title: values.title,
      body: values.body,
      entity_type: values.entityType,
      entity_id: values.entityId,
      deep_link: values.deepLink,
      assignee: values.assignee,
      mentions: values.mentions ?? [],
      participants: values.participants ?? [],
      priority: values.priority ?? 'normal',
      due_at: values.dueAt,
    }),
  });
}

export function appendCollaborationComment(session: AppSession, values: { threadId: string; commentId: string; body: string; mentions?: string[] }): Promise<CollaborationThread> {
  return request<CollaborationThread>('/v1/collaboration/comments', session, {
    method: 'POST',
    body: organizationBody(session, { thread_id: values.threadId, comment_id: values.commentId, body: values.body, mentions: values.mentions ?? [] }),
  });
}

export function assignCollaborationThread(session: AppSession, values: { threadId: string; assignee: string; dueAt?: string; priority?: string }): Promise<CollaborationThread> {
  return request<CollaborationThread>('/v1/collaboration/threads/assign', session, {
    method: 'POST',
    body: organizationBody(session, { thread_id: values.threadId, assignee: values.assignee, due_at: values.dueAt, priority: values.priority }),
  });
}

export function resolveCollaborationThread(session: AppSession, values: { threadId: string; decision: 'resolved' | 'reopened'; rationale: string }): Promise<CollaborationThread> {
  return request<CollaborationThread>('/v1/collaboration/threads/resolve', session, {
    method: 'POST',
    body: organizationBody(session, values),
  });
}

export function markCollaborationNotificationsRead(session: AppSession, notificationIds: string[]): Promise<{ marked_count: number; notification_ids: string[] }> {
  return request<{ marked_count: number; notification_ids: string[] }>('/v1/collaboration/notifications/read', session, {
    method: 'POST',
    body: organizationBody(session, { notification_ids: notificationIds }),
  });
}

export function updateCollaborationPresence(session: AppSession, sessionId: string, cursor?: Record<string, unknown>): Promise<unknown> {
  return request<unknown>('/v1/collaboration/presence', session, {
    method: 'POST',
    body: organizationBody(session, { session_id: sessionId, display_name: session.subject ?? session.role, color: '#4cd6fa', cursor }),
  });
}

export function leaveCollaborationPresence(session: AppSession, sessionId: string): Promise<unknown> {
  return request<unknown>('/v1/collaboration/presence/leave', session, { method: 'POST', body: organizationBody(session, { session_id: sessionId }) });
}

export function fetchRosterWorkspace(session: AppSession, filters: Record<string, string> = {}, signal?: AbortSignal): Promise<RosterWorkspaceData> {
  const params = organizationParams(session, filters);
  return request<RosterWorkspaceData>(`/v1/roster/workspace?${params}`, session, { signal });
}

export function createRosterPlayer(session: AppSession, player: RosterPlayer): Promise<RosterPlayer> {
  return request<RosterPlayer>('/v1/roster/players', session, {
    method: 'POST',
    body: organizationBody(session, {
      player_id: player.id,
      display_name: player.display_name,
      position: player.position,
      position_group: player.position_group,
      jersey_number: player.jersey_number,
      aliases: player.aliases ?? [],
      eligibility: player.eligibility ?? [],
      role_groups: player.role_groups ?? [],
      status: player.status ?? 'active',
      availability: player.availability ?? 'available',
      owner: player.owner ?? session.subject,
      source_refs: player.source_refs ?? [],
    }),
  });
}

export function saveDepthChart(session: AppSession, chart: DepthChart): Promise<DepthChart> {
  return request<DepthChart>('/v1/roster/depth-charts', session, {
    method: 'POST',
    body: organizationBody(session, { depth_chart_id: chart.id, unit: chart.unit, position: chart.position, slots: chart.slots, season: chart.season, week: chart.week }),
  });
}

export function savePersonnelPackage(session: AppSession, packageRecord: PersonnelPackage): Promise<PersonnelPackage> {
  return request<PersonnelPackage>('/v1/roster/personnel-packages', session, {
    method: 'POST',
    body: organizationBody(session, { package_id: packageRecord.id, name: packageRecord.name, unit: packageRecord.unit, roles: packageRecord.roles, player_ids: packageRecord.player_ids, season: packageRecord.season }),
  });
}
