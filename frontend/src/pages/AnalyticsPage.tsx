import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BarChart3, CircleCheck, FilePlus2, GitCompareArrows, ShieldAlert } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';

import { useSession } from '../auth/SessionContext';
import { MutationNotice, RecordInspector, RecordList, WorkbenchFrame, WorkbenchSearch, WorkbenchState, WorkbenchStats, WorkbenchTabs } from '../components/OperationalWorkbench';
import { useAnalyticsWorkspaceQuery } from '../hooks/useOperationalData';
import { createAnalyticsReport, recordAnalyticsOutcome } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { FootballRecord } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { ANALYTICS_WORKSPACE } from './workspaceDefinitions';

type AnalyticsTab = 'observations' | 'reports' | 'outcomes' | 'comparison' | 'author' | 'outcome_author';

function observationRate(record: FootballRecord): string {
  const rate = Number(record.rate);
  return Number.isFinite(rate) ? `${Math.round(rate * 100)}%` : 'Not calculated';
}

export function AnalyticsPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const recordQuery = new URLSearchParams(window.location.search);
  const [tab, setTab] = useState<AnalyticsTab>(() => recordQuery.get('record_type') === 'analytics' ? 'outcomes' : 'observations');
  const [search, setSearch] = useState('');
  const [situation, setSituation] = useState('all');
  const [selectedId, setSelectedId] = useState(() => recordQuery.get('record') || '');
  const [reportObservationIds, setReportObservationIds] = useState<string[]>([]);
  const dataQuery = useAnalyticsWorkspaceQuery(situation === 'all' ? '' : situation);
  const data = dataQuery.data;
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff', 'analyst'].includes(session.role));
  const situations = useMemo(() => [...new Set((data?.observations ?? []).map((record) => String(record.context && typeof record.context === 'object' ? (record.context as Record<string, unknown>).situation || '' : '')).filter(Boolean))].sort(), [data?.observations]);
  const rawRecords = tab === 'observations' ? data?.observations ?? [] : tab === 'outcomes' || tab === 'comparison' ? data?.outcomes ?? [] : data?.reports ?? [];
  const records = useMemo(() => { const needle = search.trim().toLowerCase(); return rawRecords.filter((record) => !needle || compactValue(record).toLowerCase().includes(needle)); }, [rawRecords, search]);
  const selected = records.find((record) => record.id === selectedId) ?? records[0];
  const reportMutation = useMutation({
    mutationFn: (values: Parameters<typeof createAnalyticsReport>[1]) => createAnalyticsReport(session!, values),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['analytics-workspace', session?.organizationId] }); setTab('reports'); },
  });
  const outcomeMutation = useMutation({
    mutationFn: (values: Parameters<typeof recordAnalyticsOutcome>[1]) => recordAnalyticsOutcome(session!, values),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['analytics-workspace', session?.organizationId] }); setTab('outcomes'); },
  });

  function submitReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const selectedObservations = (data?.observations ?? []).filter((record) => String(form.get('observation_ids') || '').split(',').map((value) => value.trim()).includes(record.id));
    reportMutation.mutate({
      reportId: recordId('ANALYTICS-REPORT-'),
      audience: String(form.get('audience') || 'coaching staff'),
      metricObservations: selectedObservations,
      context: { situation: String(form.get('situation') || ''), comparison: String(form.get('comparison') || '') },
      caveats: splitList(String(form.get('caveats') || '')),
    });
  }

  function submitOutcome(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    outcomeMutation.mutate({
      outcomeId: recordId('OUTCOME-'),
      intendedRecordType: String(form.get('intended_record_type') || 'play_design'),
      intendedRecordId: String(form.get('intended_record_id') || ''),
      actualResult: String(form.get('actual_result') || 'not_scored'),
      successCount: Number(form.get('success_count') || 0),
      sampleSize: Number(form.get('sample_size') || 0),
      context: {
        situation: String(form.get('situation') || ''),
        down_distance: String(form.get('down_distance') || ''),
        field_zone: String(form.get('field_zone') || ''),
        personnel: String(form.get('personnel') || ''),
        formation: String(form.get('formation') || ''),
        responsibility_phase: String(form.get('responsibility_phase') || ''),
      },
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
      linkedPlayId: String(form.get('linked_play_id') || '') || undefined,
      linkedAssignmentId: String(form.get('linked_assignment_id') || '') || undefined,
      teachingStepId: String(form.get('teaching_step_id') || '') || undefined,
      responsibilityPhase: String(form.get('responsibility_phase') || '') || undefined,
      practiceId: String(form.get('practice_id') || '') || undefined,
      filmObservationIds: splitList(String(form.get('film_observation_ids') || '')),
      gamePlanId: String(form.get('game_plan_id') || '') || undefined,
      notes: String(form.get('notes') || ''),
    });
  }

  return (
    <WorkspacePage definition={ANALYTICS_WORKSPACE}>
      <WorkbenchFrame actions={<div className="workbench-toolbar__group"><button className="button button--secondary" disabled={!canAuthor} onClick={() => setTab('outcome_author')} type="button"><CircleCheck size={15} /> Record outcome</button><button className="button button--primary" disabled={!canAuthor} onClick={() => setTab('author')} type="button"><FilePlus2 size={15} /> New report</button></div>} description="Connect intentions, execution, and outcomes while keeping the sample, source lineage, uncertainty, and staff interpretation visible." eyebrow="Performance feedback loop" icon={BarChart3} title="Outcome analytics studio">
        <WorkbenchTabs activeTab={tab} label="Analytics workspace views" onChange={(next) => { setTab(next as AnalyticsTab); setSelectedId(''); }} tabs={[{ id: 'observations', label: 'Observations', count: data?.observations.length }, { id: 'outcomes', label: 'Outcomes', count: data?.outcomes.length }, { id: 'reports', label: 'Reports', count: data?.reports.length }, { id: 'comparison', label: 'Design → outcome', count: data?.outcomes.length }, { id: 'author', label: 'Report builder' }, { id: 'outcome_author', label: 'Outcome recorder' }]} />
        <WorkbenchState connected={Boolean(session)} error={dataQuery.error} loading={dataQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[{ label: 'Observations', value: data?.observations.length ?? 0, hint: 'source-linked metrics' }, { label: 'Outcome records', value: data?.outcome_count ?? 0, hint: 'intended vs actual' }, { label: 'Lineage complete', value: data?.lineage_complete_count ?? 0, hint: 'traceable evidence' }, { label: 'Uncertainty flags', value: data?.uncertainty_count ?? 0, hint: 'sample or interval caution' }, { label: 'Reports in review', value: data?.review_count ?? 0, hint: 'staff interpretation' }]} />
            <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> Metrics explain what the recorded sample supports. They do not prove causality, replace coaching judgment, or independently change a player plan.</div>
            {(tab === 'outcomes' || tab === 'comparison') && data?.responsibility_phase_summary?.length ? <section aria-label="Responsibility phase analytics" className="workbench-pane responsibility-phase-summary"><div className="workbench-pane__header"><div><h3>Responsibility phase performance</h3><p>Aggregate evidence across the execution chain so staff can see where a concept succeeds or breaks down.</p></div></div><div className="responsibility-phase-grid">{data.responsibility_phase_summary.map((phase) => <article className="responsibility-phase-card" key={phase.phase}><div className="responsibility-phase-card__top"><strong>{sentenceCase(phase.phase)}</strong><span>{phase.success_rate === null ? 'Unrated' : `${Math.round(phase.success_rate * 100)}%`} success</span></div><p>{phase.success_count} successful reps across {phase.sample_size} sampled reps · {phase.record_count} linked records</p><small>Confidence: {sentenceCase(phase.confidence)}{phase.human_review_required ? ' · Review required' : ''}</small>{phase.linked_assignment_ids.length ? <small>Assignments: {phase.linked_assignment_ids.join(', ')}</small> : null}</article>)}</div></section> : null}
            {tab !== 'author' && tab !== 'outcome_author' ? <>
              <div className="workbench-toolbar"><WorkbenchSearch label="Search analytics" onChange={setSearch} placeholder="Search metric, source, context…" value={search} /><label className="filter-select"><span className="sr-only">Filter situation</span><select onChange={(event) => setSituation(event.target.value)} value={situation}><option value="all">All situations</option>{situations.map((value) => <option key={value} value={value}>{sentenceCase(value)}</option>)}</select></label></div>
              <div className="workbench-split"><div className="workbench-pane workbench-pane--soft"><div className="workbench-pane__header"><div><h3>{tab === 'reports' ? 'Analytics reports' : tab === 'outcomes' || tab === 'comparison' ? 'Outcome comparison records' : 'Metric observations'}</h3><p>{records.length} records match the current evidence context.</p></div></div><RecordList emptyMessage="No analytics records match these filters." onSelect={(record) => setSelectedId(record.id)} records={records} selectedId={selected?.id} subtitle={(record) => tab === 'reports' ? `${record.audience || 'Staff'} · ${record.status || 'draft'}` : tab === 'outcomes' || tab === 'comparison' ? `${sentenceCase(String(record.actual_result || 'not scored'))} · ${compactValue(record.success_count)}/${compactValue(record.sample_size)}` : `${record.metric_id || 'metric'} · ${observationRate(record)}`} title={recordLabel} /></div><div className="workbench-pane">{selected ? <RecordInspector eyebrow={tab === 'reports' ? 'Reviewable report' : tab === 'outcomes' || tab === 'comparison' ? 'Intended versus actual outcome' : 'Metric observation'} facts={tab === 'reports' ? [{ label: 'Audience', value: compactValue(selected.audience) }, { label: 'Context', value: compactValue(selected.context) }, { label: 'Observations', value: compactValue(selected.metric_observation_ids) }, { label: 'Caveats', value: compactValue(selected.caveats) }] : tab === 'outcomes' || tab === 'comparison' ? [{ label: 'Intended record', value: `${compactValue(selected.intended_record_type)} · ${compactValue(selected.intended_record_id)}` }, { label: 'Actual result', value: sentenceCase(String(selected.actual_result || '')) }, { label: 'Success rate', value: observationRate({ id: selected.id, rate: selected.success_rate }) }, { label: 'Sample', value: `${compactValue(selected.success_count)} / ${compactValue(selected.sample_size)}` }, { label: 'Confidence', value: sentenceCase(String(selected.confidence || 'unrated')) }, { label: 'Linked evidence', value: compactValue(selected.evidence_refs) }] : [{ label: 'Metric', value: compactValue(selected.metric_id) }, { label: 'Rate', value: observationRate(selected) }, { label: 'Sample', value: `${compactValue(selected.numerator)} / ${compactValue(selected.denominator)}` }, { label: 'Confidence', value: sentenceCase(String(selected.confidence || 'unrated')) }, { label: 'Uncertainty', value: compactValue(selected.uncertainty) }]} note="The next decision must be made by the relevant coach, analyst, or owner using the linked evidence and the operational context." status={selected.status} title={recordLabel(selected)}><ul className="evidence-stack">{[...(selected.source ? [compactValue(selected.source)] : []), ...(Array.isArray(selected.observation_ids) ? selected.observation_ids : []), ...(Array.isArray(selected.metric_observation_ids) ? selected.metric_observation_ids : []), ...(Array.isArray(selected.evidence_refs) ? selected.evidence_refs : [])].map((ref) => <li key={String(ref)}><strong>{String(ref)}</strong><span>Organization-scoped lineage reference</span></li>)}</ul></RecordInspector> : <div className="record-list__empty"><GitCompareArrows aria-hidden="true" size={22} /> Select a record to inspect the outcome loop.</div>}</div></div>
            </> : null}
            {tab === 'author' ? canAuthor ? <form className="workbench-form workbench-pane" onSubmit={submitReport}><div className="workbench-pane__header"><div><h3><FilePlus2 aria-hidden="true" size={16} /> Compose analytics report</h3><p>Use valid observations only and state the context and caveats the staff must carry forward.</p></div></div><div className="workbench-form__grid"><label><span>Audience</span><input defaultValue="coaching staff" name="audience" required /></label><label><span>Situation</span><input name="situation" placeholder="third_down" required /></label><label className="is-wide"><span>Observation IDs <small>comma separated</small></span><input name="observation_ids" placeholder="METRIC-OBS-…" required /></label><label className="is-wide"><span>Choose source-linked observations <small>Ctrl/Cmd-click for multiple</small></span><select aria-label="Source-linked observations for analytics report" className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); setReportObservationIds(ids); const input = event.currentTarget.form?.elements.namedItem('observation_ids') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, data?.observations.length ?? 4))} value={reportObservationIds}>{(data?.observations ?? []).map((observation) => <option key={observation.id} value={observation.id}>{String(observation.metric_id || observation.id)} - {observation.rate !== undefined ? observationRate(observation) : 'unrated'} - sample {compactValue(observation.denominator)}</option>)}</select></label><label className="is-wide"><span>Comparison question</span><textarea name="comparison" placeholder="Did the intended answer improve execution in the recorded sample?" required /></label><label className="is-wide"><span>Caveats <small>comma separated</small></span><input name="caveats" placeholder="small sample, opponent context changed" required /></label></div><div className="workbench-form__actions"><p className="workbench-form__hint">Only valid, source-linked observations can enter a report.</p><button className="button button--primary" disabled={reportMutation.isPending || !data?.observations.length} type="submit"><FilePlus2 size={15} /> Submit report</button></div><MutationNotice error={reportMutation.error} pending={reportMutation.isPending} success={reportMutation.isSuccess} successMessage="Analytics report created for staff interpretation." /></form> : <p className="approval-boundary">Analytics authoring requires analyst, coaching, or program-owner authority.</p> : null}
            {tab === 'outcome_author' ? canAuthor ? <form className="workbench-form workbench-pane" onSubmit={submitOutcome}><div className="workbench-pane__header"><div><h3><CircleCheck aria-hidden="true" size={16} /> Record intended-versus-actual outcome</h3><p>Capture what the play, practice period, or game-plan decision intended and what the observed sample produced.</p></div></div><div className="workbench-form__grid"><label><span>Intended record type</span><select defaultValue="play_design" name="intended_record_type"><option>play_design</option><option>practice_period</option><option>game_plan</option><option>scouting_claim</option><option>player_assignment</option></select></label><label><span>Intended record ID</span><input name="intended_record_id" placeholder="PLAY-…, PERIOD-…, GAMEPLAN-…" required /></label><label><span>Actual result</span><select defaultValue="not_scored" name="actual_result"><option>success</option><option>partial</option><option>failure</option><option>neutral</option><option>not_scored</option></select></label><label><span>Successes</span><input min="0" name="success_count" required type="number" /></label><label><span>Sample size</span><input min="1" name="sample_size" required type="number" /></label><label><span>Situation</span><input name="situation" placeholder="third_down" required /></label><label><span>Down / distance</span><input name="down_distance" placeholder="3-and-6" /></label><label><span>Field zone</span><input name="field_zone" placeholder="high_red_zone" /></label><label><span>Personnel</span><input name="personnel" placeholder="11" /></label><label><span>Formation</span><input name="formation" placeholder="trips_right" /></label><label><span>Linked Play ID <small>optional</small></span><input name="linked_play_id" placeholder="PLAY-…" /></label><label><span>Practice ID <small>optional</small></span><input name="practice_id" placeholder="PRACTICE-…" /></label><label><span>Film observation IDs <small>comma separated</small></span><input name="film_observation_ids" placeholder="FILM-OBS-…" /></label><label><span>Game plan ID <small>optional</small></span><input name="game_plan_id" placeholder="GAMEPLAN-…" /></label><label className="is-wide"><span>Evidence references <small>comma separated</small></span><input name="evidence_refs" placeholder="FILM-OBS-…, PRACTICE-…, GAME-…" required /></label><label className="is-wide"><span>Notes</span><textarea name="notes" placeholder="What happened, what remains uncertain, and what should staff review?" /></label></div><div className="workbench-form__actions"><p className="workbench-form__hint">Sample size, confidence, and Wilson uncertainty are calculated server-side; low-sample and negative outcomes remain review-required.</p><button className="button button--primary" disabled={outcomeMutation.isPending} type="submit"><CircleCheck size={15} /> Save outcome record</button></div><MutationNotice error={outcomeMutation.error} pending={outcomeMutation.isPending} success={outcomeMutation.isSuccess} successMessage="Outcome recorded with lineage and uncertainty context." /></form> : <p className="approval-boundary">Outcome recording requires analyst, coaching, or program-owner authority.</p> : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
