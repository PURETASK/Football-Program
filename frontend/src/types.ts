export type UserRole =
  | 'program_owner'
  | 'coach_staff'
  | 'analyst'
  | 'player'
  | 'validator'
  | 'performance_staff'
  | string;

export interface AppSession {
  organizationId: string;
  token: string;
  role: UserRole;
  subject?: string;
}

export interface OrganizationPopulation {
  status: string;
  ready_component_count: number;
  required_component_count: number;
}

export interface OrganizationPopulationComponent {
  component: string;
  collection: string;
  required_status: string;
  found: boolean;
  record_id?: string | null;
  actual_status?: string | null;
  scope_valid: boolean;
  season_valid: boolean;
  ready: boolean;
}

export interface OrganizationPopulationReadinessData {
  organization_id: string;
  season: string;
  status: string;
  components: OrganizationPopulationComponent[];
  ready_component_count: number;
  required_component_count: number;
  blockers: Array<Record<string, string>>;
  owner_review_required: boolean;
  activation_performed: boolean;
  production_implementation_allowed: boolean;
  external_state_changed: boolean;
}

export interface OperatorSummary {
  organization_id: string;
  role: UserRole;
  allowed_sections: string[];
  stage: string;
  work_package: string;
  pending_review_count: number;
  stale_source_count: number;
  record_counts: Record<string, number>;
  media_job_counts: Record<string, number>;
  organization_population?: OrganizationPopulation;
}

export interface Point {
  x: number;
  y: number;
}

export interface PlayPlayer {
  id: string;
  alignment_key?: string;
  defensive_technique?: string;
  defensive_alignment?: string;
  position?: string;
  role?: string;
  start?: Point;
  label?: string;
  locked?: boolean;
  hidden?: boolean;
}

export interface PlayAlignmentSlot {
  key: string;
  position?: string;
  role?: string;
  x: number;
  y: number;
}

export interface PlayAssetCompatibility {
  compatible: boolean;
  selectable: boolean;
  score: number;
  reasons: string[];
  warnings: string[];
  basis: string[];
  replacement_id?: string | null;
}

export interface TimelinePhase {
  id: string;
  label?: string;
  start_ms: number;
  end_ms: number;
}

export interface RouteBranch {
  id: string;
  label: string;
  condition: string;
  points: Point[];
  start_ms?: number;
  end_ms?: number;
  timing?: { start_ms?: number; end_ms?: number; phases?: TimelinePhase[] };
}

export interface PlayElement {
  id: string;
  kind: string;
  player_id?: string | null;
  type?: string;
  points?: Point[];
  path?: Point[];
  note?: string;
  assignment?: string;
  responsibility?: string;
  arrow_style?: string;
  arrow_ends?: 'end' | 'start' | 'both' | 'none' | string;
  path_mode?: 'smooth' | 'sharp' | string;
  line_style?: 'solid' | 'dashed' | 'dotted' | string;
  stroke_width?: number;
  line_cap?: 'round' | 'square' | 'butt' | string;
  angle_preset?: string;
  handle_roles?: string[];
  collision_status?: 'clear' | 'possible' | string;
  collision_intent?: 'review' | 'intentional' | 'avoid' | string;
  collision_note?: string;
  collision_corridor_yards?: number;
  asset_id?: string;
  start_ms?: number;
  end_ms?: number;
  timing?: {
    start_ms?: number;
    end_ms?: number;
    phases?: TimelinePhase[];
  };
  visibility?: string;
  zone?: string;
  read_key?: string;
  read_prompt?: string;
  objective?: string;
  technique?: string;
  landmark?: string;
  depth_yards?: number;
  leverage?: 'inside' | 'outside' | 'head_up' | 'top_down' | 'trail' | 'stack' | 'free' | string;
  gap?: string;
  fit_gap?: string;
  gap_owner?: string;
  gap_owner_label?: string;
  fit_rule?: string;
  coverage?: string;
  rush_lane?: string;
  blitz_path?: string;
  stunt?: string;
  rotation?: string;
  rotation_trigger?: string;
  rotation_from_zone?: string;
  rotation_to_zone?: string;
  rotation_replacement_player_id?: string;
  rotation_vacated_zone?: string;
  rotation_sequence?: number;
  rotation_communication?: string;
  movement_geometry?: 'manual' | 'shell-targeted' | string;
  blocking_primitive?: string;
  blocking_path_role?: string;
  blocking_geometry?: 'manual' | 'target-aware' | string;
  block_target_element_id?: string;
  block_partner_element_id?: string;
  protection_mode?: string;
  release_after_ms?: number;
  route_family?: string;
  stem_depth_yards?: number;
  break_type?: string;
  break_depth_yards?: number;
  finish_direction?: string;
  option_rule?: string;
  option_condition?: string;
  branches?: RouteBranch[];
  phase?: string;
  target_player_id?: string;
  target_element_id?: string;
  depends_on?: string[];
  exchange_with?: string;
  exchange_role?: string;
  exclusive_assignment?: boolean;
  locked?: boolean;
  hidden?: boolean;
  [key: string]: unknown;
}

