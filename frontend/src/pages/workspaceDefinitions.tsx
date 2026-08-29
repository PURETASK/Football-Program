import {
  BadgeCheck,
  BarChart3,
  BellRing,
  CheckCircle2,
  BookOpenCheck,
  BrainCircuit,
  CalendarDays,
  ChartNoAxesCombined,
  ClipboardCheck,
  ClipboardList,
  Eye,
  FileCheck2,
  Film,
  Gauge,
  GitBranch,
  GraduationCap,
  Library,
  ListChecks,
  LockKeyhole,
  MessageSquareText,
  MonitorCog,
  NotebookTabs,
  PlayCircle,
  ScanSearch,
  Settings2,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Target,
  TimerReset,
  UsersRound,
  WandSparkles,
  type LucideIcon,
} from 'lucide-react';

export interface WorkspaceMetric {
  label: string;
  recordKey?: string;
  description: string;
}

export interface WorkspaceFeature {
  id: string;
  title: string;
  description: string;
  howItWorks: string;
  input: string;
  output: string;
  status: string;
  icon: LucideIcon;
}

export interface WorkspaceDefinition {
  slug: string;
  eyebrow: string;
  title: string;
  description: string;
  howItWorks: string;
  audience: string;
  outcome: string;
  icon: LucideIcon;
  tone: 'blue' | 'cyan' | 'amber' | 'violet' | 'green';
  metrics: WorkspaceMetric[];
  features: WorkspaceFeature[];
  workflow: Array<{ title: string; description: string }>;
  boundary: string;
}

export const ROSTER_WORKSPACE: WorkspaceDefinition = {
  slug: 'roster', eyebrow: 'People and personnel', title: 'Roster & Personnel', icon: UsersRound, tone: 'green',
  description: 'Maintain the organization-scoped player identity, position groups, depth charts, personnel packages, eligibility, and availability that every football workflow depends on.',
  howItWorks: 'Roster records are validated once, then reused by Player, Practice, Play Designer, Game Plan, Scouting, and analytics without silently inferring identity or status.',
  audience: 'Program owners, coaches, position staff, analysts, performance staff, and players through privacy-filtered views.',
  outcome: 'A trustworthy personnel graph with stable player IDs, accountable depth-chart roles, package membership, and explicit availability state.',
  metrics: [
    { label: 'Players', recordKey: 'roster_players', description: 'Organization-scoped identity records.' },
    { label: 'Depth charts', recordKey: 'depth_charts', description: 'Position and unit ordering.' },
    { label: 'Personnel packages', recordKey: 'personnel_packages', description: 'Reusable role groupings for football systems.' },
  ],
  features: [
    { id: 'identity', title: 'Player identity registry', icon: UsersRound, status: 'Interactive controls live', description: 'Keep stable player IDs, aliases, position, eligibility, role groups, owner, and availability together.', howItWorks: 'Authorized staff create organization-scoped records with source references and explicit status values.', input: 'Verified roster identity and source evidence.', output: 'A canonical player record.' },
    { id: 'depth-charts', title: 'Depth charts', icon: GitBranch, status: 'Interactive controls live', description: 'Assign starters, rotational players, and reserves by unit and position for a defined season and week.', howItWorks: 'Each slot resolves to a roster player and rejects unknown or duplicate identities before save.', input: 'Roster players, unit, position, season, and slot order.', output: 'An auditable depth-chart artifact.' },
    { id: 'personnel', title: 'Personnel packages', icon: BadgeCheck, status: 'Interactive controls live', description: 'Define reusable role packages that can power formations, practice groups, scouting filters, and game-plan menus.', howItWorks: 'Packages reference canonical player IDs and role labels rather than copying names into downstream systems.', input: 'Roster IDs, package roles, unit, and season.', output: 'Reusable personnel context.' },
    { id: 'availability', title: 'Availability boundary', icon: ShieldCheck, status: 'Human controlled', description: 'Expose active, reserve, injured, practice-squad, and other states without silently making medical or eligibility decisions.', howItWorks: 'Availability is a staff-entered state with ownership and source references; downstream users see the current recorded status and its uncertainty.', input: 'Authorized staff status and evidence.', output: 'Visible, accountable personnel availability.' },
  ],
  workflow: [
    { title: 'Register', description: 'Create or reconcile a stable player identity with source evidence.' },
    { title: 'Organize', description: 'Assign position groups, role groups, eligibility, and availability.' },
    { title: 'Compose', description: 'Build depth charts and reusable personnel packages.' },
    { title: 'Propagate', description: 'Let downstream systems reference the same canonical IDs and audit trail.' },
  ],
  boundary: 'Roster controls do not infer medical clearance, eligibility, depth-chart authority, or player status from external systems. Those remain explicit, organization-owned decisions.',
};

