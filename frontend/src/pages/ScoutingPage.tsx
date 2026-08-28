import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Binoculars, ChartNoAxesCombined, FilePlus2, ShieldAlert, TrendingUp } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import {
  MutationNotice,
  RecordInspector,
  RecordList,
  WorkbenchFrame,
  WorkbenchSearch,
  WorkbenchState,
  WorkbenchStats,
  WorkbenchTabs,
} from '../components/OperationalWorkbench';
import { useFilmWorkspaceQuery, useScoutingTendencyQuery, useScoutingWorkspaceQuery } from '../hooks/useOperationalData';
import { createCollaborationThread, createScoutingReport } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import { buildTendencyExplorerRecords, TENDENCY_DIMENSIONS, type TendencyExplorerRecord } from '../lib/scoutingExplorer';
import type { FootballRecord } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { SCOUTING_WORKSPACE } from './workspaceDefinitions';

import '../styles/scouting.css';

type ScoutingTab = 'profiles' | 'reports' | 'matchups' | 'evolution' | 'explorer' | 'author';

function scoutingFacts(record: FootballRecord, tab: ScoutingTab) {
  if (tab === 'profiles') return [
    { label: 'Opponent', value: compactValue(record.opponent) },
    { label: 'Season', value: compactValue(record.season) },
    { label: 'Offense profile', value: compactValue(record.offense) },
    { label: 'Defense profile', value: compactValue(record.defense) },
  ];
  if (tab === 'reports') return [
    { label: 'Situation', value: compactValue(record.situation) },
    { label: 'Sample', value: compactValue(record.sample_size) },
    { label: 'Claims', value: Array.isArray(record.claims) ? record.claims.length : 0 },
    { label: 'Analyst', value: compactValue(record.analyst) },
  ];
  if (tab === 'matchups') return [
    { label: 'Opponent', value: compactValue(record.opponent) },
    { label: 'Context', value: compactValue(record.context) },
    { label: 'Matchups', value: compactValue(record.matchups) },
    { label: 'Analyst', value: compactValue(record.analyst) },
  ];
  return [
    { label: 'Opponent', value: compactValue(record.opponent) },
    { label: 'Historical claim', value: compactValue(record.historical_claims) },
    { label: 'Current claim', value: compactValue(record.current_claims) },
    { label: 'Adaptation warning', value: compactValue(record.adaptation_warning) },
  ];
}

function EvidenceReferencePicker({ options, value, onChange }: { options: Array<{ id: string; label: string }>; value: string[]; onChange: (ids: string[]) => void }) {
  return <label className="is-wide"><span>Choose film evidence references <small>catalog-backed; manual refs remain available</small></span><select aria-label="Film evidence references for scouting report" className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); onChange(ids); const input = event.currentTarget.form?.elements.namedItem('evidence_refs') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, options.length || 4))} value={value}>{options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>;
}