export interface TimelineMarker {
  id: string;
  label: string;
  ms: number;
  kind?: string;
}

export interface PlayTimeline {
  snap_ms?: number;
  duration_ms?: number;
  markers?: TimelineMarker[];
  events?: PlayTimelineEvent[];
  narration?: PlayNarrationCue[];
}

export interface PlayTimelineEvent {
  id?: string;
  kind?: string;
  ms?: number;
  start_ms?: number;
  end_ms?: number;
  element_id?: string;
  player_id?: string;
  target_player_id?: string;
  branch_id?: string;
  label?: string;
  [key: string]: unknown;
}

export interface PlayNarrationCue {
  id: string;
  role?: string;
  text: string;
  start_ms: number;
  end_ms: number;
  branch_id?: string;
}

export interface PlayFieldContext {
  hash?: 'left' | 'middle' | 'right' | string;
  ball_x?: number;
  ball_y?: number;
  line_of_scrimmage_y?: number;
  strength?: 'left' | 'right' | 'balanced' | string;
  direction?: 'left' | 'right' | string;
  field_zone?: string;
}

export interface ValidationIssue {
  code?: string;
  message?: string;
  explanation?: string;
  severity?: 'error' | 'warning' | string;
  path?: string;
  status?: string;
  overrideable?: boolean;
  suggestion?: string;
  source?: {
    title?: string;
    uri?: string | null;
  };
}

export interface PlayDesign {
  id: string;
  name?: string;
  organization_id?: string;
  unit: 'offense' | 'defense' | 'special_teams' | string;
  personnel?: string;
  formation?: string;
  status?: string;
  version?: string;
  players?: PlayPlayer[];
  elements?: PlayElement[];
  timeline?: PlayTimeline;
  field_context?: PlayFieldContext;
  assignment_model_version?: string;
  concept?: string;
  front?: string;
  coverage?: string;
  rule_profile?: string;
  players_on_field?: number;
  route_collision_policy?: string;
  coverage_zones?: string[];
  coaching_notes?: string[];
  checksum?: string;
  latest_snapshot_id?: string;
  renderer_version?: string;
  validation?: {
    status?: string;
    issues?: ValidationIssue[];
  };
  _revision?: number;
  parent_design_id?: string;
  variant_batch_id?: string;
  variant_look?: { label?: string; patch?: Record<string, unknown>; assignment_patches?: Array<{ element_id: string; patch: Record<string, unknown> }>; source_design_id?: string; source_revision?: number };
  updated_at?: string;
  [key: string]: unknown;
}

export interface PlayRoleViewStep {
  id: string;
  element_id?: string;
  player_id?: string | null;
  position?: string;
  label?: string;
  instruction?: string;
  start_ms?: number;
  end_ms?: number;
  gap_owner?: string;
  exchange_with?: string;
  exchange_role?: string;
  replacement_zone?: string;
  rotation_trigger?: string;
  rotation_sequence?: number;
  step_index?: number;
  revealed?: boolean;
  mastered?: boolean;
}

