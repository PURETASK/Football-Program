import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, BookOpenCheck, GraduationCap, LockKeyhole, Plus, Target } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent } from 'react';

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
import { useFilmWorkspaceQuery, usePlayerTodayQuery, usePracticeWorkspaceQuery, useRosterWorkspaceQuery } from '../hooks/useOperationalData';
import { usePlayDesignsQuery } from '../hooks/useWorkspaceData';
import { createPlayerAssignment } from '../lib/api';
import { readEncryptedOfflineCache, writeEncryptedOfflineCache } from '../lib/encryptedOfflineCache';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { FootballRecord, PlayerTodayData } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { PLAYER_WORKSPACE } from './workspaceDefinitions';

type PlayerTab = 'assignments' | 'lessons' | 'mastery' | 'development' | 'quizzes';

function scorePercent(record: FootballRecord): string {
  const score = Number(record.score);
  return Number.isFinite(score) ? `${Math.round(score * 100)}%` : 'Not scored';
}

function PlayerRecordInspector({ record, tab, revealedSteps, onReveal }: { record: FootballRecord; tab: PlayerTab; revealedSteps: number; onReveal: () => void }) {
  const facts = tab === 'assignments'
    ? [
        { label: 'Assignment type', value: sentenceCase(String(record.assignment_type || '')) },
        { label: 'Due date', value: compactValue(record.due_date) },
        { label: 'Learning artifact', value: compactValue(record.artifact_id) },
        { label: 'Coach / owner', value: compactValue(record.owner) },
      ]
    : tab === 'lessons'
      ? [
          { label: 'Position role', value: compactValue(record.learner_role) },
          { label: 'Source play', value: compactValue(record.source_play_id) },
          { label: 'Lesson steps', value: Array.isArray(record.steps) ? record.steps.length : 0 },
          { label: 'Current state', value: sentenceCase(record.status) },
        ]
      : tab === 'mastery'
        ? [
            { label: 'Capability', value: compactValue(record.capability_id) },
            { label: 'Current level', value: sentenceCase(String(record.current_level || '')) },
            { label: 'Target level', value: sentenceCase(String(record.target_level || '')) },
            { label: 'Score', value: scorePercent(record) },
          ]
        : tab === 'development'
          ? [
              { label: 'Objective', value: compactValue(record.objectives) },
              { label: 'Plan owner', value: compactValue(record.owner) },
              { label: 'Status', value: sentenceCase(record.status) },
              { label: 'Player', value: compactValue(record.player_id) },
            ]
          : [
              { label: 'Quiz', value: compactValue(record.quiz_id) },
              { label: 'Score', value: scorePercent(record) },
              { label: 'Participant', value: compactValue(record.participant) },
              { label: 'Review state', value: sentenceCase(record.status) },
            ];
  const steps = Array.isArray(record.steps) ? record.steps as Array<Record<string, unknown>> : [];
  return (
    <RecordInspector eyebrow={`${sentenceCase(tab)} detail`} facts={facts} status={record.status} title={recordLabel(record)}>
      {tab === 'lessons' && steps.length ? (
        <div>
          <p className="eyebrow">Step-by-step reveal</p>
          <ol className="evidence-stack">
            {steps.slice(0, revealedSteps).map((step, index) => <li key={String(step.id || index)}><strong>Step {index + 1}</strong><span>{compactValue(step.instruction)}</span></li>)}
          </ol>
          {revealedSteps < steps.length ? <button className="button button--secondary" onClick={onReveal} type="button">Reveal next step <ArrowRight size={14} /></button> : <p className="mutation-notice mutation-notice--success">All lesson steps are visible. Review the play artifact before marking mastery.</p>}
        </div>
      ) : null}
      {tab === 'mastery' ? <p className="record-inspector__note">Next action: {compactValue(record.next_actions)}</p> : null}
    </RecordInspector>
  );
}