export const FILM_WORKSPACE: WorkspaceDefinition = {
  slug: 'film', eyebrow: 'Teaching media', title: 'Film Room', icon: Film, tone: 'violet',
  description: 'Review authorized video, organize teaching clips, annotate evidence, and turn correction moments into role-specific learning.',
  howItWorks: 'Assets enter through the authorized media pipeline, become bounded clips, then move through playlists, annotations, staff QA, and player teaching.',
  audience: 'Coaches, analysts, quality-control staff, and players with role-scoped access.',
  outcome: 'Evidence-linked clips, reviewed corrections, teaching playlists, and searchable football observations.',
  metrics: [
    { label: 'Film clips', recordKey: 'film_clips', description: 'Authorized, bounded teaching moments.' },
    { label: 'Media assets', recordKey: 'film_assets', description: 'Registered source videos with provenance.' },
    { label: 'Playlists', recordKey: 'film_playlists', description: 'Role-filtered teaching sequences.' },
  ],
  features: [
    { id: 'library', title: 'Media library', icon: Library, status: 'Backend operational', description: 'Find registered games, practices, cutups, and clips without losing source provenance.', howItWorks: 'Search and filters narrow organization-scoped records by game, unit, situation, player, concept, and evidence state.', input: 'Authorized media assets and clip metadata.', output: 'A filtered evidence library ready for review.' },
    { id: 'playlists', title: 'Teaching playlists', icon: PlayCircle, status: 'Backend operational', description: 'Sequence clips for installs, corrections, opponent preparation, and position meetings.', howItWorks: 'Staff select validated clips, order them, assign an audience, and retain every source reference.', input: 'Reviewed clips and a teaching objective.', output: 'Role-scoped, ordered film sessions.' },
    { id: 'annotations', title: 'Annotation and telestration', icon: WandSparkles, status: 'Interactive controls live', description: 'Mark leverage, keys, landmarks, errors, and corrections against a bounded film moment.', howItWorks: 'The React workbench creates scoped annotation sessions and stores classified observations, confidence, correction state, and linked football concepts.', input: 'A bounded clip and staff observation.', output: 'Reviewable visual evidence and correction notes.' },
    { id: 'qa', title: 'Film QA and correction', icon: BadgeCheck, status: 'Human controlled', description: 'Prevent low-confidence or incomplete observations from becoming definitive player feedback.', howItWorks: 'Reviewers verify tags, confidence, corrections, and source integrity before teaching release.', input: 'Annotations and analyst observations.', output: 'Approved teaching evidence or an explicit correction queue.' },
  ],
  workflow: [
    { title: 'Register', description: 'Verify source authority, integrity, organization scope, and media metadata.' },
    { title: 'Clip', description: 'Create bounded teaching moments without altering the source asset.' },
    { title: 'Analyze', description: 'Tag, annotate, grade confidence, and connect observations to football context.' },
    { title: 'Teach', description: 'Publish reviewed playlists and corrections to the appropriate role.' },
  ],
  boundary: 'The page is independent from the legacy dashboard and its library, evidence, playlist, and annotation-session controls are live. Media writes remain governed by the Python API, authorization, retention, and review controls; frame drawing and video playback expansion must preserve those same boundaries.',
};

export const PRACTICE_WORKSPACE: WorkspaceDefinition = {
  slug: 'practice', eyebrow: 'Weekly development', title: 'Practice', icon: CalendarDays, tone: 'green',
  description: 'Build accountable practice scripts that connect every period, drill, workload decision, and correction to the weekly plan.',
  howItWorks: 'Coaches assemble objectives and periods, assign groups and drills, monitor planned load, and link work back to plays, film, and development goals.',
  audience: 'Coordinators, position coaches, performance staff, quality control, and approved operations staff.',
  outcome: 'A measurable practice script, install coverage, workload summary, coaching responsibilities, and printable schedule.',
  metrics: [
    { label: 'Practice plans', recordKey: 'practice_plans', description: 'Organization-scoped weekly scripts.' },
    { label: 'Drills', recordKey: 'drills', description: 'Validated teaching and development activities.' },
    { label: 'Player assignments', recordKey: 'player_assignments', description: 'Role-specific work and objectives.' },
  ],
  features: [
    { id: 'script', title: 'Practice script', icon: ClipboardList, status: 'Backend operational', description: 'Lay out the day by period, duration, field, group, objective, and accountable coach.', howItWorks: 'Periods are ordered into a bounded schedule with install and situation coverage.', input: 'Weekly objectives, available time, players, fields, and staff.', output: 'A complete timed practice schedule.' },
    { id: 'drills', title: 'Drill library', icon: NotebookTabs, status: 'Validated corpus', description: 'Choose position-specific drills with coaching cues, common errors, progressions, KPIs, film angles, and safety controls.', howItWorks: 'Filters connect the objective and position group to approved drills and seasonal variants.', input: 'Development objective, position, phase, and constraints.', output: 'A measurable drill prescription.' },
    { id: 'load', title: 'Workload and safety', icon: Gauge, status: 'Qualified review', description: 'See planned physical and cognitive load without turning the app into a medical decision maker.', howItWorks: 'Period demand is summarized and health signals are escalated to qualified staff.', input: 'Period durations, intensity, group assignments, and approved observations.', output: 'Non-diagnostic workload visibility and review flags.' },
    { id: 'review', title: 'Post-practice review', icon: ListChecks, status: 'Human controlled', description: 'Record what was installed, what failed, and what must be corrected in film or the next practice.', howItWorks: 'Staff link outcomes and evidence to the original objective and player development loop.', input: 'Completed periods, notes, clips, and coaching observations.', output: 'Correction tasks and updated weekly priorities.' },
  ],
  workflow: [
    { title: 'Set objectives', description: 'Define the football, development, and situation outcomes for the day.' },
    { title: 'Build periods', description: 'Assign time, groups, staff, field space, plays, and drills.' },
    { title: 'Validate load', description: 'Check total time, workload, conflicts, equipment, and safety boundaries.' },
    { title: 'Review outcomes', description: 'Link practice results to film, mastery, and the next planning decision.' },
  ],
  boundary: 'This individual page now provides the live period builder, schedule inspection, load envelope, and draft persistence without redirecting to the monolithic dashboard. Canonical edits remain API-controlled and medical decisions remain outside the system.',
};