export interface PlayRoleViewQuiz {
  id: string;
  question?: string;
  options?: unknown[];
  step_id?: string;
  answer?: unknown;
  answer_required?: boolean;
}

export interface PlayMasterySummary {
  attempt_count?: number;
  average_score?: number | null;
  mastered_step_count?: number;
  mastered_steps?: string[];
  status?: string;
}

export interface PlayMasteryRecord {
  id?: string;
  design_id?: string;
  role?: string;
  user_id?: string;
  step_id?: string;
  score?: number;
  result?: string;
  status?: string;
  practice_ref?: string | null;
  notes?: string;
  recorded_at?: string;
  [key: string]: unknown;
}

export interface PlayMasteryResponse {
  design_id: string;
  role?: string | null;
  user_id?: string | null;
  attempts: PlayMasteryRecord[];
  summary: PlayMasterySummary;
}

export interface PlayRoleView {
  id: string;
  play_id: string;
  role: string;
  mode: 'player' | 'position_group' | 'coach' | string;
  position_group?: string[];
  source_play_version?: string;
  source_snapshot_id?: string;
  source_checksum?: string;
  renderer_version?: string;
  renderer_checksum?: string;
  player?: PlayPlayer | null;
  players: PlayPlayer[];
  context_players: PlayPlayer[];
  elements: PlayElement[];
  filtered_diagram?: Record<string, unknown>;
  timeline?: PlayTimeline;
  steps: PlayRoleViewStep[];
  current_step?: number | null;
  read_reveal: Array<Record<string, unknown>>;
  quizzes: PlayRoleViewQuiz[];
  mastery: PlayMasteryResponse;
  practice_linkage?: Record<string, unknown>;
  coaching_notes?: string[];
  accessible_text?: string;
  status?: string;
  visible_element_ids?: string[];
}

export interface PlayAsset {
  id: string;
  category?: string;
  kind: string;
  term: string;
  display_name?: string;
  unit: string;
  aliases?: string[];
  description?: string;
  default_timing_ms?: number;
  arrow_style?: string;
  status?: string;
  version?: string;
  accessibility?: string;
  compatible_formations?: string[];
  compatible_personnel?: string[];
  compatible_rule_profiles?: string[];
  replacement_id?: string | null;
  compatibility?: PlayAssetCompatibility;
  alignment?: {
    term?: string;
    unit?: string;
    category?: string;
    ball?: { hash?: string; x?: number; y?: number };
    slots?: PlayAlignmentSlot[];
  };
}

export interface PlayTemplate {
  id: string;
  name: string;
  unit: string;
  formation?: string;
  personnel?: string;
  concept?: string;
  front?: string;
  coverage?: string;
  template_kind?: 'complete_call' | 'concept_layer' | 'protection_layer' | 'coverage_layer' | 'pressure_layer' | 'custom' | string;
  layer?: string;
  version?: string;
  status?: string;
  scope?: 'system' | 'organization' | string;
  description?: string;
  tags?: string[];
  situations?: string[];
  expected_companion_layers?: string[];
  coaching_points?: string[];
  timeline?: PlayTimeline;
  assignments?: PlayTemplateAssignment[];
  alignment?: {
    term?: string;
    unit?: string;
    category?: string;
    ball?: { hash?: string; x?: number; y?: number };
    slots?: PlayAlignmentSlot[];
  };
  source_design_id?: string;
  source_snapshot_id?: string;
  source_checksum?: string;
  parent_template_id?: string;
  inherited_assignments?: PlayTemplateAssignment[];
}

export interface PlayTemplateAssignment {
  key: string;
  slot: string;
  kind: string;
  type?: string;
  arrow_style?: string;
  assignment?: string;
  responsibility?: string;
  objective?: string;
  technique?: string;
  landmark?: string;
  depth_yards?: number;
  leverage?: string;
  gap?: string;
  fit_gap?: string;
  zone?: string;
  coverage?: string;
  phase?: string;
  read_key?: string;
  read_prompt?: string;
  exclusive_assignment?: boolean;
  asset_id?: string;
  start_ms?: number;
  end_ms?: number;
  timing?: PlayElement['timing'];
  points?: Array<{ dx: number; dy: number }>;
  depends_on?: string[];
  exchange_with?: string;
  target_element_key?: string;
  [key: string]: unknown;
}