export function ScoutingPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const scoutingQuery = useScoutingWorkspaceQuery();
  const recordQuery = new URLSearchParams(window.location.search);
  const [tab, setTab] = useState<ScoutingTab>(() => recordQuery.get('record_type') === 'scouting' ? 'reports' : 'profiles');
  const [search, setSearch] = useState('');
  const [opponent, setOpponent] = useState('all');
  const [selectedId, setSelectedId] = useState(() => recordQuery.get('record') || '');
  const [evidenceReferenceIds, setEvidenceReferenceIds] = useState<string[]>([]);
  const [tendencyFilters, setTendencyFilters] = useState({ down: 'all', distance: 'all', field_zone: 'all', personnel: 'all', formation: 'all', motion: 'all', front: 'all', coverage: 'all', pressure: 'all' });
  const data = scoutingQuery.data;
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff', 'analyst'].includes(session.role));
  const filmQuery = useFilmWorkspaceQuery('', canAuthor);
  const tendencyQuery = useScoutingTendencyQuery(tendencyFilters, opponent === 'all' ? '' : opponent, tab === 'explorer');
  const evidenceReferenceOptions = useMemo(() => {
    const options = [
      ...(filmQuery.data?.observations ?? []).map((observation) => ({ id: observation.id, label: String(observation.label || observation.id) + ' - film observation' })),
      ...(filmQuery.data?.clips ?? []).map((clip) => ({ id: clip.id, label: clip.id + ' - ' + String(clip.context?.situation || 'film clip') })),
    ];
    return options.filter((option, index, all) => all.findIndex((candidate) => candidate.id === option.id) === index);
  }, [filmQuery.data?.clips, filmQuery.data?.observations]);

  const opponents = useMemo(() => {
    const records = [...(data?.opponent_profiles ?? []), ...(data?.scouting_reports ?? []), ...(data?.matchup_models ?? []), ...(data?.opponent_evolutions ?? [])];
    return [...new Set(records.map((record) => record.opponent).filter((value): value is string => Boolean(value)))].sort();
  }, [data]);
  const rawRecords: FootballRecord[] = tab === 'profiles'
    ? data?.opponent_profiles ?? []
    : tab === 'reports'
      ? data?.scouting_reports ?? []
      : tab === 'matchups'
        ? data?.matchup_models ?? []
        : tab === 'evolution'
          ? data?.opponent_evolutions ?? []
          : [];
  const records = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rawRecords.filter((record) => (opponent === 'all' || record.opponent === opponent) && (!needle || compactValue(record).toLowerCase().includes(needle)));
  }, [opponent, rawRecords, search]);
  const localTendencyRecords = useMemo(() => buildTendencyExplorerRecords(data?.scouting_reports ?? []), [data?.scouting_reports]);
  const tendencyRecords = useMemo(() => tendencyQuery.data ? tendencyQuery.data.records as unknown as TendencyExplorerRecord[] : localTendencyRecords, [localTendencyRecords, tendencyQuery.data]);
  const filteredTendencies = useMemo(() => tendencyQuery.data ? tendencyRecords : tendencyRecords.filter((record) => TENDENCY_DIMENSIONS.every((key) => tendencyFilters[key] === 'all' || record[key] === tendencyFilters[key])), [tendencyFilters, tendencyQuery.data, tendencyRecords]);
  const tendencyOptions = useMemo(() => TENDENCY_DIMENSIONS.reduce<Record<string, string[]>>((result, key) => { result[key] = [...new Set(localTendencyRecords.map((record) => record[key]).filter((value) => value !== 'all'))].sort(); return result; }, {}), [localTendencyRecords]);
  const selected = records.find((record) => record.id === selectedId) ?? records[0];

  const mutation = useMutation({
    mutationFn: (report: FootballRecord) => createScoutingReport(session!, report),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scouting-workspace', session?.organizationId] });
      setTab('reports');
    },
  });
  const tendencyReviewMutation = useMutation({
    mutationFn: (values: Parameters<typeof createCollaborationThread>[1]) => createCollaborationThread(session!, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-workspace', session?.organizationId] });
      queryClient.invalidateQueries({ queryKey: ['operations-inbox', session?.organizationId] });
    },
  });

  function requestTendencyReview(record: TendencyExplorerRecord) {
    if (!session) return;
    const sources = [...new Set([...record.source_clips, ...record.evidence_refs])];
    tendencyReviewMutation.mutate({
      threadId: recordId('COLLAB-THREAD-'),
      title: `Game-plan review: ${record.statement}`,
      body: [
        `Scouting tendency: ${record.statement}`,
        `Report: ${record.report_id}`,
        `Situation: ${[record.down && `D${record.down}`, record.distance, record.field_zone, record.personnel].filter(Boolean).join(' · ') || 'Not supplied'}`,
        `Sample: ${record.sample_size}`,
        `Confidence: ${record.confidence}`,
        `Trend: ${record.trend || 'Not supplied'}`,
        `Review gate: ${sentenceCase(record.review_gate)}`,
        `Contradictions: ${record.contradictions.length ? record.contradictions.join(', ') : 'None declared'}`,
        `Source references: ${sources.length ? sources.join(', ') : 'None supplied'}`,
        'This request routes the evidence to staff review; it does not promote the claim into the game plan.',
      ].join('\n'),
      entityType: 'scouting_tendency',
      entityId: record.report_id,
      deepLink: '/scouting',
      priority: record.review_gate === 'ready_for_staff_review' ? 'normal' : 'high',
    });
  }

  function submitReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const evidenceRefs = splitList(String(form.get('evidence_refs') || ''));
    mutation.mutate({
      id: recordId('SCOUT-REPORT-'),
      opponent: String(form.get('opponent') || ''),
      situation: { down: Number(form.get('down')), distance: String(form.get('distance') || '') },
      claims: [{
        statement: String(form.get('claim') || ''),
        classification: String(form.get('classification') || 'observed'),
        confidence: String(form.get('confidence') || 'moderate'),
        uncertainty: splitList(String(form.get('uncertainty') || '')),
        evidence_refs: evidenceRefs,
      }],
      sample_size: Number(form.get('sample_size')),
      source_refs: evidenceRefs,
      status: 'under_review',
    });
  }

  return (
    <WorkspacePage definition={SCOUTING_WORKSPACE}>
      <WorkbenchFrame
        actions={<button className="button button--primary" disabled={!canAuthor} onClick={() => setTab('author')} type="button"><FilePlus2 size={15} /> New report</button>}
        description="Move from opponent identity to situation-specific evidence, matchup hypotheses, and adaptation warnings while preserving sample size and uncertainty."
        eyebrow="Live competitive intelligence"
        icon={Binoculars}
        title="Opponent intelligence desk"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Scouting workspace views"
          onChange={(next) => { setTab(next as ScoutingTab); setSelectedId(''); }}
          tabs={[
            { id: 'profiles', label: 'Opponent profiles', count: data?.opponent_profiles.length },
            { id: 'reports', label: 'Situation reports', count: data?.scouting_reports.length },
            { id: 'matchups', label: 'Matchups', count: data?.matchup_models.length },
            { id: 'evolution', label: 'Evolution', count: data?.opponent_evolutions.length },
            { id: 'explorer', label: 'Tendency explorer', count: filteredTendencies.length },
            { id: 'author', label: 'Report builder' },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={scoutingQuery.error} loading={scoutingQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Opponents', value: opponents.length, hint: 'distinct profiles' },
              { label: 'Review queue', value: data?.review_count ?? 0, hint: 'human judgment' },
              { label: 'Low samples', value: data?.low_sample_count ?? 0, hint: 'under 10 plays' },
              { label: 'Adaptation alerts', value: data?.adaptation_warning_count ?? 0, hint: 'historical drift' },
            ]} />

            {tab !== 'author' && tab !== 'explorer' ? (
              <>
                <div className="workbench-toolbar">
                  <WorkbenchSearch label="Search scouting records" onChange={setSearch} placeholder={`Search ${sentenceCase(tab).toLowerCase()}…`} value={search} />
                  <div className="workbench-toolbar__group">
                    <label className="filter-select"><span className="sr-only">Filter by opponent</span><select onChange={(event) => setOpponent(event.target.value)} value={opponent}><option value="all">All opponents</option>{opponents.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                    <span className="workbench-form__hint">{records.length} matching records</span>
                  </div>
                </div>
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <div className="workbench-pane__header"><div><h3>{sentenceCase(tab)}</h3><p>Choose an evidence package to inspect its claims and boundaries.</p></div></div>
                    <RecordList
                      emptyMessage="No scouting records match these filters."
                      onSelect={(record) => setSelectedId(record.id)}
                      records={records}
                      selectedId={selected?.id}
                      subtitle={(record) => `${record.opponent || 'Unknown opponent'} · ${record.id}`}
                      title={recordLabel}
                    />
                  </div>
                  <div className="workbench-pane">
                    {selected ? (
                      <RecordInspector
                        eyebrow={`${sentenceCase(tab)} intelligence`}
                        facts={scoutingFacts(selected, tab)}
                        note={tab === 'evolution' ? 'Historical tendency is not treated as a guarantee. The adaptation warning remains attached to every evolution record.' : tab === 'reports' ? 'Sample size, confidence, classification, and uncertainty travel with every scouting claim.' : undefined}
                        status={selected.status}
                        title={recordLabel(selected)}
                      >
                        <div>
                          <p className="eyebrow">Evidence trail</p>
                          <ul className="evidence-stack">
                            {([...(selected.source_refs ?? []), ...(selected.evidence_refs ?? [])]).length
                              ? [...(selected.source_refs ?? []), ...(selected.evidence_refs ?? [])].map((ref) => <li key={ref}><strong>{ref}</strong><span>Organization-authorized supporting reference</span></li>)
                              : <li><strong>Evidence embedded in record</strong><span>{compactValue(selected.sources || selected.claims || selected.matchups)}</span></li>}
                          </ul>
                        </div>
                      </RecordInspector>
                    ) : <div className="record-list__empty">No intelligence package is selected.</div>}
                  </div>
                </div>
              </>
            ) : null}

            {tab === 'explorer' ? (
              <div className="workbench-pane">
                <div className="workbench-pane__header"><div><h3><ChartNoAxesCombined aria-hidden="true" size={16} /> Tendency explorer</h3><p>Slice opponent claims by situation, expose denominator and confidence, and keep the source clips attached before promotion to the game plan.</p></div></div>
                <div className="workbench-toolbar tendency-filter-grid">
                  {Object.keys(tendencyFilters).map((key) => <label className="filter-select" key={key}><span>{sentenceCase(key.replaceAll('_', ' '))}</span><select onChange={(event) => setTendencyFilters((current) => ({ ...current, [key]: event.target.value }))} value={tendencyFilters[key as keyof typeof tendencyFilters]}><option value="all">All</option>{(tendencyOptions[key] ?? []).map((value) => <option key={value} value={value}>{sentenceCase(value)}</option>)}</select></label>)}
                </div>
                <div className="tendency-table-wrap">
                  {tendencyQuery.isLoading ? <p className="workbench-form__hint">Querying the organization scouting index…</p> : null}
                  {tendencyQuery.error ? <p className="mutation-notice mutation-notice--error" role="alert">The server tendency index could not be loaded; local report filters remain visible for review.</p> : null}
                  <div className="tendency-review-grid" aria-label="Tendency evidence review cards">
                    {filteredTendencies.map((record) => {
                      const sources = [...new Set([...record.source_clips, ...record.evidence_refs])];
                      return <article className="tendency-review-card" key={`${record.id}-review`}>
                        <div className="tendency-review-card__header"><div><span className="eyebrow">{record.report_id}</span><h4>{record.statement}</h4></div><span className={`tendency-gate tendency-gate--${record.review_gate}`}>{sentenceCase(record.review_gate)}</span></div>
                        <div className="tendency-review-card__facts"><span><strong>Trend</strong>{record.trend ? sentenceCase(record.trend) : 'Not supplied'}</span><span><strong>Contradictions</strong>{record.contradictions.length ? `${record.contradictions.length} linked` : 'None declared'}</span><span><strong>Sources</strong>{sources.length}</span></div>
                        <div className="tendency-review-card__sources">{sources.length ? sources.map((source) => <Link key={source} to={`/film?search=${encodeURIComponent(source)}`}>{source}</Link>) : <span>No source or clip references supplied.</span>}</div>
                        <button className="button button--secondary tendency-review-button" disabled={!canAuthor || tendencyReviewMutation.isPending} onClick={() => requestTendencyReview(record)} type="button">Request game-plan review</button>
                      </article>;
                    })}
                  </div>
                  <table className="tendency-table"><caption className="sr-only">Filtered opponent tendencies</caption><thead><tr><th scope="col">Tendency</th><th scope="col">Situation</th><th scope="col">Sample</th><th scope="col">Confidence</th><th scope="col">Evidence</th></tr></thead><tbody>{filteredTendencies.map((record) => <tr key={record.id}><th scope="row">{String(record.statement)}</th><td>{[record.down && `D${record.down}`, record.distance, record.field_zone, record.personnel].filter(Boolean).join(' · ')}</td><td>{String(record.sample_size)}</td><td>{sentenceCase(String(record.confidence))}</td><td>{Array.isArray(record.evidence_refs) ? record.evidence_refs.join(', ') : compactValue(record.evidence_refs)}</td></tr>)}</tbody></table>
                  {!filteredTendencies.length ? <div className="record-list__empty">No claims match this situation envelope. Broaden the filters or add a source-linked report.</div> : null}
                </div>
                <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={16} /> A filtered claim is still not a call recommendation. Staff must review sample size, contradictions, source quality, and current opponent context before using it in the game plan. The review action creates a collaboration thread only; it never promotes a scouting claim directly.</div>
                <MutationNotice error={tendencyReviewMutation.error} pending={tendencyReviewMutation.isPending} success={tendencyReviewMutation.isSuccess} successMessage="Review request routed to the collaboration inbox." />
              </div>
            ) : null}

            {tab === 'author' ? (
              canAuthor ? (
                <form className="workbench-form workbench-pane" onSubmit={submitReport}>
                  <div className="workbench-pane__header"><div><h3><FilePlus2 aria-hidden="true" size={16} /> Situation report builder</h3><p>Author one explainable claim with source, sample, confidence, classification, and uncertainty.</p></div></div>
                  <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> Reports are submitted under review. A tendency describes the available sample and never guarantees future opponent behavior.</div>
                  <div className="workbench-form__grid">
                    <label><span>Opponent</span><input defaultValue={opponents[0] || 'OPPONENT-ID'} list="opponent-options" name="opponent" required /><datalist id="opponent-options">{opponents.map((item) => <option key={item} value={item} />)}</datalist></label>
                    <label><span>Sample size</span><input min="1" name="sample_size" required type="number" /></label>
                    <label><span>Down</span><select defaultValue="3" name="down"><option>1</option><option>2</option><option>3</option><option>4</option></select></label>
                    <label><span>Distance</span><select defaultValue="medium" name="distance"><option>short</option><option>medium</option><option>long</option><option>goal_to_go</option></select></label>
                    <label><span>Classification</span><select defaultValue="observed" name="classification"><option>observed</option><option>measured</option><option>reported</option><option>inferred</option><option>hypothesized</option></select></label>
                    <label><span>Confidence</span><select defaultValue="moderate" name="confidence"><option>low</option><option>moderate</option><option>high</option></select></label>
                    <label className="is-wide"><span>Claim</span><textarea name="claim" placeholder="Describe the tendency precisely and condition it on the observed situation." required /></label>
                    <label><span>Uncertainty <small>comma separated</small></span><input name="uncertainty" placeholder="small sample, possible self-scout adjustment" required /></label>
                    <label><span>Evidence references <small>comma separated</small></span><input name="evidence_refs" placeholder="FILM-OBS-…, SOURCE-…" required /></label>
                  </div>
                  <EvidenceReferencePicker onChange={setEvidenceReferenceIds} options={evidenceReferenceOptions} value={evidenceReferenceIds} />
                  <div className="workbench-form__actions"><p className="workbench-form__hint"><TrendingUp aria-hidden="true" size={13} /> Reviewers will see the entire evidence envelope.</p><button className="button button--primary" disabled={mutation.isPending} type="submit"><FilePlus2 size={15} /> Submit for review</button></div>
                  <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Scouting report submitted for human review." />
                </form>
              ) : <p className="approval-boundary">Scouting report authoring requires owner, coaching, or analyst authority.</p>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