export const SCOUTING_WORKSPACE: WorkspaceDefinition = {
  slug: 'scouting', eyebrow: 'Opponent intelligence', title: 'Scouting', icon: Target, tone: 'amber',
  description: 'Turn authorized opponent evidence into tendencies, matchup context, warnings, and staff-ready situational decisions.',
  howItWorks: 'Analysts assemble source-linked observations, preserve denominator and uncertainty, then route reports through staff review before game-plan use.',
  audience: 'Pro scouts, advance scouts, analysts, quality control, coordinators, and approved coaching staff.',
  outcome: 'Opponent profiles, tendency reports, matchup alerts, adaptation warnings, and game-plan inputs.',
  metrics: [
    { label: 'Scouting reports', recordKey: 'scouting_reports', description: 'Evidence-linked opponent reports.' },
    { label: 'Analytics reports', recordKey: 'analytics_reports', description: 'Contextual tendency and matchup outputs.' },
    { label: 'Knowledge claims', recordKey: 'knowledge_claims', description: 'Source-classified research records.' },
  ],
  features: [
    { id: 'profile', title: 'Opponent profile', icon: ScanSearch, status: 'Backend operational', description: 'Organize personnel, scheme, identity, recent changes, and source freshness in one reviewable record.', howItWorks: 'Evidence is grouped by unit and confidence while unsupported conclusions remain blocked.', input: 'Authorized film, reports, roster context, and verified sources.', output: 'A current opponent identity dossier.' },
    { id: 'tendencies', title: 'Tendency explorer', icon: ChartNoAxesCombined, status: 'Evidence required', description: 'Inspect what an opponent does by situation without hiding sample size, denominator, or uncertainty.', howItWorks: 'Filters segment observations by down, distance, field zone, personnel, formation, motion, pressure, and coverage.', input: 'Tagged observations and metric definitions.', output: 'Qualified tendencies with context and caveats.' },
    { id: 'matchups', title: 'Personnel and matchups', icon: UsersRound, status: 'Human reviewed', description: 'Compare opponent traits and expected roles to your roster and plan.', howItWorks: 'Staff record strengths, vulnerabilities, usage, substitution patterns, and confidence rather than definitive predictions.', input: 'Approved roster context and opponent observations.', output: 'Matchup considerations and coaching alerts.' },
    { id: 'adaptation', title: 'Adaptation tracker', icon: TimerReset, status: 'Review required', description: 'Track how the opponent changes across weeks, injuries, opponents, and game situations.', howItWorks: 'Chronological evidence separates durable identity from recent or low-sample adjustments.', input: 'Time-stamped reports, film, and situation context.', output: 'Change warnings and contingency triggers.' },
  ],
  workflow: [
    { title: 'Collect', description: 'Use only registered, authorized, and current sources.' },
    { title: 'Qualify', description: 'Preserve sample, context, denominator, confidence, and disagreement.' },
    { title: 'Review', description: 'Coaches and analysts challenge conclusions and document uncertainty.' },
    { title: 'Apply', description: 'Promote accepted findings into game-plan options and counters.' },
  ],
  boundary: 'Scouting is a decision-support system, not an autonomous recommendation engine. Every high-impact conclusion remains evidence-linked and human reviewed.',
};