export interface PlayVersionSnapshot {
  id: string;
  design_id?: string;
  version?: string;
  source?: string;
  checksum?: string;
  created_at?: string;
  created_by?: string;
  renderer_version?: string;
  renderer_checksum?: string;
  integrity?: { valid: boolean; issues?: string[]; expected_checksum?: string; expected_snapshot_id?: string };
}

export interface PlayVersionHistory {
  design_id?: string;
  snapshots: PlayVersionSnapshot[];
  releases: Array<Record<string, unknown> & { integrity?: { valid: boolean; issues?: string[] } }>;
}

export interface PlayDesignDiffCollection {
  added: string[];
  removed: string[];
  changed: Array<{ id: string; fields: string[]; before?: Record<string, unknown>; after?: Record<string, unknown> }>;
}

export interface PlayDesignDiff {
  design_id: string;
  base_snapshot_id: string;
  compare_snapshot_id: string;
  base_version?: string;
  compare_version?: string;
  base_design?: PlayDesign;
  compare_design?: PlayDesign;
  diff: {
    changed_fields: string[];
    players: PlayDesignDiffCollection;
    elements: PlayDesignDiffCollection;
    timeline_changed: boolean;
    base_checksum?: string;
    candidate_checksum?: string;
  };
}

export interface PlayMergeResult {
  status: 'merged' | 'conflict';
  design_id?: string;
  branch_id: string;
  merge_base_snapshot_id?: string;
  design?: PlayDesign;
  conflicts?: Array<{ path?: string; base?: unknown; target?: unknown; branch?: unknown; message?: string }>;
  diff?: PlayDesignDiff['diff'];
}

export interface PlayLegalityReport {
  design_id: string;
  rule_profile: string;
  status: string;
  profile?: {
    id?: string;
    label?: string;
    source?: { title?: string; uri?: string | null; rule_refs?: string[] };
  };
  issues: ValidationIssue[];
  overrides: Array<Record<string, unknown>>;
}

export interface PlayAssignmentGraphNode {
  id: string;
  kind?: string;
  label?: string;
  player_id?: string | null;
  objective?: string | null;
  start_ms?: number | null;
  end_ms?: number | null;
}

export interface PlayAssignmentGraphEdge {
  source: string;
  target: string;
  relation: 'precedes' | 'exchange' | 'targets_assignment' | 'targets_player' | string;
}

export interface PlayAssignmentGraph {
  version: string;
  nodes: PlayAssignmentGraphNode[];
  edges: PlayAssignmentGraphEdge[];
  findings: ValidationIssue[];
  summary: {
    node_count: number;
    edge_count: number;
    blocking_count: number;
    warning_count: number;
  };
}

export interface PlayDraftValidationReport extends PlayLegalityReport {
  draft: true;
  persisted: false;
  draft_checksum: string;
  normalized_design: PlayDesign;
  assignment_graph: PlayAssignmentGraph;
}

export interface PlayComment {
  id: string;
  design_id?: string;
  text?: string;
  actor?: string;
  created_by?: string;
  created_at?: string;
  status?: string;
  element_id?: string | null;
  replies?: PlayComment[];
}

export interface PlayPresence {
  session_id: string;
  subject?: string;
  display_name?: string;
  role?: string;
  color?: string;
  cursor?: Point;
  last_seen_at?: string;
}

export interface PlayCollaborationEvent {
  id: string;
  design_id: string;
  sequence: number;
  event_type: string;
  actor?: string;
  payload?: Record<string, unknown>;
  created_at?: string;
}

