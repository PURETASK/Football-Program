import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, ClipboardCheck, GitCompareArrows, LockKeyhole, MessageCirclePlus, Reply, ShieldAlert } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';

import { useSession } from '../auth/SessionContext';
import {
  MutationNotice,
  RecordInspector,
  RecordList,
  WorkbenchFrame,
  WorkbenchState,
  WorkbenchStats,
  WorkbenchTabs,
} from '../components/OperationalWorkbench';
import { useGamePlanDataQuery, useGamePlanReleaseRoomQuery } from '../hooks/useOperationalData';
import { approveGamePlanReleaseSnapshot, commentOnGamePlanThread, createGamePlanReleaseSnapshot, createGamePlanThread, resolveGamePlanThread, rollbackGamePlanReleaseSnapshot } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import { compareReleaseSnapshots } from '../lib/releaseDiff';
import type { FootballRecord, GamePlanComment, GamePlanReleaseSnapshot, GamePlanThread } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { GAME_PLAN_WORKSPACE } from './workspaceDefinitions';

import '../styles/game-plan.css';

type GamePlanTab = 'plan' | 'situations' | 'evidence' | 'collaboration' | 'release';

function arrayRecords(value: unknown): FootballRecord[] {
  return Array.isArray(value) ? value.map((item, index) => typeof item === 'object' && item !== null ? { id: String((item as FootballRecord).id || `ITEM-${index + 1}`), ...(item as Record<string, unknown>) } as FootballRecord : { id: `ITEM-${index + 1}`, title: String(item) }) : [];
}

function ReleaseEvidencePicker({ options, value, onChange }: { options: Array<{ id: string; label: string }>; value: string[]; onChange: (ids: string[]) => void }) {
  return <label className="is-wide"><span>Choose release evidence <small>scouting, analytics, rules, delivery, or release records</small></span><select aria-label="Release evidence references" className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); onChange(ids); const input = event.currentTarget.form?.elements.namedItem('artifact_refs') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, options.length || 4))} value={value}>{options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>;
}