export const GAME_PLAN_WORKSPACE: WorkspaceDefinition = {
  slug: 'game-plan', eyebrow: 'Weekly decisions', title: 'Game Plan', icon: ClipboardList, tone: 'blue',
  description: 'Compose the weekly plan from approved plays, opponent evidence, situations, counters, practice installation, and human decisions.',
  howItWorks: 'Staff select calls by situation, document triggers and counter-counters, link evidence, assign install status, and lock an approved weekly snapshot.',
  audience: 'Head coach, coordinators, position coaches, quality control, analysts, and approved operations staff.',
  outcome: 'A reviewable weekly plan, install matrix, situational call menu, call sheet, and immutable approved snapshot.',
  metrics: [
    { label: 'Weekly plans', recordKey: 'game_plans', description: 'Human-controlled plan packages.' },
    { label: 'Published plays', recordKey: 'play_designs', description: 'Canonical calls available for selection.' },
    { label: 'Pending reviews', description: 'Decisions awaiting staff or owner action.' },
  ],
  features: [
    { id: 'situations', title: 'Situational plan', icon: ClipboardCheck, status: 'Backend operational', description: 'Organize calls for down, distance, field zone, clock, score, personnel, and special situations.', howItWorks: 'Each situation retains primary calls, alerts, constraints, and accountable staff.', input: 'Published plays, opponent context, rules, and staff decisions.', output: 'A complete situational menu.' },
    { id: 'counters', title: 'Counters and triggers', icon: GitBranch, status: 'Human controlled', description: 'Document what the opponent can do, what adjustment answers it, and what triggers the change.', howItWorks: 'Counter and counter-counter logic stays linked to evidence and an explicit decision owner.', input: 'Scouting evidence, scheme rules, and approved options.', output: 'Actionable adjustment logic.' },
    { id: 'evidence', title: 'Evidence board', icon: Eye, status: 'Source linked', description: 'Keep film, scouting, analytics, and rule evidence beside the decision it supports.', howItWorks: 'Every high-impact plan item exposes its source, confidence, caveat, and review state.', input: 'Verified clips, reports, metrics, and rules.', output: 'Auditable decision context.' },
    { id: 'release', title: 'Approval and snapshot', icon: LockKeyhole, status: 'Approval gated', description: 'Freeze the accepted version for installation and game-day output without silently changing it later.', howItWorks: 'A decision reference locks content and renderer checksums; later changes branch from the release.', input: 'Complete plan, acceptance evidence, and approver.', output: 'Immutable game-plan snapshot and release evidence.' },
  ],
  workflow: [
    { title: 'Prioritize', description: 'Choose situation goals and candidate calls from published systems.' },
    { title: 'Stress test', description: 'Evaluate counters, constraints, evidence quality, and operational risk.' },
    { title: 'Install', description: 'Connect plan items to meetings, film, practice, and player teaching.' },
    { title: 'Approve and lock', description: 'Record the human decision and preserve an immutable game-week snapshot.' },
  ],
  boundary: 'The system organizes options and evidence but does not choose the game plan. Final strategy, publication, and game-day changes remain human decisions.',
};

export const ANALYTICS_WORKSPACE: WorkspaceDefinition = {
  slug: 'analytics', eyebrow: 'Outcome intelligence', title: 'Outcome Analytics', icon: BarChart3, tone: 'violet',
  description: 'Close the loop between intended design, practice execution, game outcomes, player learning, and evidence quality.',
  howItWorks: 'Analysts attach metric observations to source records, preserve denominators and uncertainty, then publish reviewable reports for staff interpretation.',
  audience: 'Analysts, quality control, coordinators, performance staff, and program owners.',
  outcome: 'Lineage-complete observations, uncertainty-aware reports, and an evidence-backed loop from plan to result.',
  metrics: [
    { label: 'Observations', recordKey: 'metric_observations', description: 'Source-linked outcome measurements.' },
    { label: 'Reports', recordKey: 'analytics_reports', description: 'Contextual analyses awaiting staff use.' },
    { label: 'Uncertainty flags', description: 'Observations where sample or lineage needs attention.' },
  ],
  features: [
    { id: 'lineage', title: 'Metric lineage', icon: BadgeCheck, status: 'Evidence linked', description: 'Keep numerator, denominator, context, source, observation IDs, and confidence beside every result.', howItWorks: 'The analytics API rejects invalid metric envelopes and preserves source references when reports are created.', input: 'Provider batches, film observations, practice outcomes, and game records.', output: 'Auditable metric observations.' },
    { id: 'comparison', title: 'Design-to-outcome comparison', icon: ChartNoAxesCombined, status: 'Interactive controls live', description: 'Compare intended calls and teaching objectives with practice and game results without overclaiming causality.', howItWorks: 'Context filters and caveats stay visible so staff can interpret the result against its sample.', input: 'Plan IDs, outcome metrics, situation, and source records.', output: 'Reviewable performance comparisons.' },
    { id: 'reporting', title: 'Staff-ready reporting', icon: NotebookTabs, status: 'Human reviewed', description: 'Turn qualified observations into reports that carry uncertainty and role-specific interpretation requirements.', howItWorks: 'Analysts submit draft reports; staff decide how and whether to apply them.', input: 'Valid observations, audience, context, and caveats.', output: 'A report routed to the decision workflow.' },
    { id: 'uncertainty', title: 'Sample and uncertainty guard', icon: ShieldAlert, status: 'Fail closed', description: 'Keep denominator, confidence, interval, caveat, and lineage visible before an outcome becomes a staff claim.', howItWorks: 'Low sample or incomplete lineage remains a review flag instead of being silently generalized.', input: 'Metric bounds, uncertainty envelope, and source quality.', output: 'An interpretable result with explicit limits.' },
  ],
  workflow: [
    { title: 'Collect', description: 'Ingest authorized observations and keep the source manifest.' },
    { title: 'Validate', description: 'Check bounds, context, sample, and lineage before calculation.' },
    { title: 'Compare', description: 'Relate intended design, execution, learning, and outcome dimensions.' },
    { title: 'Interpret', description: 'Route the report to staff; do not turn a metric into an autonomous football decision.' },
  ],
  boundary: 'Analytics preserves uncertainty and supports decisions. It does not independently grade players, diagnose health, or select calls without qualified human interpretation.',
};