export interface ExportArtifact {
  artifact_id?: string;
  filename: string;
  mime_type: string;
  content_base64: string;
  bytes: number;
  sha256: string;
  source_manifest_hash?: string;
  source_manifest?: Array<{
    design_id?: string;
    name?: string;
    version?: string;
    snapshot_id?: string;
    content_checksum?: string;
    renderer_version?: string;
    renderer_checksum?: string;
    status?: string;
    release_id?: string;
    approval_state?: string;
  }>;
  signature?: string;
  kind?: string;
  format?: string;
  layout?: string;
  role?: string;
  validation?: { status?: string; issues?: ValidationIssue[] };
  page_size?: string;
  page_count?: number;
  printer_safe?: boolean;
  black_white?: boolean;
  accessibility?: { has_alt_text?: boolean; has_accessible_text?: boolean; role?: string };
  source_lock?: { status?: string; issues?: ValidationIssue[] };
  integrity?: { status?: string; issues?: ValidationIssue[]; sha256?: string; bytes?: number };
}

export interface ExportPreflight {
  kind: string;
  format: string;
  layout: string;
  role: string;
  design_count: number;
  can_render: boolean;
  validation: { status: string; issues: ValidationIssue[] };
  source_manifest_hash: string;
  source_manifest: NonNullable<ExportArtifact['source_manifest']>;
  page_size?: string;
  page_count?: number;
  printer_safe?: boolean;
  accessibility?: { has_alt_text?: boolean; has_accessible_text?: boolean; role?: string };
  source_lock?: { status?: string; issues?: ValidationIssue[] };
}

export interface ApiEnvelope<T> {
  status: string;
  data: T;
  error?: string | null;
}

export interface FootballRecord {
  id: string;
  name?: string;
  title?: string;
  status?: string;
  organization_id?: string;
  owner?: string;
  opponent?: string;
  week?: string;
  week_context?: string;
  source_refs?: string[];
  evidence_refs?: string[];
  issues?: Array<string | Record<string, unknown>>;
  blockers?: Array<string | Record<string, unknown>>;
  human_review_required?: boolean;
  [key: string]: unknown;
}

export interface FilmAsset extends FootballRecord {
  uri?: string;
  duration_seconds?: number;
  file_name?: string;
  media_type?: string;
  captured_at?: string;
  team_context?: string;
}

export interface FilmClip extends FootballRecord {
  asset_id?: string;
  start_seconds?: number;
  end_seconds?: number;
  context?: { team?: string; opponent?: string; situation?: string };
}

export interface FilmLinkedRecordRef {
  record_type: 'playbook' | 'scouting' | 'player_development' | 'game_plan' | 'analytics' | string;
  record_id: string;
  label?: string;
}

export interface FilmObservation extends FootballRecord {
  clip_id?: string;
  asset_id?: string;
  linked_play_ids?: string[];
  domain?: string;
  label?: string;
  confidence?: string;
  classification?: string;
  evidence?: string;
  context?: { team?: string; opponent?: string; situation?: Record<string, unknown> };
  linked_record_refs?: FilmLinkedRecordRef[];
}

export interface FilmPlaylist extends FootballRecord {
  purpose?: string;
  clip_ids?: string[];
  access_roles?: string[];
  filters?: Record<string, unknown>;
}

export interface FilmAnnotationSession extends FootballRecord {
  clip_id?: string;
  annotator?: string;
  allowed_domains?: string[];
  annotations?: FilmObservation[];
}

export interface FilmVoiceNote extends FootballRecord {
  clip_id?: string;
  asset_id?: string;
  frame_seconds?: number;
  mime_type?: string;
  audio_data?: string;
  transcript?: string;
  byte_size?: number;
  access_roles?: string[];
  storage_boundary?: string;
}

export interface FilmWorkspaceData {
  assets: FilmAsset[];
  clips: FilmClip[];
  observations: FilmObservation[];
  playlists: FilmPlaylist[];
  sessions: FilmAnnotationSession[];
  voice_notes: FilmVoiceNote[];
}

