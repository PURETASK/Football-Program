import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, CalendarClock, ClipboardCheck, Gauge, GripVertical, Plus, Printer, Save, Trash2 } from 'lucide-react';
import { lazy, Suspense, useMemo, useState, type FormEvent } from 'react';

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
import { usePracticeAttendanceQuery, usePracticeDrillsQuery, usePracticeWorkspaceQuery, useRosterWorkspaceQuery } from '../hooks/useOperationalData';
import { usePlayDesignsQuery } from '../hooks/useWorkspaceData';
import { createPracticePlan, recordPracticeAttendance } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { PracticePeriod, PracticePlan } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { PRACTICE_WORKSPACE } from './workspaceDefinitions';

const PracticeOutcomeRecorder = lazy(() => import('./PracticeOutcomeRecorder').then((module) => ({ default: module.PracticeOutcomeRecorder })));

import '../styles/practice.css';

type PracticeTab = 'schedule' | 'builder' | 'outcomes' | 'attendance' | 'load';

function blankPeriod(index: number): PracticePeriod {
  return {
    id: recordId('PERIOD-'),
    type: index === 0 ? 'individual' : 'team',
    objective: '',
    owner: 'COACH-STAFF',
    players: ['offense'],
    position_groups: [],
    minutes: 10,
    reps: 8,
    learning_rationale: '',
    load_rationale: '',
    play_ids: [],
    drill_ids: [],
    attendance: ['all assigned players'],
    coaching_objective: '',
    install_phase: 'teach',
    status: 'draft',
  };
}

function PracticeTimeline({ plan }: { plan: PracticePlan }) {
  let elapsed = 0;
  return (
    <div className="timeline-board" aria-label={`${recordLabel(plan)} practice timeline`}>
      {(plan.periods ?? []).map((period) => {
        const start = elapsed;
        elapsed += Number(period.minutes || 0);
        return (
          <article className="timeline-period" key={period.id}>
            <span className="timeline-period__time">{start}–{elapsed}</span>
            <div><strong>{period.objective || sentenceCase(period.type)}</strong><small>{sentenceCase(period.type)} · {period.owner} · {compactValue(period.players)} · {compactValue(period.play_ids || [])}</small></div>
            <span className="timeline-period__load">{period.reps} reps</span>
            {period.position_groups?.length ? <small className="timeline-period__groups">{compactValue(period.position_groups)}</small> : null}
          </article>
        );
      })}
    </div>
  );
}