export const DELIVERY_WORKSPACE: WorkspaceDefinition = {
  slug: 'delivery', eyebrow: 'Game-week logistics', title: 'Delivery Center', icon: CalendarDays, tone: 'blue',
  description: 'Coordinate meetings, installs, practices, approvals, exports, and staff ownership across the game week.',
  howItWorks: 'Tasks, release snapshots, practice plans, and delivery packages share one deadline view while the owning system remains authoritative for content and approval.',
  audience: 'Coaches, coordinators, analysts, operations staff, players through approved packets, and program owners.',
  outcome: 'A visible game-week calendar, accountable deadlines, delivery packet checklist, and completion evidence.',
  metrics: [
    { label: 'Open tasks', description: 'Scheduled delivery responsibilities.' },
    { label: 'Overdue', description: 'Deadlines needing immediate ownership.' },
    { label: 'Locked releases', description: 'Approved plan snapshots ready for delivery.' },
  ],
  features: [
    { id: 'calendar', title: 'Game-week calendar', icon: CalendarDays, status: 'Interactive controls live', description: 'See tasks by due time, category, priority, owner, and linked football artifact.', howItWorks: 'The API computes due state from authenticated organization task records and exposes overdue work explicitly.', input: 'Task deadlines, owners, priorities, and week context.', output: 'A sortable delivery schedule.' },
    { id: 'packets', title: 'Delivery packet checklist', icon: FileCheck2, status: 'Reference-aware', description: 'Track coach, player, coordinator, wristband, and administrator outputs against the weekly package.', howItWorks: 'Packet output types are visible beside release and practice readiness without silently generating or sending files.', input: 'Approved snapshots, practice plans, call sheets, and exports.', output: 'A human-controlled handoff checklist.' },
    { id: 'ownership', title: 'Ownership and completion', icon: BadgeCheck, status: 'Audited', description: 'Assign one accountable owner, record completion, and preserve the note and timestamp.', howItWorks: 'Task completion is an authenticated mutation that writes audit history and leaves the linked record unchanged.', input: 'Owner, due time, and completion evidence.', output: 'A reliable responsibility trail.' },
    { id: 'readiness', title: 'Release readiness', icon: LockKeyhole, status: 'Approval aware', description: 'Keep packet assembly beside the release lock, practice plan, and unresolved blockers that can stop a handoff.', howItWorks: 'The center summarizes readiness while approval and export actions remain in their owning workspaces.', input: 'Locked snapshots, packages, practice plans, and blockers.', output: 'A visible handoff gate.' },
  ],
  workflow: [
    { title: 'Plan', description: 'Create deadlines for film, install, practice, scouting, approval, and delivery.' },
    { title: 'Assign', description: 'Put one accountable person and priority on every task.' },
    { title: 'Verify', description: 'Check linked artifacts, release state, and packet readiness.' },
    { title: 'Complete', description: 'Record the handoff result and return unresolved blockers to the inbox.' },
  ],
  boundary: 'The delivery center orchestrates work and packet readiness. It does not publish a plan, email a player, notify an external provider, or override approval gates by itself.',
};