export function GamePlanPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const gamePlanQuery = useGamePlanDataQuery();
  const releaseQuery = useGamePlanReleaseRoomQuery();
  const recordQuery = new URLSearchParams(window.location.search);
  const [tab, setTab] = useState<GamePlanTab>('plan');
  const [selectedPlanId, setSelectedPlanId] = useState(() => recordQuery.get('record') || '');
  const [selectedThreadId, setSelectedThreadId] = useState('');
  const [selectedReleaseId, setSelectedReleaseId] = useState('');
  const [compareBaseId, setCompareBaseId] = useState('');
  const [releaseEvidenceIds, setReleaseEvidenceIds] = useState<string[]>([]);
  const data = gamePlanQuery.data;
  const workspace = data?.workspace;
  const collaboration = data?.collaboration;
  const selectedPlan = workspace?.plans.find((plan) => plan.id === selectedPlanId) ?? workspace?.plans[0];
  const selectedThread = collaboration?.threads.find((thread) => thread.id === selectedThreadId) ?? collaboration?.threads[0];
  const selectedRelease = releaseQuery.data?.snapshots.find((snapshot) => snapshot.id === selectedReleaseId) ?? releaseQuery.data?.latest_snapshot;
  const compareBase = releaseQuery.data?.snapshots.find((snapshot) => snapshot.id === compareBaseId)
    ?? releaseQuery.data?.snapshots.find((snapshot) => snapshot.id === selectedRelease?.previous_snapshot_id)
    ?? releaseQuery.data?.snapshots.find((snapshot) => snapshot.id !== selectedRelease?.id);
  const releaseChanges = useMemo(() => compareReleaseSnapshots(compareBase, selectedRelease), [compareBase, selectedRelease]);
  const canCollaborate = Boolean(session && ['program_owner', 'coach_staff', 'analyst', 'validator'].includes(session.role));
  const canResolve = Boolean(session && ['program_owner', 'coach_staff', 'validator'].includes(session.role));
  const canRelease = Boolean(session && ['program_owner', 'coach_staff'].includes(session.role));
  const isOwner = session?.role === 'program_owner';
  const situationRecords = useMemo(() => arrayRecords(selectedPlan?.situational_plans), [selectedPlan]);
  const evidencePackages = useMemo(() => [
    { label: 'Scouting reports', records: workspace?.scouting_reports ?? [] },
    { label: 'Metric observations', records: workspace?.metric_observations ?? [] },
    { label: 'Rule recommendations', records: workspace?.rule_recommendations ?? [] },
    { label: 'Weekly deliveries', records: workspace?.weekly_deliveries ?? [] },
    { label: 'Release candidates', records: workspace?.release_candidates ?? [] },
  ], [workspace?.metric_observations, workspace?.release_candidates, workspace?.rule_recommendations, workspace?.scouting_reports, workspace?.weekly_deliveries]);
  const releaseEvidenceOptions = useMemo(() => evidencePackages.flatMap((group) => group.records.map((record) => ({ id: record.id, label: recordLabel(record) + ' - ' + group.label + ' - ' + sentenceCase(String(record.status || 'record')) }))).filter((option, index, all) => all.findIndex((candidate) => candidate.id === option.id) === index), [evidencePackages]);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['game-plan-workspace', session?.organizationId] });
  const threadMutation = useMutation({ mutationFn: (values: Parameters<typeof createGamePlanThread>[1]) => createGamePlanThread(session!, values), onSuccess: refresh });
  const replyMutation = useMutation({ mutationFn: (values: Parameters<typeof commentOnGamePlanThread>[1]) => commentOnGamePlanThread(session!, values), onSuccess: refresh });
  const resolveMutation = useMutation({ mutationFn: (values: Parameters<typeof resolveGamePlanThread>[1]) => resolveGamePlanThread(session!, values), onSuccess: refresh });
  const releaseMutation = useMutation({ mutationFn: (values: Parameters<typeof createGamePlanReleaseSnapshot>[1]) => createGamePlanReleaseSnapshot(session!, values), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['game-plan-release-room', session?.organizationId] }); setTab('release'); } });
  const approveReleaseMutation = useMutation({ mutationFn: (snapshotId: string) => approveGamePlanReleaseSnapshot(session!, snapshotId, recordId('DEC-')), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['game-plan-release-room', session?.organizationId] }) });
  const rollbackReleaseMutation = useMutation({ mutationFn: (snapshotId: string) => rollbackGamePlanReleaseSnapshot(session!, snapshotId, recordId('DEC-')), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['game-plan-release-room', session?.organizationId] }) });

  function submitThread(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    threadMutation.mutate({
      threadId: recordId('GAMEPLAN-THREAD-'),
      planId: String(form.get('plan_id') || ''),
      week: String(form.get('week') || ''),
      topic: String(form.get('topic') || ''),
      comment: String(form.get('comment') || ''),
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
    });
  }

  function submitReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedThread) return;
    const form = new FormData(event.currentTarget);
    replyMutation.mutate({
      threadId: selectedThread.id,
      commentId: recordId('COMMENT-'),
      comment: String(form.get('comment') || ''),
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
    });
  }

  function submitResolution(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedThread) return;
    const form = new FormData(event.currentTarget);
    resolveMutation.mutate({
      threadId: selectedThread.id,
      decision: String(form.get('decision')) as 'accepted' | 'deferred' | 'rejected',
      decisionRef: recordId('DEC-'),
      rationale: String(form.get('rationale') || ''),
    });
  }

  function submitReleaseSnapshot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    releaseMutation.mutate({
      snapshotId: recordId('RELEASE-SNAPSHOT-'),
      planId: String(form.get('plan_id') || ''),
      week: String(form.get('week') || ''),
      note: String(form.get('note') || ''),
      artifactRefs: splitList(String(form.get('artifact_refs') || '')),
    });
  }

  return (
    <WorkspacePage definition={GAME_PLAN_WORKSPACE}>
      <WorkbenchFrame
        actions={<button className="button button--primary" disabled={!canCollaborate} onClick={() => setTab('collaboration')} type="button"><MessageCirclePlus size={15} /> Staff review</button>}
        description="Inspect the complete weekly plan, drill into situational counters, verify its evidence chain, and resolve staff questions through governed threads."
        eyebrow="Live weekly operations"
        icon={ClipboardCheck}
        title="Game-plan command board"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Game Plan views"
          onChange={(next) => setTab(next as GamePlanTab)}
          tabs={[
            { id: 'plan', label: 'Weekly plan', count: workspace?.plans.length },
            { id: 'situations', label: 'Situations & counters', count: situationRecords.length },
            { id: 'evidence', label: 'Evidence & release', count: workspace?.pending_review_count },
            { id: 'collaboration', label: 'Staff threads', count: collaboration?.open_thread_count },
            { id: 'release', label: 'Release room', count: releaseQuery.data?.snapshots.length },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={gamePlanQuery.error} loading={gamePlanQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Weekly plans', value: workspace?.plans.length ?? 0, hint: 'organization corpus' },
              { label: 'Pending review', value: workspace?.pending_review_count ?? 0, hint: 'controlled decisions' },
              { label: 'Open threads', value: collaboration?.open_thread_count ?? 0, hint: 'staff collaboration' },
              { label: 'Blockers', value: workspace?.blockers.length ?? 0, hint: 'release constraints' },
            ]} />

            {(tab === 'plan' || tab === 'situations') ? (
              <div className="workbench-split">
                <div className="workbench-pane workbench-pane--soft">
                  <div className="workbench-pane__header"><div><h3>Weekly plans</h3><p>Choose the plan that owns the current call sheet and teaching output.</p></div></div>
                  <RecordList
                    emptyMessage="No weekly game plan exists for this organization."
                    onSelect={(plan) => setSelectedPlanId(plan.id)}
                    records={workspace?.plans ?? []}
                    selectedId={selectedPlan?.id}
                    subtitle={(plan) => `${plan.week_context || plan.week || 'No week'} · ${compactValue(plan.team_context)}`}
                    title={recordLabel}
                  />
                </div>
                <div className="workbench-pane">
                  {selectedPlan && tab === 'plan' ? (
                    <RecordInspector
                      eyebrow="Weekly game plan"
                      facts={[
                        { label: 'Week', value: compactValue(selectedPlan.week_context || selectedPlan.week) },
                        { label: 'Identity', value: compactValue(selectedPlan.identity) },
                        { label: 'Offense', value: compactValue(selectedPlan.offense) },
                        { label: 'Defense', value: compactValue(selectedPlan.defense) },
                        { label: 'Opening script', value: compactValue(selectedPlan.opening_script) },
                        { label: 'Pressure answers', value: compactValue(selectedPlan.pressure_answers) },
                        { label: 'Matchups', value: compactValue(selectedPlan.matchups) },
                        { label: 'Teaching output', value: compactValue(selectedPlan.teaching_outputs) },
                      ]}
                      note="The command board is an inspection and collaboration surface. Canonical publishing and approval continue through their specific governed workflow."
                      status={selectedPlan.status}
                      title={recordLabel(selectedPlan)}
                    />
                  ) : selectedPlan && tab === 'situations' ? (
                    <RecordInspector
                      eyebrow="Situation tree"
                      facts={[
                        { label: 'Base calls', value: compactValue(selectedPlan.base_calls) },
                        { label: 'Shot plan', value: compactValue(selectedPlan.shot_plan) },
                        { label: 'Contingencies', value: compactValue(selectedPlan.contingencies) },
                        { label: 'In-game update', value: compactValue(selectedPlan.in_game_update) },
                      ]}
                      note="Every primary answer is shown with the opponent response and counter so staff can evaluate the full decision tree."
                      status={selectedPlan.status}
                      title="Situation and counter matrix"
                    >
                      <ul className="evidence-stack">
                        {situationRecords.map((situation) => <li key={situation.id}><strong>{sentenceCase(String(situation.situation || situation.id))}</strong><span>Primary: {compactValue(situation.primary)} · Responses: {compactValue(situation.opponent_responses)} · Counters: {compactValue(situation.counters)}</span></li>)}
                      </ul>
                    </RecordInspector>
                  ) : <div className="record-list__empty">Select a weekly plan to inspect.</div>}
                </div>
              </div>
            ) : null}

            {tab === 'evidence' ? (
              <div className="workbench-split">
                <div className="workbench-pane workbench-pane--soft">
                  <div className="workbench-pane__header"><div><h3>Evidence envelope</h3><p>Inputs and release controls used by the weekly plan.</p></div></div>
                  <ul className="evidence-stack">
                    {evidencePackages.map((group) => <li key={group.label}><strong>{group.label}</strong><span>{group.records.length} records · {group.records.filter((record) => ['under_review', 'blocked', 'pending_approval'].includes(record.status || '')).length} pending</span></li>)}
                  </ul>
                </div>
                <div className="workbench-pane">
                  <RecordInspector
                    eyebrow="Release readiness"
                    facts={[
                      { label: 'Scouting reports', value: workspace?.evidence_summary.scouting_reports ?? 0 },
                      { label: 'Metric observations', value: workspace?.evidence_summary.metric_observations ?? 0 },
                      { label: 'Rule recommendations', value: workspace?.evidence_summary.rule_recommendations ?? 0 },
                      { label: 'Human approval', value: workspace?.human_approval_required ? 'Required' : 'Not currently required' },
                    ]}
                    note="A release blocker is never hidden or converted into an automatic approval. Resolve evidence and workflow-specific gates before publication."
                    status={workspace?.blockers.length ? 'blocked' : 'ready'}
                    title="Game-plan release envelope"
                  >
                    {workspace?.blockers.length ? <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> {workspace.blockers.map(compactValue).join(' · ')}</div> : null}
                  </RecordInspector>
                </div>
              </div>
            ) : null}

            {tab === 'release' ? (
              <>
                <div className="approval-boundary"><LockKeyhole aria-hidden="true" size={17} /> {releaseQuery.data?.boundary || 'A release snapshot is immutable evidence and requires an accountable human approval.'}</div>
                <WorkbenchStats stats={[
                  { label: 'Snapshots', value: releaseQuery.data?.snapshots.length ?? 0, hint: 'versioned release evidence' },
                  { label: 'Pending approval', value: releaseQuery.data?.pending_approval_count ?? 0, hint: 'owner decision required' },
                  { label: 'Locked releases', value: releaseQuery.data?.locked_count ?? 0, hint: 'approved snapshots' },
                  { label: 'Rollback', value: releaseQuery.data?.rollback_available ? 'Available' : 'Unavailable', hint: 'owner-controlled' },
                ]} />
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <div className="workbench-pane__header"><div><h3>Release snapshots</h3><p>Each snapshot stores a content hash, renderer version, source plan, and change summary.</p></div></div>
                    <RecordList
                      emptyMessage="No release snapshots have been created for this organization."
                      records={releaseQuery.data?.snapshots ?? []}
                      onSelect={(snapshot) => setSelectedReleaseId(snapshot.id)}
                      selectedId={selectedRelease?.id}
                      subtitle={(snapshot) => `${snapshot.week} · ${snapshot.locked ? 'locked' : 'pending decision'} · ${snapshot.content_hash?.slice(0, 10) || 'no hash'}`}
                      title={(snapshot) => snapshot.note || snapshot.id}
                    />
                  </div>
                  <div className="workbench-pane">
                    {selectedRelease ? (
                      <RecordInspector
                        eyebrow="Latest release evidence"
                        facts={[
                          { label: 'Snapshot', value: selectedRelease.id },
                          { label: 'Plan', value: selectedRelease.plan_id },
                          { label: 'State', value: selectedRelease.locked ? 'Immutable / locked' : sentenceCase(selectedRelease.status) },
                          { label: 'Renderer', value: selectedRelease.renderer_version || 'Unknown' },
                          { label: 'Changed fields', value: selectedRelease.what_changed?.join(', ') || 'No diff recorded' },
                          { label: 'Linked dependencies', value: `${selectedRelease.dependency_manifest?.linked_count ?? 0}/${selectedRelease.dependency_manifest?.artifact_count ?? 0}` },
                          { label: 'Evidence gaps', value: selectedRelease.dependency_manifest?.unresolved_refs?.join(', ') || 'None declared' },
                          { label: 'Manifest checksum', value: selectedRelease.release_manifest_hash?.slice(0, 16) || 'Not available' },
                        ]}
                        note="Compare before approval. A later edit creates a new snapshot; it never silently mutates this release."
                        status={selectedRelease.status}
                        title={selectedRelease.note || selectedRelease.id}
                      >
                        <div className="workbench-toolbar__group">
                          {isOwner && selectedRelease.status === 'pending_approval' ? <button className="button button--primary" disabled={approveReleaseMutation.isPending} onClick={() => approveReleaseMutation.mutate(selectedRelease.id)} type="button"><CheckCircle2 size={14} /> Approve and lock</button> : null}
                          {isOwner && selectedRelease.status === 'approved' ? <button className="button button--secondary" disabled={rollbackReleaseMutation.isPending} onClick={() => rollbackReleaseMutation.mutate(selectedRelease.id)} type="button"><GitCompareArrows size={14} /> Roll back</button> : null}
                        </div>
                        <MutationNotice error={approveReleaseMutation.error || rollbackReleaseMutation.error} pending={approveReleaseMutation.isPending || rollbackReleaseMutation.isPending} success={approveReleaseMutation.isSuccess || rollbackReleaseMutation.isSuccess} successMessage="Release state updated with an owner decision." />
                        <div className="release-diff-panel">
                          <div className="workbench-pane__header"><div><h4><GitCompareArrows aria-hidden="true" size={15} /> Visual change comparison</h4><p>Compare this immutable source-plan snapshot with its prior frozen version before approval.</p></div></div>
                          <label className="filter-select"><span>Compare against</span><select onChange={(event) => setCompareBaseId(event.target.value)} value={compareBase?.id || ''}><option value="">Automatic prior snapshot</option>{(releaseQuery.data?.snapshots ?? []).filter((snapshot) => snapshot.id !== selectedRelease.id).map((snapshot) => <option key={snapshot.id} value={snapshot.id}>{snapshot.id} · {snapshot.status}</option>)}</select></label>
                          {compareBase ? <div className="release-diff-summary"><strong>{releaseChanges.length} field change{releaseChanges.length === 1 ? '' : 's'}</strong><span>{compareBase.id} → {selectedRelease.id}</span></div> : <p className="workbench-form__hint">No prior snapshot is available. This is the initial release comparison boundary.</p>}
                          {releaseChanges.length ? <ul className="release-diff-list">{releaseChanges.map((change) => <li className={`release-diff release-diff--${change.kind}`} key={change.path}><strong>{change.path}</strong><span>{change.before} → {change.after}</span></li>)}</ul> : null}
                        </div>
                      </RecordInspector>
                    ) : <div className="record-list__empty">Create the first release snapshot after the weekly plan is ready.</div>}
                  </div>
                </div>
                {canRelease ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitReleaseSnapshot}>
                    <div className="workbench-pane__header"><div><h3><LockKeyhole aria-hidden="true" size={16} /> Create immutable release snapshot</h3><p>Capture the exact plan version that staff will teach, export, and deliver.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Plan</span><select name="plan_id" required>{workspace?.plans.map((plan) => <option key={plan.id} value={plan.id}>{recordLabel(plan)}</option>)}</select></label>
                      <label><span>Week</span><input defaultValue={String(selectedPlan?.week_context || selectedPlan?.week || 'WEEK-1')} name="week" required /></label>
                      <label className="is-wide"><span>Artifact and evidence refs <small>comma separated</small></span><input name="artifact_refs" placeholder="PLAY-..., SCOUT-..., FILM-..., PRACTICE-..." /></label>
                      <ReleaseEvidencePicker onChange={setReleaseEvidenceIds} options={releaseEvidenceOptions} value={releaseEvidenceIds} />
                      <label className="is-wide"><span>Release note</span><textarea name="note" placeholder="What is this snapshot ready to deliver?" required /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">The snapshot remains pending until a program owner approves it.</p><button className="button button--primary" disabled={releaseMutation.isPending || !workspace?.plans.length} type="submit"><LockKeyhole size={15} /> Create snapshot</button></div>
                    <MutationNotice error={releaseMutation.error} pending={releaseMutation.isPending} success={releaseMutation.isSuccess} successMessage="Release snapshot created and queued for owner approval." />
                  </form>
                ) : <p className="approval-boundary">Release snapshot authoring is available to coaching staff and program owners. Approval and rollback remain owner-only.</p>}
              </>
            ) : null}

            {tab === 'collaboration' ? (
              <>
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <div className="workbench-pane__header"><div><h3>Staff review threads</h3><p>Open questions, evidence, replies, and explicit resolutions.</p></div></div>
                    <RecordList
                      emptyMessage="No game-plan review threads have been opened."
                      onSelect={(thread) => setSelectedThreadId(thread.id)}
                      records={collaboration?.threads ?? []}
                      selectedId={selectedThread?.id}
                      subtitle={(thread) => `${thread.week || 'No week'} · ${thread.comments?.length ?? 0} comments`}
                      title={(thread) => thread.topic || thread.id}
                    />
                  </div>
                  <div className="workbench-pane">
                    {selectedThread ? (
                      <RecordInspector
                        eyebrow="Staff decision thread"
                        facts={[
                          { label: 'Plan', value: compactValue(selectedThread.plan_id) },
                          { label: 'Week', value: compactValue(selectedThread.week) },
                          { label: 'Comments', value: selectedThread.comments?.length ?? 0 },
                          { label: 'Decision', value: compactValue(selectedThread.decision) },
                        ]}
                        status={selectedThread.status}
                        title={selectedThread.topic || selectedThread.id}
                      >
                        <div className="comment-stack">
                          {(selectedThread.comments ?? []).map((comment: GamePlanComment) => <article className="comment-card" key={comment.id}><strong>{comment.author || 'Staff'} · {sentenceCase(comment.role)}</strong><p>{comment.body}</p><small>Evidence: {compactValue(comment.evidence_refs)}</small></article>)}
                        </div>
                      </RecordInspector>
                    ) : <div className="record-list__empty">Select or create a staff thread.</div>}
                  </div>
                </div>

                {canCollaborate ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitThread}>
                    <div className="workbench-pane__header"><div><h3><MessageCirclePlus aria-hidden="true" size={16} /> Open staff review</h3><p>Frame one question against one weekly plan and attach its evidence.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Plan</span><select name="plan_id" required>{workspace?.plans.map((plan) => <option key={plan.id} value={plan.id}>{recordLabel(plan)}</option>)}</select></label>
                      <label><span>Week</span><input defaultValue={String(selectedPlan?.week_context || selectedPlan?.week || 'WEEK-1')} name="week" required /></label>
                      <label className="is-wide"><span>Topic</span><input name="topic" placeholder="Third-down pressure answer" required /></label>
                      <label className="is-wide"><span>Opening comment</span><textarea name="comment" placeholder="State the decision needed, not only the observation." required /></label>
                      <label className="is-wide"><span>Evidence references</span><input name="evidence_refs" placeholder="SCOUT-REPORT-…, FILM-OBS-…" required /></label>
                    </div>
                    <div className="workbench-form__actions"><span /><button className="button button--primary" disabled={threadMutation.isPending || !workspace?.plans.length} type="submit"><MessageCirclePlus size={15} /> Open thread</button></div>
                    <MutationNotice error={threadMutation.error} pending={threadMutation.isPending} success={threadMutation.isSuccess} successMessage="Staff review thread opened." />
                  </form>
                ) : null}

                {canCollaborate && selectedThread?.status === 'open' ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitReply}>
                    <div className="workbench-pane__header"><div><h3><Reply aria-hidden="true" size={16} /> Reply with evidence</h3><p>Add coaching or analytical context to {selectedThread.id}.</p></div></div>
                    <div className="workbench-form__grid"><label className="is-wide"><span>Comment</span><textarea name="comment" required /></label><label className="is-wide"><span>Evidence references</span><input name="evidence_refs" required /></label></div>
                    <div className="workbench-form__actions"><span /><button className="button button--secondary" disabled={replyMutation.isPending} type="submit"><Reply size={15} /> Add reply</button></div>
                    <MutationNotice error={replyMutation.error} pending={replyMutation.isPending} success={replyMutation.isSuccess} successMessage="Reply added to the staff thread." />
                  </form>
                ) : null}

                {canResolve && selectedThread?.status === 'open' ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitResolution}>
                    <div className="workbench-pane__header"><div><h3><CheckCircle2 aria-hidden="true" size={16} /> Resolve staff decision</h3><p>Close the discussion with an explicit outcome, rationale, actor, and generated decision reference.</p></div></div>
                    <div className="workbench-form__grid"><label><span>Decision</span><select defaultValue="accepted" name="decision"><option>accepted</option><option>deferred</option><option>rejected</option></select></label><label className="is-wide"><span>Rationale</span><textarea name="rationale" required /></label></div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">Resolution is permanent evidence; it is not a publication action.</p><button className="button button--primary" disabled={resolveMutation.isPending} type="submit"><CheckCircle2 size={15} /> Record resolution</button></div>
                    <MutationNotice error={resolveMutation.error} pending={resolveMutation.isPending} success={resolveMutation.isSuccess} successMessage="Staff decision recorded and thread resolved." />
                  </form>
                ) : null}
                {!canCollaborate ? <p className="approval-boundary">Game-plan collaboration requires coaching, analyst, validator, or owner authority.</p> : null}
              </>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