export function PlayerPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const selfId = session?.role === 'player' ? (session.subject || '') : '';
  const canAssign = Boolean(session && ['program_owner', 'coach_staff'].includes(session.role));
  const [playerInput, setPlayerInput] = useState(selfId || 'PLAYER-DEMO-QB-1');
  const [playerId, setPlayerId] = useState(selfId || 'PLAYER-DEMO-QB-1');
  const [assignmentTargetId, setAssignmentTargetId] = useState(selfId || 'PLAYER-DEMO-QB-1');
  const [assignmentType, setAssignmentType] = useState('play_lesson');
  const [artifactId, setArtifactId] = useState('');
  const [sourceRefs, setSourceRefs] = useState('');
  const playerQuery = usePlayerTodayQuery(playerId);
  const rosterQuery = useRosterWorkspaceQuery({}, canAssign);
  const playbookQuery = usePlayDesignsQuery(canAssign);
  const filmQuery = useFilmWorkspaceQuery('', canAssign);
  const practiceQuery = usePracticeWorkspaceQuery('', canAssign);
  const recordQuery = new URLSearchParams(window.location.search);
  const [tab, setTab] = useState<PlayerTab>('assignments');
  const [selectedId, setSelectedId] = useState(() => recordQuery.get('record') || '');
  const [revealedSteps, setRevealedSteps] = useState(1);
  const [cachedData, setCachedData] = useState<PlayerTodayData | null>(null);
  useEffect(() => {
    if (!session) {
      setCachedData(null);
      return undefined;
    }
    let active = true;
    void readEncryptedOfflineCache<PlayerTodayData>(session, `player-today:${playerId}`).then((cached) => {
      if (!active) return;
      setCachedData(cached?.value ?? null);
    });
    return () => { active = false; };
  }, [playerId, session]);
  useEffect(() => {
    if (!session || !playerQuery.data) return;
    void writeEncryptedOfflineCache(session, `player-today:${playerId}`, playerQuery.data, { player_id: playerId, approved_only: true });
  }, [playerId, playerQuery.data, session]);
  const data = playerQuery.data ?? cachedData;
  const usingOfflineCache = !playerQuery.data && Boolean(cachedData);
  const artifactOptions = useMemo(() => {
    const playOptions = (playbookQuery.data ?? []).map((play) => ({ id: play.id, label: `${play.name || play.concept || play.id} · Playbook`, sourceRefs: [play.id] }));
    const filmOptions = [
      ...(filmQuery.data?.playlists ?? []).map((playlist) => ({ id: playlist.id, label: `${playlist.name || playlist.id} · Film playlist`, sourceRefs: [playlist.id, ...(playlist.clip_ids ?? [])] })),
      ...(filmQuery.data?.clips ?? []).map((clip) => ({ id: clip.id, label: `${clip.id} · Film clip`, sourceRefs: [clip.id, ...(clip.asset_id ? [clip.asset_id] : [])] })),
    ];
    const practiceOptions = (practiceQuery.data?.plans ?? []).map((plan) => ({ id: plan.id, label: `${recordLabel(plan)} · Practice plan`, sourceRefs: [plan.id, ...(plan.periods ?? []).flatMap((period) => [...(period.play_ids ?? []), ...(period.drill_ids ?? [])])].filter(Boolean) }));
    if (assignmentType === 'film_playlist' || assignmentType === 'film_quiz') return filmOptions;
    if (assignmentType === 'practice_correction') return practiceOptions;
    return playOptions;
  }, [assignmentType, filmQuery.data?.clips, filmQuery.data?.playlists, playbookQuery.data, practiceQuery.data?.plans]);
  const records = useMemo<FootballRecord[]>(() => tab === 'assignments'
    ? data?.assignments ?? []
    : tab === 'lessons'
      ? data?.lessons ?? []
      : tab === 'mastery'
        ? data?.mastery ?? []
        : tab === 'development'
          ? data?.development_plans ?? []
          : data?.quiz_attempts ?? [], [data, tab]);
  const selected = records.find((record) => record.id === selectedId) ?? records[0];

  const mutation = useMutation({
    mutationFn: (values: Parameters<typeof createPlayerAssignment>[1]) => createPlayerAssignment(session!, values),
    onSuccess: (_assignment, values) => {
      void queryClient.invalidateQueries({ queryKey: ['player-today', session?.organizationId, values.playerId] });
      void queryClient.invalidateQueries({ queryKey: ['player-today', session?.organizationId, playerId] });
    },
  });

  function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const selectedArtifact = artifactOptions.find((option) => option.id === artifactId);
    mutation.mutate({
      assignmentId: recordId('ASSIGNMENT-'),
      playerId: assignmentTargetId || playerId,
      title: String(form.get('title') || ''),
      assignmentType: String(form.get('assignment_type') || ''),
      artifactId: String(form.get('artifact_id') || artifactId),
      dueDate: String(form.get('due_date') || '') || undefined,
      sourceRefs: splitList(String(form.get('source_refs') || '')).length ? splitList(String(form.get('source_refs') || '')) : (selectedArtifact?.sourceRefs ?? []),
    });
  }

  return (
    <WorkspacePage definition={PLAYER_WORKSPACE}>
      <WorkbenchFrame
        description="Deliver a privacy-scoped daily learning path: assigned football work, guided lessons, mastery evidence, development objectives, and film-quiz results."
        eyebrow="Role-filtered teaching workspace"
        icon={GraduationCap}
        title="Player development cockpit"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Player development views"
          onChange={(next) => { setTab(next as PlayerTab); setSelectedId(''); setRevealedSteps(1); }}
          tabs={[
            { id: 'assignments', label: 'Assignments', count: data?.assignments.length },
            { id: 'lessons', label: 'Lessons', count: data?.lessons.length },
            { id: 'mastery', label: 'Mastery', count: data?.mastery.length },
            { id: 'development', label: 'Development plan', count: data?.development_plans.length },
            { id: 'quizzes', label: 'Film quizzes', count: data?.quiz_attempts.length },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={playerQuery.error && !cachedData ? playerQuery.error : undefined} loading={playerQuery.isLoading && !cachedData}>
          <div className="workbench-body">
            <div className="workbench-toolbar">
              <div className="workbench-toolbar__group">
                <label className="filter-select"><LockKeyhole aria-hidden="true" size={15} /><span className="sr-only">Player identifier</span><input disabled={session?.role === 'player'} onChange={(event) => setPlayerInput(event.target.value)} value={playerInput} /></label>
                {session?.role !== 'player' ? <button className="button button--secondary" disabled={!playerInput.trim()} onClick={() => { setPlayerId(playerInput.trim()); setAssignmentTargetId(playerInput.trim()); setSelectedId(''); }} type="button">Load player</button> : null}
              </div>
              <span className="workbench-form__hint"><LockKeyhole aria-hidden="true" size={12} /> {usingOfflineCache ? 'Offline: privacy-scoped cached content only; reconnect to verify the latest server state.' : data?.privacy || 'Only the player or authorized coaching authority can load this workspace.'}</span>
            </div>

            <WorkbenchStats stats={[
              { label: 'Assigned work', value: data?.assignments.length ?? 0, hint: 'current learning queue' },
              { label: 'Lessons', value: data?.lessons.length ?? 0, hint: 'guided install' },
              { label: 'Mastery records', value: data?.mastery.length ?? 0, hint: 'evidence based' },
              { label: 'Quiz attempts', value: data?.quiz_attempts.length ?? 0, hint: 'film recognition' },
            ]} />

            {data?.next_step ? (
              <article className="record-inspector">
                <header><div><p className="eyebrow">Recommended next action</p><h3>{recordLabel(data.next_step)}</h3></div><Target aria-hidden="true" size={24} /></header>
                <dl><div><dt>Learning artifact</dt><dd>{compactValue(data.next_step.artifact_id)}</dd></div><div><dt>Due</dt><dd>{compactValue(data.next_step.due_date)}</dd></div></dl>
              </article>
            ) : null}

            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                <div className="workbench-pane__header"><div><h3>{sentenceCase(tab)}</h3><p>Only records owned by {playerId} are returned.</p></div></div>
                <RecordList
                  emptyMessage={`No ${sentenceCase(tab).toLowerCase()} are currently assigned to this player.`}
                  onSelect={(record) => { setSelectedId(record.id); setRevealedSteps(1); }}
                  records={records}
                  selectedId={selected?.id}
                  subtitle={(record) => tab === 'mastery' || tab === 'quizzes' ? scorePercent(record) : record.id}
                  title={recordLabel}
                />
              </div>
              <div className="workbench-pane">
                {selected ? <PlayerRecordInspector onReveal={() => setRevealedSteps((count) => count + 1)} record={selected} revealedSteps={revealedSteps} tab={tab} /> : <div className="record-list__empty"><BookOpenCheck aria-hidden="true" size={22} /> Select a learning record to begin.</div>}
              </div>
            </div>

            {canAssign && tab === 'assignments' ? (
              <form className="workbench-form workbench-pane" onSubmit={submitAssignment}>
                <div className="workbench-pane__header"><div><h3><Plus aria-hidden="true" size={16} /> Assign development work</h3><p>Connect one player to one approved play, lesson, film playlist, quiz, or practice artifact.</p></div></div>
                <div className="workbench-form__grid">
                  <label className="is-wide"><span>Assign to roster player <small>catalog-backed; manual ID remains available</small></span><select onChange={(event) => setAssignmentTargetId(event.target.value)} value={assignmentTargetId}><option value="">Choose a player</option>{assignmentTargetId && !(rosterQuery.data?.players ?? []).some((player) => player.id === assignmentTargetId) ? <option value={assignmentTargetId}>{assignmentTargetId} - manual target</option> : null}{(rosterQuery.data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name} - {player.position} - {player.availability || 'availability unknown'}</option>)}</select></label>
                  <label><span>Title</span><input name="title" placeholder="Dagger boundary-safety read" required /></label>
                  <label><span>Assignment type</span><select name="assignment_type" onChange={(event) => { setAssignmentType(event.target.value); setArtifactId(''); setSourceRefs(''); }} value={assignmentType}><option>play_lesson</option><option>film_playlist</option><option>film_quiz</option><option>practice_correction</option><option>install_sheet</option></select></label>
                  <label className="is-wide"><span>Approved catalog artifact <small>filtered by assignment type</small></span><select onChange={(event) => { const selectedArtifact = artifactOptions.find((option) => option.id === event.target.value); setArtifactId(event.target.value); setSourceRefs(selectedArtifact?.sourceRefs.join(', ') ?? ''); }} value={artifactId}><option value="">Choose an approved artifact</option>{artifactOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>
                   <label><span>Artifact ID</span><input name="artifact_id" onChange={(event) => setArtifactId(event.target.value)} placeholder="Enter a catalog ID or use the selector above" required value={artifactId} /></label>
                  <label><span>Due date</span><input name="due_date" type="date" /></label>
                   <label className="is-wide"><span>Source references</span><input name="source_refs" onChange={(event) => setSourceRefs(event.target.value)} placeholder="Catalog references are suggested; manual refs remain allowed" required value={sourceRefs} /></label>
                </div>
                <div className="workbench-form__actions"><p className="workbench-form__hint">Assignment creation does not expose another player’s private records.</p><button className="button button--primary" disabled={mutation.isPending} type="submit"><Plus size={15} /> Assign to player</button></div>
                <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Development assignment created." />
              </form>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