export const PLAYER_WORKSPACE: WorkspaceDefinition = {
  slug: 'player', eyebrow: 'Role-specific teaching', title: 'Player Development', icon: GraduationCap, tone: 'cyan',
  description: 'Give each player the exact assignments, teaching progressions, film, practice work, and feedback appropriate to their role.',
  howItWorks: 'Role filters reduce staff information into safe player views, then connect instruction, quiz evidence, practice execution, and coach review into a mastery loop.',
  audience: 'Players, position coaches, coordinators, player-development staff, and qualified performance staff.',
  outcome: 'Daily assignments, role-specific play views, teaching playlists, quiz evidence, mastery progress, and reviewed development plans.',
  metrics: [
    { label: 'Assignments', recordKey: 'player_assignments', description: 'Role- and privacy-scoped daily work.' },
    { label: 'Quiz attempts', recordKey: 'film_quiz_attempts', description: 'Teaching checks awaiting or carrying review.' },
    { label: 'Mastery records', recordKey: 'mastery_records', description: 'Evidence-linked development progress.' },
  ],
  features: [
    { id: 'today', title: 'Player Today', icon: Sparkles, status: 'Privacy scoped', description: 'Show only the meetings, assignments, corrections, and preparation relevant to the signed-in player.', howItWorks: 'The API filters by organization, subject, role, and assignment visibility before returning content.', input: 'Approved staff assignments and player identity.', output: 'A focused daily plan.' },
    { id: 'teaching', title: 'Role teaching view', icon: BookOpenCheck, status: 'Backend operational', description: 'Reduce a full play to the player’s alignment, assignment, key, timing, coaching cue, and adjustment.', howItWorks: 'Canonical play elements are filtered by role while shared context remains available when authorized.', input: 'Published play and role mapping.', output: 'Accessible diagrams and step-by-step teaching.' },
    { id: 'quiz', title: 'Checks for understanding', icon: BrainCircuit, status: 'Coach reviewed', description: 'Measure recognition and decision process without treating a quiz score as complete mastery.', howItWorks: 'Prompts link to plays or clips; attempts preserve evidence and route uncertainty to a coach.', input: 'Approved teaching material and measurable prompt.', output: 'Reviewable understanding evidence.' },
    { id: 'mastery', title: 'Mastery and development plan', icon: BarChart3, status: 'Evidence linked', description: 'Track progression across knowledge, decision speed, technique, execution, consistency, and adaptability.', howItWorks: 'Coaches combine multiple evidence types and set reviewed objectives, progressions, and checkpoints.', input: 'Film, practice, quiz, coaching, and performance evidence.', output: 'A human-reviewed development path.' },
  ],
  workflow: [
    { title: 'Assign', description: 'Staff publish role-specific work and teaching objectives.' },
    { title: 'Learn', description: 'The player studies filtered diagrams, film, cues, and adjustments.' },
    { title: 'Demonstrate', description: 'Quizzes, practice, and film provide multiple forms of evidence.' },
    { title: 'Review', description: 'A coach interprets evidence and updates the development plan.' },
  ],
  boundary: 'Privacy, role visibility, medical boundaries, and coach authority apply throughout. Automated outputs support teaching but never independently grade or discipline a player.',
};

export const ADMIN_WORKSPACE: WorkspaceDefinition = {
  slug: 'admin', eyebrow: 'Controlled operations', title: 'Admin & Governance', icon: Settings2, tone: 'violet',
  description: 'Manage organization configuration, approvals, terminology, permissions, source controls, system readiness, and auditable human authority.',
  howItWorks: 'Owner-only controls compose governed records and evidence while stage gates, role boundaries, and production safeguards fail closed.',
  audience: 'Program owners, approved administrators, validators, security, and deployment owners.',
  outcome: 'Controlled organization configuration, decision evidence, permission state, readiness reports, and audit history.',
  metrics: [
    { label: 'Pending reviews', description: 'Human decisions waiting in the approval queue.' },
    { label: 'Authorized sources', recordKey: 'knowledge_sources', description: 'Registered evidence and media origins.' },
    { label: 'Audit events', recordKey: 'audit_events', description: 'Organization-scoped operational history.' },
  ],
  features: [
    { id: 'organization', title: 'Organization setup', icon: MonitorCog, status: 'Owner controlled', description: 'Configure season, roster, staff, terminology, doctrine, and organization-specific operating context.', howItWorks: 'Draft records progress through explicit validation and decision references before becoming accepted context.', input: 'Verified organization records and accountable owners.', output: 'An approved organization operating bundle.' },
    { id: 'approvals', title: 'Approval center', icon: FileCheck2, status: 'Human required', description: 'Review plays, packages, sources, changes, releases, and exceptions that require accountable authority.', howItWorks: 'Each decision retains alternatives, evidence, approver, scope, and audit history.', input: 'A controlled artifact and complete acceptance evidence.', output: 'Approved, rejected, or returned decision state.' },
    { id: 'permissions', title: 'Roles and permissions', icon: ShieldCheck, status: 'Fail closed', description: 'Control which roles can see, create, review, publish, export, or administer each resource.', howItWorks: 'API authorization combines token role, organization scope, resource state, and action-specific policy.', input: 'Approved role assignments and access policy.', output: 'Auditable least-privilege access decisions.' },
    { id: 'readiness', title: 'Operational readiness', icon: Gauge, status: 'Deployment gated', description: 'Inspect database, secrets, monitoring, schedulers, media tools, rollback, pilots, and Stage 0 authorization.', howItWorks: 'Independent checks compose a value-free readiness report and block when required external evidence is absent.', input: 'Deployment-owned registrations and local validation evidence.', output: 'A non-activating readiness report with explicit blockers.' },
  ],
  workflow: [
    { title: 'Configure', description: 'Create organization-scoped drafts with stable IDs and accountable ownership.' },
    { title: 'Validate', description: 'Run structural, security, evidence, and readiness checks.' },
    { title: 'Approve', description: 'Record a qualified human decision without inferring authorization.' },
    { title: 'Audit', description: 'Preserve immutable evidence, history, and rollback boundaries.' },
  ],
  boundary: 'This page never auto-advances Stage 0, activates production, registers external providers, or replaces the required program-owner and deployment-owner decisions.',
};