export interface PracticePeriod extends FootballRecord {
  type: string;
  objective: string;
  owner: string;
  players: string[];
  position_groups?: string[];
  minutes: number;
  reps: number;
  learning_rationale: string;
  load_rationale: string;
  play_ids?: string[];
  drill_ids?: string[];
  attendance?: string[];
  coaching_objective?: string;
  install_phase?: string;
}

export interface PracticeDrill extends FootballRecord {
  name?: string;
  position_groups?: string[];
  objective?: string;
  skill?: string;
  status?: string;
}

export interface PracticeDrillWorkspaceData {
  organization_id: string;
  status: string;
  drills: PracticeDrill[];
}

export interface PracticePlan extends FootballRecord {
  team_context?: string;
  season_phase?: string;
  objective?: string;
  opponent_priorities?: string[];
  periods?: PracticePeriod[];
  total_minutes?: number;
  load_controls?: Record<string, unknown>;
  roster_ids?: string[];
  install_items?: Array<Record<string, unknown>>;
  attendance_policy?: string;
  practice_card_preferences?: Record<string, unknown>;
}

export interface PracticeWorkspaceData {
  organization_id: string;
  status: string;
  week?: string;
  plans: PracticePlan[];
  load_exceeded: number;
  human_review_required: boolean;
}

export interface PracticeAttendanceRecord extends FootballRecord {
  practice_id: string;
  player_id: string;
  player_name?: string;
  position?: string;
  position_group?: string;
  recorded_by?: string;
  recorded_at?: string;
  period_ids?: string[];
  minutes_available?: number | null;
  note?: string;
  source_refs?: string[];
  human_review_required?: boolean;
}

export interface PracticeAttendanceWorkspaceData {
  organization_id: string;
  practice_id?: string | null;
  records: PracticeAttendanceRecord[];
  counts: Record<string, number>;
  total: number;
  limited_or_absent: PracticeAttendanceRecord[];
  human_review_required: boolean;
  production_implementation_allowed: boolean;
}

export interface ScoutingWorkspaceData {
  organization_id: string;
  opponent?: string | null;
  status: string;
  opponent_profiles: FootballRecord[];
  scouting_reports: FootballRecord[];
  matchup_models: FootballRecord[];
  opponent_evolutions: FootballRecord[];
  low_sample_count: number;
  review_count: number;
  adaptation_warning_count: number;
  human_review_required: boolean;
}

export interface ScoutingTendencyExplorerData {
  organization_id: string;
  opponent?: string | null;
  filters: Record<string, string>;
  records: FootballRecord[];
  total: number;
  sample_size_total: number;
  review_gate_counts: Record<string, number>;
  human_review_required: boolean;
  production_implementation_allowed: boolean;
}

export interface GamePlanWorkspaceData {
  organization_id: string;
  status: string;
  week?: string | null;
  plans: FootballRecord[];
  scouting_reports: FootballRecord[];
  metric_observations: FootballRecord[];
  rule_recommendations: FootballRecord[];
  weekly_deliveries: FootballRecord[];
  release_candidates: FootballRecord[];
  pending_review_count: number;
  blockers: Array<string | Record<string, unknown>>;
  evidence_summary: Record<string, number>;
  human_approval_required: boolean;
}

export interface GamePlanComment extends FootballRecord {
  author?: string;
  role?: string;
  body?: string;
  created_at?: string;
}

export interface GamePlanThread extends FootballRecord {
  plan_id?: string;
  topic?: string;
  comments?: GamePlanComment[];
  decision?: Record<string, unknown> | null;
}

export interface GamePlanThreadWorkspace {
  organization_id: string;
  status: string;
  threads: GamePlanThread[];
  open_thread_count: number;
  human_decision_required: boolean;
}

export interface GamePlanData {
  workspace: GamePlanWorkspaceData;
  collaboration: GamePlanThreadWorkspace;
}