export function PracticePage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const practiceQuery = usePracticeWorkspaceQuery();
  const rosterQuery = useRosterWorkspaceQuery();
  const drillsQuery = usePracticeDrillsQuery();
  const playbookQuery = usePlayDesignsQuery();
  const [tab, setTab] = useState<PracticeTab>('schedule');
  const [selectedId, setSelectedId] = useState('');
  const [attendanceSelectedId, setAttendanceSelectedId] = useState('');
  const [periods, setPeriods] = useState<PracticePeriod[]>([blankPeriod(0), blankPeriod(1)]);
  const [maxMinutes, setMaxMinutes] = useState(75);
  const [draggingPeriodId, setDraggingPeriodId] = useState('');
  const [rosterIds, setRosterIds] = useState<string[]>([]);
  const [playSearch, setPlaySearch] = useState('');
  const [drillSearch, setDrillSearch] = useState('');
  const data = practiceQuery.data;
  const selected = data?.plans.find((plan) => plan.id === selectedId) ?? data?.plans[0];
  const attendancePracticeId = selected?.id ?? '';
  const attendanceQuery = usePracticeAttendanceQuery(attendancePracticeId);
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff', 'performance_staff'].includes(session.role));
  const plannedMinutes = useMemo(() => periods.reduce((total, period) => total + Number(period.minutes || 0), 0), [periods]);
  const plannedReps = useMemo(() => periods.reduce((total, period) => total + Number(period.reps || 0), 0), [periods]);
  const loadExceeded = plannedMinutes > maxMinutes;
  const availablePlays = useMemo(() => {
    const query = playSearch.trim().toLowerCase();
    return (playbookQuery.data ?? []).filter((play) => !query || [play.id, play.name, play.concept, play.formation, play.personnel].filter(Boolean).join(' ').toLowerCase().includes(query));
  }, [playSearch, playbookQuery.data]);
  const availableDrills = useMemo(() => {
    const query = drillSearch.trim().toLowerCase();
    return (drillsQuery.data?.drills ?? []).filter((drill) => !query || [drill.id, drill.name, drill.objective, drill.skill, ...(drill.position_groups ?? [])].filter(Boolean).join(' ').toLowerCase().includes(query));
  }, [drillSearch, drillsQuery.data?.drills]);
  const availablePositionGroups = useMemo(() => Array.from(new Set([
    ...(rosterQuery.data?.position_groups ?? []),
    ...(drillsQuery.data?.drills ?? []).flatMap((drill) => drill.position_groups ?? []),
  ].map((group) => group.trim()).filter(Boolean))).sort((left, right) => left.localeCompare(right)), [drillsQuery.data?.drills, rosterQuery.data?.position_groups]);

  const mutation = useMutation({
    mutationFn: (plan: PracticePlan) => createPracticePlan(session!, plan),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['practice-workspace', session?.organizationId] });
      setTab('schedule');
    },
  });
  const attendanceMutation = useMutation({
    mutationFn: (values: Parameters<typeof recordPracticeAttendance>[1]) => recordPracticeAttendance(session!, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['practice-attendance', session?.organizationId, attendancePracticeId] }),
  });

  function updatePeriod(id: string, key: keyof PracticePeriod, value: string | number | string[]) {
    setPeriods((current) => current.map((period) => period.id === id ? { ...period, [key]: value } : period));
  }

  function movePeriod(id: string, direction: -1 | 1) {
    setPeriods((current) => {
      const index = current.findIndex((period) => period.id === id);
      const nextIndex = index + direction;
      if (index < 0 || nextIndex < 0 || nextIndex >= current.length) return current;
      const next = [...current];
      [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
      return next;
    });
  }

  function dropPeriod(targetId: string) {
    if (!draggingPeriodId || draggingPeriodId === targetId) return;
    setPeriods((current) => {
      const from = current.findIndex((period) => period.id === draggingPeriodId);
      const to = current.findIndex((period) => period.id === targetId);
      if (from < 0 || to < 0) return current;
      const next = [...current];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
    setDraggingPeriodId('');
  }

  function submitPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      id: recordId('PRACTICE-'),
      team_context: String(form.get('team_context') || ''),
      season_phase: String(form.get('season_phase') || ''),
      week_context: String(form.get('week_context') || ''),
      objective: String(form.get('objective') || ''),
      opponent_priorities: splitList(String(form.get('priorities') || '')),
      periods,
      roster_ids: splitList(String(form.get('roster_ids') || '')),
      install_items: periods.map((period) => ({ period_id: period.id, play_ids: period.play_ids ?? [], drill_ids: period.drill_ids ?? [], install_phase: period.install_phase ?? 'teach', coaching_objective: period.coaching_objective ?? period.objective })),
      attendance_policy: String(form.get('attendance_policy') || 'staff_recorded'),
      practice_card_preferences: { black_white: form.get('black_white') === 'on', show_sources: true },
      staff_available: splitList(String(form.get('staff') || '')),
      facility_constraints: splitList(String(form.get('facilities') || '')),
      load_controls: { max_total_minutes: maxMinutes, max_reps_by_position: { QB: 40, WR: 55, OL: 55, DL: 50, DB: 50 } },
      restrictions: [],
      status: 'draft',
    });
  }

  function submitAttendance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!attendancePracticeId) return;
    const form = new FormData(event.currentTarget);
    const minutes = Number(form.get('minutes_available'));
    attendanceMutation.mutate({
      attendanceId: recordId('ATTENDANCE-'),
      practiceId: attendancePracticeId,
      playerId: String(form.get('player_id') || ''),
      status: String(form.get('status') || 'present'),
      minutesAvailable: Number.isFinite(minutes) && minutes >= 0 ? minutes : undefined,
      periodIds: splitList(String(form.get('period_ids') || '')),
      note: String(form.get('note') || ''),
      sourceRefs: splitList(String(form.get('source_refs') || '')),
    });
  }

  return (
    <WorkspacePage definition={PRACTICE_WORKSPACE}>
      <WorkbenchFrame
        actions={<><button className="button button--secondary" onClick={() => window.print()} type="button"><Printer size={15} /> Print card</button><button className="button button--primary" disabled={!canAuthor} onClick={() => setTab('builder')} type="button"><Plus size={15} /> Build practice</button></>}
        description="Compose period-by-period practices, monitor live load against declared limits, and preserve each plan as an organization record."
        eyebrow="Live practice operations"
        icon={CalendarClock}
        title="Practice orchestration board"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Practice workspace views"
          onChange={(next) => setTab(next as PracticeTab)}
          tabs={[
            { id: 'schedule', label: 'Practice plans', count: data?.plans.length },
            { id: 'builder', label: 'Period builder' },
            { id: 'outcomes', label: 'Rep outcomes' },
            { id: 'attendance', label: 'Attendance', count: attendanceQuery.data?.total },
            { id: 'load', label: 'Load & restrictions', count: data?.load_exceeded },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={practiceQuery.error} loading={practiceQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Saved plans', value: data?.plans.length ?? 0, hint: 'organization scoped' },
              { label: 'Total periods', value: data?.plans.reduce((sum, plan) => sum + (plan.periods?.length ?? 0), 0) ?? 0, hint: 'scheduled work' },
              { label: 'Load findings', value: data?.load_exceeded ?? 0, hint: 'requires adjustment' },
              { label: 'Review state', value: data?.human_review_required ? 'Human' : 'Clear', hint: 'coach authority' },
              { label: 'Attendance flags', value: attendanceQuery.data?.limited_or_absent.length ?? 0, hint: 'absent or limited' },
            ]} />

            {tab === 'schedule' ? (
              <div className="workbench-split">
                <div className="workbench-pane workbench-pane--soft">
                  <div className="workbench-pane__header"><div><h3>Saved practice plans</h3><p>Select a plan to inspect its timeline and objective mapping.</p></div></div>
                  <RecordList
                    emptyMessage="No practice plans are saved for this organization yet."
                    onSelect={(plan) => setSelectedId(plan.id)}
                    records={data?.plans ?? []}
                    selectedId={selected?.id}
                    subtitle={(plan) => `${plan.week_context || 'No week'} · ${plan.total_minutes ?? 0} minutes`}
                    title={recordLabel}
                  />
                </div>
                <div className="workbench-pane">
                  {selected ? (
                    <RecordInspector
                      eyebrow="Practice plan"
                      facts={[
                        { label: 'Week', value: compactValue(selected.week_context) },
                        { label: 'Objective', value: compactValue(selected.objective) },
                        { label: 'Opponent priorities', value: compactValue(selected.opponent_priorities) },
                        { label: 'Total load', value: `${selected.total_minutes ?? 0} minutes · ${selected.periods?.reduce((sum, period) => sum + Number(period.reps || 0), 0) ?? 0} reps` },
                      ]}
                      note="The timeline preserves learning purpose and physical-load rationale for every period; staff review remains required before field use."
                      status={selected.status}
                      title={recordLabel(selected)}
                    >
                      <PracticeTimeline plan={selected} />
                    </RecordInspector>
                  ) : <div className="record-list__empty">Create a practice to see its operational timeline here.</div>}
                </div>
              </div>
            ) : null}

            {tab === 'builder' ? (
              canAuthor ? (
                <form className="workbench-form" onSubmit={submitPlan}>
                  <div className="workbench-pane">
                    <div className="workbench-pane__header"><div><h3>Practice identity and objective</h3><p>Define why the practice exists before scheduling its periods.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Team context</span><input defaultValue="TEAM-DEMO-FIDOS" name="team_context" required /></label>
                      <label><span>Week</span><input defaultValue="WEEK-1" name="week_context" required /></label>
                      <label><span>Season phase</span><select defaultValue="regular_season" name="season_phase"><option>preseason</option><option>regular_season</option><option>postseason</option><option>offseason</option></select></label>
                      <label><span>Available staff <small>comma separated</small></span><input defaultValue={session?.subject || 'COACH-STAFF'} name="staff" required /></label>
                      <label className="is-wide"><span>Roster player IDs <small>catalog selection or comma-separated import</small></span><input list="practice-roster-options" name="roster_ids" onChange={(event) => setRosterIds(splitList(event.target.value))} placeholder="PLAYER-..., PLAYER-..." value={rosterIds.join(', ')} /><datalist id="practice-roster-options">{(rosterQuery.data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name}</option>)}</datalist></label>
                      <label className="is-wide"><span>Assign roster players <small>Ctrl/Cmd-click for multiple</small></span><select className="practice-multi-select" multiple onChange={(event) => setRosterIds(Array.from(event.target.selectedOptions).map((option) => option.value))} size={Math.min(5, Math.max(3, rosterQuery.data?.players.length ?? 3))} value={rosterIds}>{(rosterQuery.data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name} · {player.position} · {player.availability || 'availability unknown'}</option>)}</select></label>
                      <label><span>Attendance policy</span><select defaultValue="staff_recorded" name="attendance_policy"><option>staff_recorded</option><option>position_group_check_in</option><option>coach_confirmed</option></select></label>
                      <div className="workbench-checkbox"><span>Print format</span><label className="checkbox-field"><input name="black_white" type="checkbox" /><span>Black-and-white practice card</span></label></div>
                      <label className="is-wide"><span>Primary objective</span><textarea name="objective" placeholder="Install, correct, or prepare a specific football outcome." required /></label>
                      <label><span>Opponent priorities</span><input name="priorities" placeholder="third-down pressure, late rotation" required /></label>
                      <label><span>Facility constraints <small>optional</small></span><input name="facilities" placeholder="half field, indoor only" /></label>
                    </div>
                  </div>

                  <div className="workbench-pane">
                    <div className="workbench-pane__header">
                      <div><h3>Period schedule</h3><p>Drag periods to reorder the install, or use the keyboard controls. Start/end timing recalculates immediately.</p></div>
                      <button className="button button--secondary" onClick={() => setPeriods((current) => [...current, blankPeriod(current.length)])} type="button"><Plus size={14} /> Add period</button>
                    </div>
                    <label className="practice-search"><span>Playbook catalog filter</span><input onChange={(event) => setPlaySearch(event.target.value)} placeholder="Search concept, formation, personnel, or play ID" value={playSearch} /></label>
                    <label className="practice-search"><span>Drill catalog filter</span><input onChange={(event) => setDrillSearch(event.target.value)} placeholder="Search drill skill or position group" value={drillSearch} /></label>
                    <div className="timeline-board">
                      {periods.map((period, index) => (
                        <fieldset className="workbench-form workbench-pane workbench-pane--soft" draggable onDragEnd={() => setDraggingPeriodId('')} onDragOver={(event) => event.preventDefault()} onDragStart={() => setDraggingPeriodId(period.id)} onDrop={() => dropPeriod(period.id)} key={period.id}>
                          <legend className="sr-only">Period {index + 1}</legend>
                          <div className="workbench-pane__header"><div><h3><GripVertical aria-hidden="true" size={15} /> Period {index + 1}</h3><p>{period.id} · {periods.slice(0, index).reduce((total, item) => total + Number(item.minutes || 0), 0)}–{periods.slice(0, index + 1).reduce((total, item) => total + Number(item.minutes || 0), 0)} min</p></div><div className="workbench-toolbar__group"><button aria-label={`Move period ${index + 1} up`} className="button button--ghost" disabled={index === 0} onClick={() => movePeriod(period.id, -1)} type="button"><ArrowUp size={14} /></button><button aria-label={`Move period ${index + 1} down`} className="button button--ghost" disabled={index === periods.length - 1} onClick={() => movePeriod(period.id, 1)} type="button"><ArrowDown size={14} /></button><button aria-label={`Remove period ${index + 1}`} className="button button--ghost" disabled={periods.length === 1} onClick={() => setPeriods((current) => current.filter((item) => item.id !== period.id))} type="button"><Trash2 size={14} /></button></div></div>
                          <div className="workbench-form__grid">
                            <label><span>Type</span><select onChange={(event) => updatePeriod(period.id, 'type', event.target.value)} value={period.type}><option>individual</option><option>group</option><option>inside_run</option><option>skelly</option><option>team</option><option>situational</option><option>special_teams</option><option>installation</option><option>correction</option><option>walkthrough</option><option>competitive</option></select></label>
                            <label><span>Owner</span><input onChange={(event) => updatePeriod(period.id, 'owner', event.target.value)} required value={period.owner} /></label>
                            <label className="is-wide"><span>Objective</span><input onChange={(event) => updatePeriod(period.id, 'objective', event.target.value)} required value={period.objective} /></label>
                            <label className="is-wide"><span>Position groups <small>{availablePositionGroups.length} catalog group{availablePositionGroups.length === 1 ? '' : 's'}</small></span><select aria-label={`Position groups for period ${index + 1}`} className="practice-multi-select" multiple onChange={(event) => updatePeriod(period.id, 'position_groups', Array.from(event.target.selectedOptions).map((option) => option.value))} size={Math.min(5, Math.max(3, availablePositionGroups.length || 3))} value={period.position_groups ?? []}>{availablePositionGroups.map((group) => <option key={group} value={group}>{group}</option>)}</select></label>
                            <label><span>Players / groups</span><input onChange={(event) => updatePeriod(period.id, 'players', splitList(event.target.value))} required value={period.players.join(', ')} /></label>
                            <label><span>Play IDs</span><input onChange={(event) => updatePeriod(period.id, 'play_ids', splitList(event.target.value))} placeholder="PLAY-..., PLAY-..." value={(period.play_ids ?? []).join(', ')} /></label>
                            <label className="is-wide"><span>Link Playbook calls <small>{availablePlays.length} catalog result{availablePlays.length === 1 ? '' : 's'}</small></span><select className="practice-multi-select" multiple onChange={(event) => updatePeriod(period.id, 'play_ids', Array.from(event.target.selectedOptions).map((option) => option.value))} size={Math.min(5, Math.max(3, availablePlays.length || 3))} value={period.play_ids ?? []}>{availablePlays.map((play) => <option key={play.id} value={play.id}>{play.name || play.concept || play.id} · {play.formation || 'formation n/a'} · {play.personnel || 'personnel n/a'}</option>)}</select></label>
                            <label><span>Drill IDs</span><input onChange={(event) => updatePeriod(period.id, 'drill_ids', splitList(event.target.value))} placeholder="DRILL-..., DRILL-..." value={(period.drill_ids ?? []).join(', ')} /></label>
                            <label className="is-wide"><span>Link drill catalog <small>{availableDrills.length} catalog result{availableDrills.length === 1 ? '' : 's'}</small></span><select className="practice-multi-select" multiple onChange={(event) => updatePeriod(period.id, 'drill_ids', Array.from(event.target.selectedOptions).map((option) => option.value))} size={Math.min(5, Math.max(3, availableDrills.length || 3))} value={period.drill_ids ?? []}>{availableDrills.map((drill) => <option key={drill.id} value={drill.id}>{drill.name || drill.id} · {drill.skill || drill.objective || 'objective n/a'} · {(drill.position_groups ?? []).join('/') || 'group n/a'}</option>)}</select></label>
                            <label><span>Install phase</span><select onChange={(event) => updatePeriod(period.id, 'install_phase', event.target.value)} value={period.install_phase ?? 'teach'}><option>teach</option><option>walkthrough</option><option>rehearse</option><option>compete</option><option>correct</option></select></label>
                            <label><span>Minutes</span><input min="1" onChange={(event) => updatePeriod(period.id, 'minutes', Number(event.target.value))} required type="number" value={period.minutes} /></label>
                            <label><span>Reps</span><input min="0" onChange={(event) => updatePeriod(period.id, 'reps', Number(event.target.value))} required type="number" value={period.reps} /></label>
                            <label className="is-wide"><span>Learning rationale</span><input onChange={(event) => updatePeriod(period.id, 'learning_rationale', event.target.value)} required value={period.learning_rationale} /></label>
                            <label className="is-wide"><span>Coaching objective</span><input onChange={(event) => updatePeriod(period.id, 'coaching_objective', event.target.value)} placeholder="What must the player demonstrate?" value={period.coaching_objective ?? ''} /></label>
                            <label className="is-wide"><span>Attendance / participant rule</span><input onChange={(event) => updatePeriod(period.id, 'attendance', splitList(event.target.value))} value={(period.attendance ?? []).join(', ')} /></label>
                            <label className="is-wide"><span>Load rationale</span><input onChange={(event) => updatePeriod(period.id, 'load_rationale', event.target.value)} required value={period.load_rationale} /></label>
                          </div>
                        </fieldset>
                      ))}
                    </div>
                  </div>

                  <div className="workbench-pane">
                    <div className="workbench-pane__header"><div><h3><Gauge aria-hidden="true" size={16} /> Live load envelope</h3><p>The plan is checked before it is submitted to the API.</p></div></div>
                    <WorkbenchStats stats={[
                      { label: 'Periods', value: periods.length },
                      { label: 'Minutes', value: plannedMinutes, hint: `${maxMinutes} maximum` },
                      { label: 'Total reps', value: plannedReps },
                      { label: 'Envelope', value: loadExceeded ? 'Exceeded' : 'Inside', hint: loadExceeded ? 'reduce minutes' : 'ready to validate' },
                    ]} />
                    <div className="workbench-form__grid" style={{ marginTop: '0.75rem' }}>
                      <label><span>Maximum total minutes</span><input min="1" onChange={(event) => setMaxMinutes(Number(event.target.value))} type="number" value={maxMinutes} /></label>
                    </div>
                    {loadExceeded ? <p className="mutation-notice mutation-notice--error" role="alert">Planned minutes exceed the declared maximum. The API will reject this plan until the load is corrected.</p> : null}
                  </div>
                  <div className="workbench-form__actions"><p className="workbench-form__hint">Saving creates a governed draft; it does not silently activate the practice.</p><button className="button button--primary" disabled={mutation.isPending || loadExceeded || periods.some((period) => !period.objective || !period.learning_rationale || !period.load_rationale)} type="submit"><Save size={15} /> Save practice draft</button></div>
                  <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Practice plan saved as a governed draft." />
                </form>
              ) : <p className="approval-boundary">Practice authoring requires owner, coach, or performance-staff authority. Your current role can inspect approved practice information.</p>
            ) : null}

            {tab === 'outcomes' ? (
              selected && session ? <Suspense fallback={<div className="workbench-pane"><p className="workbench-form__hint">Opening the practice outcome recorder…</p></div>}><PracticeOutcomeRecorder canAuthor={canAuthor} onRecorded={() => queryClient.invalidateQueries({ queryKey: ['practice-workspace', session.organizationId] })} practice={selected} session={session} /></Suspense>
                : <div className="workbench-pane"><p className="workbench-form__hint">Select or create a practice plan before recording rep outcomes.</p></div>
            ) : null}

            {tab === 'attendance' ? (
              canAuthor ? (
                <>
                  <div className="workbench-split">
                    <div className="workbench-pane workbench-pane--soft">
                      <div className="workbench-pane__header"><div><h3>Recorded participation</h3><p>{selected ? `${recordLabel(selected)} · ${attendanceQuery.data?.total ?? 0} player records` : 'Select or create a practice plan first.'}</p></div></div>
                      <RecordList
                        emptyMessage={attendancePracticeId ? 'No attendance has been recorded for this practice.' : 'Create a practice plan before recording attendance.'}
                        onSelect={(record) => setAttendanceSelectedId(record.id)}
                        records={attendanceQuery.data?.records ?? []}
                        selectedId={attendanceSelectedId || attendanceQuery.data?.records[0]?.id}
                        subtitle={(record) => `${sentenceCase(record.status)} · ${record.position_group || record.position || 'Position unknown'} · ${record.minutes_available ?? '—'} min available`}
                        title={(record) => record.player_name || record.player_id}
                      />
                    </div>
                    <div className="workbench-pane">
                      {(() => {
                        const attendance = attendanceQuery.data?.records.find((record) => record.id === attendanceSelectedId) ?? attendanceQuery.data?.records[0];
                        return attendance ? <RecordInspector eyebrow="Participation record" facts={[
                          { label: 'Player', value: attendance.player_name || attendance.player_id },
                          { label: 'Status', value: sentenceCase(attendance.status) },
                          { label: 'Minutes available', value: compactValue(attendance.minutes_available) },
                          { label: 'Periods', value: compactValue(attendance.period_ids) },
                          { label: 'Recorded by', value: compactValue(attendance.recorded_by) },
                          { label: 'Note', value: compactValue(attendance.note) },
                        ]} note="Absent and limited records stay visible as human-review flags and do not infer medical clearance or automatically change player eligibility." status={attendance.status} title={attendance.player_name || attendance.player_id} /> : <RecordInspector eyebrow="Participation summary" facts={[
                          { label: 'Present', value: attendanceQuery.data?.counts.present ?? 0 },
                          { label: 'Absent', value: attendanceQuery.data?.counts.absent ?? 0 },
                          { label: 'Limited', value: attendanceQuery.data?.counts.limited ?? 0 },
                          { label: 'Late / excused', value: (attendanceQuery.data?.counts.late ?? 0) + (attendanceQuery.data?.counts.excused ?? 0) },
                        ]} note="Attendance is a staff-recorded practice fact. It is not a medical or eligibility decision." status={attendanceQuery.data?.human_review_required ? 'review_required' : 'ready'} title="No attendance record selected" />;
                      })()}
                    </div>
                  </div>
                  <form className="workbench-form workbench-pane" onSubmit={submitAttendance}>
                    <div className="workbench-pane__header"><div><h3><ClipboardCheck aria-hidden="true" size={16} /> Record player attendance</h3><p>Link the participation fact to the selected practice and organization roster.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Practice</span><input value={attendancePracticeId || 'No practice selected'} readOnly /></label>
                      <label><span>Player</span><select name="player_id" required>{(rosterQuery.data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name} · {player.position} · {player.availability || 'availability unknown'}</option>)}</select></label>
                      <label><span>Status</span><select defaultValue="present" name="status"><option>present</option><option>absent</option><option>limited</option><option>late</option><option>excused</option></select></label>
                      <label><span>Minutes available <small>optional</small></span><input min="0" name="minutes_available" type="number" /></label>
                      <label className="is-wide"><span>Period IDs <small>comma separated</small></span><input name="period_ids" placeholder="PERIOD-..., PERIOD-..." /></label>
                      <label className="is-wide"><span>Note</span><textarea name="note" placeholder="Participation context or staff instruction." /></label>
                      <label className="is-wide"><span>Source references <small>optional, comma separated</small></span><input name="source_refs" placeholder="PRACTICE-CHECKIN-001" /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">Attendance writes are roster-validated, organization-scoped, and never change medical status or eligibility.</p><button className="button button--primary" disabled={attendanceMutation.isPending || !attendancePracticeId || !(rosterQuery.data?.players.length)} type="submit"><ClipboardCheck size={15} /> Save participation record</button></div>
                    <MutationNotice error={attendanceMutation.error} pending={attendanceMutation.isPending} success={attendanceMutation.isSuccess} successMessage="Practice attendance recorded and linked to the roster." />
                  </form>
                </>
              ) : <p className="approval-boundary">Attendance recording requires owner, coaching, or performance-staff authority.</p>
            ) : null}

            {tab === 'load' ? (
              <div className="workbench-split">
                <div className="workbench-pane workbench-pane--soft">
                  <div className="workbench-pane__header"><div><h3>Plans requiring attention</h3><p>Load findings remain explainable and linked to the affected plan.</p></div></div>
                  <RecordList
                    emptyMessage="No saved plans currently exceed their declared load controls."
                    onSelect={(plan) => setSelectedId(plan.id)}
                    records={(data?.plans ?? []).filter((plan) => plan.issues?.some((issue) => compactValue(issue).includes('PRACTICE-LOAD-EXCEEDED')))}
                    selectedId={selectedId}
                    subtitle={(plan) => `${plan.total_minutes ?? 0} minutes`}
                    title={recordLabel}
                  />
                </div>
                <div className="workbench-pane">
                  <RecordInspector
                    eyebrow="Load policy"
                    facts={[
                      { label: 'Saved findings', value: data?.load_exceeded ?? 0 },
                      { label: 'Builder minutes', value: plannedMinutes },
                      { label: 'Builder maximum', value: maxMinutes },
                      { label: 'Current envelope', value: loadExceeded ? 'Exceeded' : 'Within limit' },
                    ]}
                    note="Load limits are staff-declared safeguards. Medical or performance restrictions must still be confirmed by authorized human staff before practice."
                    status={loadExceeded ? 'blocked' : 'ready'}
                    title="Practice load controls"
                  />
                </div>
              </div>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