export const INBOX_WORKSPACE: WorkspaceDefinition = {
  slug: 'inbox', eyebrow: 'Cross-system operations', title: 'Operations Inbox', icon: BellRing, tone: 'cyan',
  description: 'Turn reviews, due work, validation failures, source freshness, practice preparation, and game-plan decisions into one accountable work queue.',
  howItWorks: 'The API aggregates organization-scoped records, applies role visibility, calculates urgency and due state, and links each item to its owning workspace without performing silent approvals or external actions.',
  audience: 'Coaches, analysts, validators, performance staff, players, and program owners with role-scoped work.',
  outcome: 'Prioritized work, explicit ownership, visible blockers, unread notifications, and one-click movement to the authoritative system of record.',
  metrics: [
    { label: 'Pending decisions', description: 'Review work currently waiting for a human decision.' },
    { label: 'Validation findings', description: 'Stale or blocked evidence requiring attention.' },
    { label: 'Audit events', recordKey: 'audit_events', description: 'Organization-scoped activity retained for traceability.' },
  ],
  features: [
    { id: 'priority-queue', title: 'Priority queue', icon: ListChecks, status: 'Interactive controls live', description: 'Sort work by urgency, due state, status, and ownership so the next accountable action is obvious.', howItWorks: 'Each item receives deterministic urgency and due-state labels from its record status, priority, and due timestamp.', input: 'Organization records and workflow state.', output: 'A role-filtered, prioritized queue.' },
    { id: 'deep-links', title: 'Deep-linked actions', icon: Target, status: 'Interactive controls live', description: 'Move from an inbox item directly into Film, Practice, Scouting, Game Plan, Player, Playbook, or Admin.', howItWorks: 'Every item carries an owning collection, record identity, action label, and safe route target.', input: 'Canonical record identity and owning workflow.', output: 'One-click context-preserving navigation.' },
    { id: 'notifications', title: 'Notifications', icon: BellRing, status: 'Read state live', description: 'Surface unread organization notifications and preserve who acknowledged them and when.', howItWorks: 'Authenticated recipients can mark notification records read; the action is audited and never changes the underlying workflow state.', input: 'Recipient-scoped notification records.', output: 'Visible unread count and auditable read state.' },
    { id: 'automation-boundary', title: 'Safe workflow automation', icon: ShieldCheck, status: 'Fail closed', description: 'Prioritize and route work without silently approving, publishing, changing player status, or changing external provider state.', howItWorks: 'The inbox is an orchestration surface; domain-specific APIs remain authoritative for every high-impact transition.', input: 'Role, tenant, status, evidence, and policy boundaries.', output: 'Actionable work without hidden authority escalation.' },
  ],
  workflow: [
    { title: 'Triage', description: 'Filter the queue by urgency, due state, category, assignment, or unread notification.' },
    { title: 'Inspect', description: 'Review blockers, evidence, owner, status, and the source record before acting.' },
    { title: 'Open', description: 'Follow the deep link into the owning workflow and use its domain-specific controls.' },
    { title: 'Verify', description: 'Return to the inbox to confirm the item, notification, or decision state changed as expected.' },
  ],
  boundary: 'This inbox prioritizes and links work; it does not silently approve, publish, lock, alter player status, or change external provider state. Those transitions remain human-controlled and API-authoritative.',
};

export const COLLABORATION_WORKSPACE: WorkspaceDefinition = {
  slug: 'collaboration', eyebrow: 'Connected staff operations', title: 'Staff Collaboration', icon: MessageSquareText, tone: 'violet',
  description: 'Coordinate cross-system decisions with context-rich threads, assignments, mentions, notifications, presence, and an auditable activity feed.',
  howItWorks: 'The collaboration service stores organization-scoped discussion and coordination records, links them to the owning workflow, notifies accountable people, and preserves activity without taking over domain approval authority.',
  audience: 'Coaches, coordinators, analysts, validators, performance staff, program owners, and players with scoped visibility.',
  outcome: 'Fewer lost decisions, clearer ownership, faster response to blockers, and a shared record of what changed and why.',
  metrics: [
    { label: 'Pending decisions', description: 'Open threads waiting for context, action, or a domain decision.' },
    { label: 'Validation findings', description: 'Unread mentions, assignments, and follow-up signals requiring attention.' },
    { label: 'Audit events', recordKey: 'audit_events', description: 'Organization-scoped collaboration activity retained for traceability.' },
  ],
  features: [
    { id: 'threads', title: 'Cross-system threads', icon: MessageSquareText, status: 'Interactive controls live', description: 'Keep a decision, question, correction, or handoff attached to its source play, clip, practice plan, game plan, roster record, or delivery task.', howItWorks: 'A thread stores the entity type, entity identity, safe owning route, comments, participants, priority, and status.', input: 'A football record and a staff question or decision.', output: 'An auditable discussion with a one-click route back to the source.', },
    { id: 'assignments', title: 'Accountability and due dates', icon: CheckCircle2, status: 'Interactive controls live', description: 'Turn discussion into an accountable next action with explicit assignee, priority, and deadline.', howItWorks: 'Assignments update the thread, add the responsible person to participants, create a notification, and remain visible in Operations Inbox.', input: 'Thread context, owner, urgency, and due timestamp.', output: 'A visible work obligation with auditable assignment history.', },
    { id: 'notifications', title: 'Mentions and notifications', icon: BellRing, status: 'Read state live', description: 'Notify people about new threads, replies, mentions, and assignments while retaining acknowledgment state.', howItWorks: 'Notifications are recipient-scoped organization records; reading one records who acknowledged it and when without changing the underlying decision.', input: 'Thread participants, assignees, and mentions.', output: 'Unread alerts with safe links to the collaboration thread.', },
    { id: 'presence', title: 'Presence and activity', icon: UsersRound, status: 'Live heartbeat', description: 'Show active staff sessions and a recent activity feed so coordination reflects the current room.', howItWorks: 'Presence heartbeats expire automatically, while durable events preserve thread, comment, assignment, and resolution history.', input: 'Authenticated session heartbeat and collaboration events.', output: 'Current staff presence plus a durable activity timeline.', },
  ],
  workflow: [
    { title: 'Open context', description: 'Start a thread from the record that needs a decision, correction, or handoff.' },
    { title: 'Coordinate', description: 'Mention the right people, reply with evidence, and keep uncertainty explicit.' },
    { title: 'Assign', description: 'Set accountable ownership, urgency, and due date; the Operations Inbox receives the work signal.' },
    { title: 'Resolve', description: 'Record the outcome and rationale while the owning football workflow remains authoritative.' },
  ],
  boundary: 'Collaboration does not silently approve, publish, lock, validate, alter player status, or mutate the linked football artifact. Those transitions remain in their domain-specific services.',
};