export interface GamePlanReleaseSnapshot extends FootballRecord {
  plan_id: string;
  week: string;
  status: string;
  locked?: boolean;
  immutable?: boolean;
  note?: string;
  content_hash?: string;
  renderer_version?: string;
  previous_snapshot_id?: string | null;
  what_changed?: string[];
  dependency_manifest?: {
    status?: string;
    artifact_count?: number;
    linked_count?: number;
    unresolved_refs?: string[];
    artifacts?: Array<{ id: string; status: string; collection?: string | null; checksum?: string | null; version?: string | number | null }>;
  };
  release_manifest_hash?: string;
  decision_ref?: string;
  created_by?: string;
  approved_by?: string;
  rolled_back_by?: string;
}

export interface GamePlanReleaseRoomData {
  organization_id: string;
  status: string;
  week?: string | null;
  plans: FootballRecord[];
  snapshots: GamePlanReleaseSnapshot[];
  latest_snapshot?: GamePlanReleaseSnapshot | null;
  pending_approval_count: number;
  locked_count: number;
  rollback_available: boolean;
  human_approval_required: boolean;
  boundary: string;
}

export interface AnalyticsWorkspaceData {
  organization_id: string;
  status: string;
  situation?: string | null;
  observations: FootballRecord[];
  reports: FootballRecord[];
  outcomes: FootballRecord[];
  outcome_count: number;
  lineage_complete_count: number;
  uncertainty_count: number;
  review_count: number;
  human_review_required: boolean;
  responsibility_phase_summary?: Array<{
    phase: string;
    record_count: number;
    success_count: number;
    sample_size: number;
    success_rate: number | null;
    confidence: string;
    human_review_required: boolean;
    linked_assignment_ids: string[];
    teaching_step_ids: string[];
    linked_play_ids: string[];
  }>;
}

export interface DeliveryTask extends FootballRecord {
  title: string;
  category: string;
  owner?: string;
  assigned_to?: string;
  due_at?: string;
  week?: string;
  priority?: string;
  linked_records?: string[];
  computed_state?: string;
}

export interface DeliveryWorkspaceData {
  organization_id: string;
  status: string;
  week?: string | null;
  tasks: DeliveryTask[];
  packets: FootballRecord[];
  delivery_packets: FootballRecord[];
  release_snapshots: GamePlanReleaseSnapshot[];
  practice_plans: PracticePlan[];
  counts: Record<string, number>;
  delivery_packet_outputs: string[];
  packet_readiness: Array<{
    id: string;
    label: string;
    audience: string;
    week?: string | null;
    status: string;
    required: string[];
    linked_records: string[];
    missing: string[];
    blockers: string[];
    human_review_required: boolean;
    boundary: string;
  }>;
  human_review_required: boolean;
  boundary: string;
}

export interface PlayerTodayData {
  organization_id: string;
  player_id: string;
  status: string;
  assignments: FootballRecord[];
  lessons: FootballRecord[];
  mastery: FootballRecord[];
  development_plans: FootballRecord[];
  quiz_attempts: FootballRecord[];
  next_step?: FootballRecord | null;
  privacy: string;
}

export interface OrganizationContextData {
  organization_id: string;
  contexts: FootballRecord[];
  terminology_bundles: FootballRecord[];
}

export interface StageZeroData {
  gate: FootballRecord & { gate_status?: string; blockers?: Array<string | Record<string, unknown>> };
  approvals: FootballRecord[];
  production_implementation_allowed: boolean;
  stage_advance_authorized: boolean;
}

export interface PilotReadinessData {
  organization_id: string;
  reports: FootballRecord[];
  human_review_required: boolean;
  production_implementation_allowed: boolean;
}

export interface Stage25AcceptanceData {
  organization_id: string;
  spec: FootballRecord;
  acceptances: FootballRecord[];
  production_implementation_allowed: boolean;
  stage_advance_authorized: boolean;
}

export interface AdminWorkspaceData {
  organization: OrganizationContextData;
  sources: FootballRecord[];
  stageZero: StageZeroData;
  pilot: PilotReadinessData;
  pilotSelections: FootballRecord[];
  pilotPackages: FootballRecord[];
  usabilityFeedback: FootballRecord[];
}

export interface GovernanceInboxItem {
  collection: string;
  id: string;
  status?: string;
  owner?: string;
  human_review_required: boolean;
  blockers: Array<string | Record<string, unknown>>;
  evidence_refs: string[];
  can_approve: boolean;
}

export interface GovernanceInboxData {
  organization_id: string;
  role: string;
  items: GovernanceInboxItem[];
  count: number;
  approval_boundary: string;
}

export interface OperationsInboxItem extends FootballRecord {
  collection: string;
  record_id: string;
  item_type: string;
  category: string;
  title: string;
  description?: string;
  urgency: 'critical' | 'high' | 'normal' | 'low' | string;
  priority?: string;
  assigned_to?: string | null;
  assigned_to_me: boolean;
  due_at?: string | null;
  due_state: 'overdue' | 'due_today' | 'upcoming' | 'unscheduled' | string;
  blockers: Array<string | Record<string, unknown>>;
  evidence_refs: string[];
  notification_unread: boolean;
  deep_link: string;
  action_label: string;
  can_act: boolean;
  human_review_required?: boolean;
  can_approve?: boolean;
}

export interface OperationsInboxData {
  organization_id: string;
  role: string;
  actor: string;
  items: OperationsInboxItem[];
  count: number;
  counts: {
    by_category: Record<string, number>;
    by_urgency: Record<string, number>;
    by_due_state: Record<string, number>;
    unread_notifications: number;
    assigned_to_me: number;
    overdue: number;
  };
  filters: Record<string, string>;
  generated_at: string;
  automation_boundary: string;
}

export interface CollaborationComment extends FootballRecord {
  thread_id?: string;
  author?: string;
  role?: string;
  body?: string;
  mentions?: string[];
}

export interface CollaborationThread extends FootballRecord {
  title: string;
  body?: string;
  entity_type: string;
  entity_id: string;
  deep_link?: string;
  status: 'open' | 'resolved' | string;
  priority?: 'critical' | 'high' | 'normal' | 'low' | string;
  assigned_to?: string | null;
  mentions?: string[];
  participants?: string[];
  due_at?: string | null;
  comments?: CollaborationComment[];
  resolution?: Record<string, unknown> | null;
}

export interface CollaborationNotification extends FootballRecord {
  recipient?: string;
  title: string;
  description?: string;
  body?: string;
  kind?: string;
  thread_id?: string;
  deep_link?: string;
  status?: string;
  read_at?: string;
}

export interface CollaborationActivity extends FootballRecord {
  sequence?: number;
  event_type?: string;
  actor?: string;
  subject?: string;
  payload?: Record<string, unknown>;
}

export interface CollaborationPresence extends FootballRecord {
  session_id: string;
  subject?: string;
  role?: string;
  display_name?: string;
  color?: string;
  cursor?: Record<string, unknown> | null;
  last_seen_at?: string;
}

export interface CollaborationWorkspaceData {
  organization_id: string;
  actor: string;
  role: string;
  threads: CollaborationThread[];
  notifications: CollaborationNotification[];
  activity: CollaborationActivity[];
  presence: CollaborationPresence[];
  counts: {
    open_threads: number;
    assigned_to_me: number;
    unread_notifications: number;
    active_presence: number;
  };
  boundary: string;
}

export interface RosterPlayer extends FootballRecord {
  display_name: string;
  position: string;
  position_group: string;
  jersey_number?: string | null;
  aliases?: string[];
  eligibility?: string[];
  role_groups?: string[];
  availability?: string;
}

export interface DepthChart extends FootballRecord {
  unit: string;
  position: string;
  season: string;
  week?: string;
  slots: Array<{ rank: number; player_id: string; role?: string }>;
}

export interface PersonnelPackage extends FootballRecord {
  name: string;
  unit: string;
  roles: string[];
  player_ids: string[];
  season: string;
}

export interface RosterWorkspaceData {
  organization_id: string;
  status: string;
  players: RosterPlayer[];
  depth_charts: DepthChart[];
  personnel_packages: PersonnelPackage[];
  position_groups: string[];
  counts: { players: number; active: number; depth_charts: number; personnel_packages: number };
  human_review_required: boolean;
  privacy_boundary: string;
}