export const REVIEWS_WORKSPACE: WorkspaceDefinition = {
  slug: 'reviews', eyebrow: 'Human decision center', title: 'Reviews & Approvals', icon: ClipboardCheck, tone: 'amber',
  description: 'See what needs a human decision, why it is blocked, what evidence supports it, and which role has authority to act.',
  howItWorks: 'The queue aggregates reviewable organization records while preserving resource-specific approval, permission, and audit rules.',
  audience: 'Coaching staff, analysts, validators, program owners, and other explicitly authorized reviewers.',
  outcome: 'Documented decisions, returned corrections, linked evidence, and auditable approval state.',
  metrics: [
    { label: 'Pending decisions', description: 'Current organization records awaiting review.' },
    { label: 'Validation findings', description: 'Blocking or warning conditions requiring attention.' },
    { label: 'Approved releases', recordKey: 'release_records', description: 'Immutable artifacts with decision evidence.' },
  ],
  features: [
    { id: 'queue', title: 'Decision queue', icon: ListChecks, status: 'Role filtered', description: 'Prioritize review work by resource, severity, deadline, and responsible authority.', howItWorks: 'The API returns only organization-scoped records the signed-in role may inspect.', input: 'Review requests from football and operating systems.', output: 'An accountable reviewer worklist.' },
    { id: 'evidence', title: 'Evidence packet', icon: Eye, status: 'Required', description: 'Inspect source links, validation findings, alternatives, changes, and acceptance evidence beside the decision.', howItWorks: 'Evidence references resolve without copying or hiding their classification and uncertainty.', input: 'Artifact, sources, validations, and prior decisions.', output: 'Decision-ready context.' },
    { id: 'discussion', title: 'Staff discussion', icon: MessageSquareText, status: 'Auditable', description: 'Ask questions, request corrections, and resolve review threads without losing history.', howItWorks: 'Comments remain linked to the artifact or specific element and carry an explicit resolution state.', input: 'Reviewer notes and artifact references.', output: 'Resolved questions or a documented return request.' },
    { id: 'decision', title: 'Approval decision', icon: LockKeyhole, status: 'Authority required', description: 'Approve, reject, or return work with a decision reference and accountable actor.', howItWorks: 'The server rechecks role, organization, artifact state, and required evidence at action time.', input: 'Complete review packet and qualified reviewer.', output: 'Auditable controlled state transition.' },
  ],
  workflow: [
    { title: 'Triage', description: 'Identify urgency, authority, blockers, and missing evidence.' },
    { title: 'Inspect', description: 'Review the artifact, diffs, sources, findings, and discussion.' },
    { title: 'Decide', description: 'Approve, reject, or return with an explicit reference and rationale.' },
    { title: 'Verify', description: 'Confirm the resulting state, immutable evidence, and downstream effects.' },
  ],
  boundary: 'Visibility never grants approval authority. Every state-changing decision is re-authorized by the Python API and preserved in organization-scoped audit history.',
};

/** Canonical definitions shared by workspace pages, tutorials, and future onboarding surfaces. */
export const ALL_WORKSPACE_DEFINITIONS: WorkspaceDefinition[] = [
  INBOX_WORKSPACE,
  ROSTER_WORKSPACE,
  ANALYTICS_WORKSPACE,
  DELIVERY_WORKSPACE,
  COLLABORATION_WORKSPACE,
  FILM_WORKSPACE,
  PRACTICE_WORKSPACE,
  SCOUTING_WORKSPACE,
  GAME_PLAN_WORKSPACE,
  PLAYER_WORKSPACE,
  ADMIN_WORKSPACE,
  REVIEWS_WORKSPACE,
];
