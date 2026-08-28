import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Clapperboard, ListVideo, MessageSquarePlus, Plus, Tag } from 'lucide-react';
import { lazy, Suspense, useMemo, useState, type FormEvent } from 'react';
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
import { useFilmWorkspaceQuery, useMediaProcessingJobsQuery } from '../hooks/useOperationalData';
import { usePlayDesignsQuery } from '../hooks/useWorkspaceData';
import { appendFilmAnnotation, createFilmAnnotationSession, createFilmClip, createFilmObservation, createFilmPlaylist, createFilmVoiceNote } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import { filmLinkPath, parseFilmLinkedRecordRefs } from '../lib/filmLinks';
import type { FilmAnnotationSession, FilmAsset, FilmClip, FilmLinkedRecordRef, FilmObservation, FilmPlaylist, FootballRecord, PlayDesign, Point } from '../types';
const FilmStudioPanel = lazy(() => import('./FilmStudioPanel').then((module) => ({ default: module.FilmStudioPanel })));
const FilmAssetRegistration = lazy(() => import('./FilmAssetRegistration').then((module) => ({ default: module.FilmAssetRegistration })));
import { WorkspacePage } from './WorkspacePage';
import { FILM_WORKSPACE } from './workspaceDefinitions';

type FilmTab = 'library' | 'observations' | 'playlists' | 'sessions' | 'voice_notes';

function buildObservation(clip: FilmClip, values: { domain: string; label: string; confidence: string; classification: string; evidence: string; playIds?: string[]; linkedRecordRefs?: FilmLinkedRecordRef[] }, subject: string): FilmObservation {
  return {
    id: recordId('FILM-OBS-'),
    clip_id: clip.id,
    asset_id: clip.asset_id,
    linked_play_ids: values.playIds ?? [],
    linked_record_refs: values.linkedRecordRefs ?? [],
    domain: values.domain,
    label: values.label,
    confidence: values.confidence,
    classification: values.classification,
    annotator: subject,
    evidence: values.evidence,
    source_frame: `${clip.id}@${clip.start_seconds ?? 0}`,
    context: {
      team: clip.context?.team || 'TEAM-UNKNOWN',
      opponent: clip.context?.opponent || 'OPPONENT-UNKNOWN',
      situation: { label: clip.context?.situation || 'unspecified' },
    },
    correction: { state: 'uncorrected', corrected_by: null, reason: null },
    status: 'ready_for_review',
  };
}

function FilmRecordInspector({ record, kind }: { record: FootballRecord; kind: FilmTab }) {
  const facts = kind === 'library'
    ? [
        { label: 'Film asset', value: compactValue(record.asset_id) },
        { label: 'Time range', value: `${compactValue(record.start_seconds)}s – ${compactValue(record.end_seconds)}s` },
        { label: 'Opponent', value: compactValue((record.context as Record<string, unknown> | undefined)?.opponent) },
        { label: 'Situation', value: compactValue((record.context as Record<string, unknown> | undefined)?.situation) },
      ]
    : kind === 'observations'
      ? [
          { label: 'Domain', value: sentenceCase(String(record.domain || '')) },
          { label: 'Confidence', value: sentenceCase(String(record.confidence || '')) },
          { label: 'Classification', value: sentenceCase(String(record.classification || '')) },
          { label: 'Evidence', value: compactValue(record.evidence) },
        ]
      : kind === 'playlists'
        ? [
            { label: 'Purpose', value: compactValue(record.purpose) },
            { label: 'Clips', value: compactValue(record.clip_ids) },
            { label: 'Audience', value: compactValue(record.access_roles) },
            { label: 'Owner', value: compactValue(record.owner) },
          ]
        : kind === 'voice_notes'
          ? [
              { label: 'Clip', value: compactValue(record.clip_id) },
              { label: 'Frame', value: `${compactValue(record.frame_seconds)}s` },
              { label: 'Format', value: compactValue(record.mime_type) },
              { label: 'Transcript', value: compactValue(record.transcript) },
            ]
          : [
              { label: 'Clip', value: compactValue(record.clip_id) },
              { label: 'Annotator', value: compactValue(record.annotator) },
              { label: 'Tag domains', value: compactValue(record.allowed_domains) },
              { label: 'Annotations', value: Array.isArray(record.annotations) ? record.annotations.length : 0 },
            ];
  return (
    <div>
      <RecordInspector
        eyebrow={`${sentenceCase(kind)} detail`}
        facts={facts}
        note={kind === 'observations' ? 'Film tags are evidence records. Confidence and classification remain visible so staff can distinguish observation from inference.' : undefined}
        status={record.status}
        title={recordLabel(record)}
      />
      {Array.isArray(record.linked_record_refs) && record.linked_record_refs.length ? <div className="workbench-pane film-record-links"><div className="workbench-pane__header"><div><h4>Connected workflows</h4><p>Evidence lineage stays attached when staff move from Film into decision workspaces.</p></div></div><ul className="evidence-stack">{record.linked_record_refs.map((link) => <li key={`${link.record_type}:${link.record_id}`}><strong>{sentenceCase(link.record_type)} · {link.label || link.record_id}</strong><a href={filmLinkPath(link)}>Open workspace</a></li>)}</ul></div> : null}
    </div>
  );
}

export function FilmPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const filmQuery = useFilmWorkspaceQuery();
  const mediaJobsQuery = useMediaProcessingJobsQuery();
  const playbookQuery = usePlayDesignsQuery();
  const [tab, setTab] = useState<FilmTab>('library');
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff', 'analyst'].includes(session.role));

  const data = filmQuery.data;
  const records = useMemo<FootballRecord[]>(() => {
    const source: FootballRecord[] = tab === 'library'
      ? data?.clips ?? []
      : tab === 'observations'
        ? data?.observations ?? []
        : tab === 'playlists'
          ? data?.playlists ?? []
          : tab === 'sessions'
            ? data?.sessions ?? []
            : data?.voice_notes ?? [];
    const needle = search.trim().toLowerCase();
    return needle ? source.filter((record) => compactValue(record).toLowerCase().includes(needle)) : source;
  }, [data, search, tab]);
  const selected = records.find((record) => record.id === selectedId) ?? records[0];
  const selectedClip = (tab === 'library' ? selected : data?.clips.find((clip) => clip.id === selected?.clip_id)) as FilmClip | undefined;
  const selectedAsset = data?.assets.find((asset) => asset.id === selectedClip?.asset_id) as FilmAsset | undefined;

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['film-workspace', session?.organizationId] });
  const playlistMutation = useMutation({ mutationFn: (values: Parameters<typeof createFilmPlaylist>[1]) => createFilmPlaylist(session!, values), onSuccess: refresh });
  const sessionMutation = useMutation({ mutationFn: (values: Parameters<typeof createFilmAnnotationSession>[1]) => createFilmAnnotationSession(session!, values), onSuccess: refresh });
  const observationMutation = useMutation({ mutationFn: (observation: FilmObservation) => createFilmObservation(session!, observation), onSuccess: refresh });
  const voiceNoteMutation = useMutation({ mutationFn: (values: Parameters<typeof createFilmVoiceNote>[1]) => createFilmVoiceNote(session!, values), onSuccess: refresh });
  const clipMutation = useMutation({ mutationFn: (values: Parameters<typeof createFilmClip>[1]) => createFilmClip(session!, values), onSuccess: refresh });
  const appendMutation = useMutation({ mutationFn: ({ sessionId, observation }: { sessionId: string; observation: FilmObservation }) => appendFilmAnnotation(session!, sessionId, observation), onSuccess: refresh });

  function submitPlaylist(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    playlistMutation.mutate({
      playlistId: recordId('PLAYLIST-'),
      name: String(form.get('name') || ''),
      purpose: String(form.get('purpose') || ''),
      clipIds: splitList(String(form.get('clip_ids') || '')),
      accessRoles: splitList(String(form.get('roles') || '')),
    });
  }

  function submitSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    sessionMutation.mutate({
      sessionId: recordId('SESSION-'),
      clipId: String(form.get('clip_id') || ''),
      allowedDomains: splitList(String(form.get('domains') || '')),
      sourceRefs: splitList(String(form.get('source_refs') || '')),
    });
  }

  function submitObservation(event: FormEvent<HTMLFormElement>, annotationSession?: FilmAnnotationSession) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const clip = annotationSession
      ? data?.clips.find((item) => item.id === annotationSession.clip_id)
      : selectedClip;
    if (!clip) return;
    const observation = buildObservation(clip, {
      domain: String(form.get('domain') || 'coverage'),
      label: String(form.get('label') || ''),
      confidence: String(form.get('confidence') || 'moderate'),
      classification: String(form.get('classification') || 'observed'),
      evidence: String(form.get('evidence') || ''),
      playIds: splitList(String(form.get('play_ids') || '')),
      linkedRecordRefs: parseFilmLinkedRecordRefs(String(form.get('linked_record_refs') || '')),
    }, session?.subject || session?.role || 'film-operator');
    if (annotationSession) appendMutation.mutate({ sessionId: annotationSession.id, observation });
    else observationMutation.mutate(observation);
  }

  function saveTelestration(points: Point[], frameSeconds: number, playIds: string[], linkedRecordRefs: FilmLinkedRecordRef[]) {
    if (!selectedClip) return;
    const observation = buildObservation(selectedClip, {
      domain: 'telestration',
      label: 'Frame telestration',
      confidence: 'moderate',
      classification: 'observed',
      evidence: `Frame-accurate visual mark captured at ${frameSeconds.toFixed(2)} seconds.`,
      playIds,
      linkedRecordRefs,
    }, session?.subject || session?.role || 'film-operator');
    observation.telestration = { points, frame_seconds: frameSeconds };
    observationMutation.mutate(observation);
  }

  function saveTracking(playerId: string, point: Point, frameSeconds: number, playIds: string[], linkedRecordRefs: FilmLinkedRecordRef[]) {
    if (!selectedClip) return;
    const observation = buildObservation(selectedClip, {
      domain: 'player_tracking',
      label: `Player tracking · ${playerId}`,
      confidence: 'moderate',
      classification: 'measured',
      evidence: `Player ${playerId} marked at ${frameSeconds.toFixed(2)} seconds.`,
      playIds,
      linkedRecordRefs,
    }, session?.subject || session?.role || 'film-operator');
    observation.player_tracking = { player_id: playerId, point, frame_seconds: frameSeconds };
    observationMutation.mutate(observation);
  }

  return (
    <WorkspacePage definition={FILM_WORKSPACE}>
      <WorkbenchFrame
        description="Search clips, inspect evidence classifications, assemble teaching playlists, and run bounded annotation sessions without leaving the Film Room."
        eyebrow="Live film operations"
        icon={Clapperboard}
        title="Film intelligence workbench"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Film Room views"
          onChange={(next) => { setTab(next as FilmTab); setSelectedId(''); }}
          tabs={[
            { id: 'library', label: 'Clip library', count: data?.clips.length },
            { id: 'observations', label: 'Evidence tags', count: data?.observations.length },
            { id: 'playlists', label: 'Playlists', count: data?.playlists.length },
            { id: 'sessions', label: 'Annotation sessions', count: data?.sessions.length },
            { id: 'voice_notes', label: 'Voice notes', count: data?.voice_notes.length },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={filmQuery.error} loading={filmQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Assets', value: data?.assets.length ?? 0, hint: 'authorized media' },
              { label: 'Clips', value: data?.clips.length ?? 0, hint: 'bounded segments' },
              { label: 'Evidence tags', value: data?.observations.length ?? 0, hint: 'confidence visible' },
              { label: 'Open sessions', value: data?.sessions.filter((item) => item.status === 'open').length ?? 0, hint: 'staff annotation' },
              { label: 'Voice notes', value: data?.voice_notes.length ?? 0, hint: 'frame-linked audio' },
              { label: 'Media jobs', value: mediaJobsQuery.data?.jobs.length ?? 0, hint: 'worker queue' },
            ]} />
            <div className="workbench-pane workbench-pane--soft film-processing-status" aria-label="Media processing status">
              <div className="workbench-pane__header"><div><h3>Media processing status</h3><p>Authorized worker activity for this organization. Failures remain reviewable and never silently disappear.</p></div><a className="button button--ghost" href="/inbox">Open Operations Inbox</a></div>
              {mediaJobsQuery.isLoading ? <p className="workbench-form__hint">Loading worker status…</p> : mediaJobsQuery.error ? <p className="approval-boundary">Worker status could not be loaded. Check the Operations Inbox for persisted job records.</p> : mediaJobsQuery.data?.jobs.length ? <div className="film-processing-status__grid">{mediaJobsQuery.data.jobs.slice(0, 6).map((job) => <Link aria-label={`Open Operations Inbox for ${job.operation || 'media'} job ${job.id}`} className={`film-processing-job film-processing-job--${String(job.status || 'queued')}`} key={job.id} to={`/inbox?job=${encodeURIComponent(job.id)}`}><div><strong>{job.operation || 'media'} · {job.asset_id || job.id}</strong><span>{job.status || 'queued'} · attempt {job.attempt ?? 0}{job.max_attempts ? `/${job.max_attempts}` : ''}</span></div>{job.last_error ? <small>{job.last_error.code || 'worker error'}: {job.last_error.message || 'Review required'}</small> : job.output_refs?.length ? <small>{job.output_refs.length} output reference{job.output_refs.length === 1 ? '' : 's'} recorded</small> : <small>Open lifecycle details in Operations Inbox</small>}</Link>)}</div> : <p className="workbench-form__hint">No media processing jobs are currently recorded.</p>}
            </div>
            <div className="workbench-toolbar">
              <WorkbenchSearch label="Search Film Room records" onChange={setSearch} placeholder={`Search ${sentenceCase(tab).toLowerCase()}…`} value={search} />
              <span className="workbench-form__hint">Showing {records.length} organization-scoped records</span>
            </div>
            {canAuthor && tab === 'library' ? <Suspense fallback={<div className="workbench-pane"><p className="workbench-form__hint">Opening the managed media importer…</p></div>}><FilmAssetRegistration /></Suspense> : null}
            {selectedClip && selectedAsset ? <Suspense fallback={<div className="workbench-pane"><p className="workbench-form__hint">Opening the Film Intelligence Studio…</p></div>}><FilmStudioPanel asset={selectedAsset} canAuthor={canAuthor} clip={selectedClip} clipPending={clipMutation.isPending} onCreateClip={(values) => clipMutation.mutate(values)} onSaveTelestration={saveTelestration} onSaveTracking={saveTracking} onSaveVoiceNote={(values) => voiceNoteMutation.mutate({ noteId: recordId('VOICE-NOTE-'), ...values })} playOptions={playbookQuery.data ?? []} /></Suspense> : null}
            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                <div className="workbench-pane__header"><div><h3>{sentenceCase(tab)}</h3><p>Select a record to inspect its football context.</p></div></div>
                <RecordList
                  onSelect={(record) => setSelectedId(record.id)}
                  records={records}
                  selectedId={selected?.id}
                  subtitle={(record) => tab === 'library' ? compactValue((record.context as Record<string, unknown> | undefined)?.situation) : record.id}
                  title={recordLabel}
                />
              </div>
              <div className="workbench-pane">
                {selected ? <FilmRecordInspector kind={tab} record={selected} /> : <div className="record-list__empty">Choose or create a record to inspect it here.</div>}
              </div>
            </div>

            {canAuthor && (tab === 'library' || tab === 'observations') && selectedClip ? (
              <form className="workbench-form workbench-pane" onSubmit={(event) => submitObservation(event)}>
                <div className="workbench-pane__header"><div><h3><Tag aria-hidden="true" size={16} /> Add evidence tag</h3><p>Attach a classified, confidence-aware observation to {selectedClip.id}.</p></div></div>
                <div className="workbench-form__grid">
                  <label><span>Domain</span><select defaultValue="coverage" name="domain"><option>coverage</option><option>pressure</option><option>formation</option><option>motion</option><option>concept</option><option>technique</option><option>situation</option><option>result</option></select></label>
                  <label><span>Confidence</span><select defaultValue="moderate" name="confidence"><option>low</option><option>moderate</option><option>high</option></select></label>
                  <label><span>Classification</span><select defaultValue="observed" name="classification"><option>observed</option><option>measured</option><option>reported</option><option>inferred</option><option>hypothesized</option></select></label>
                  <label><span>Tag label</span><input name="label" placeholder="Late Cover 3 buzz rotation" required /></label>
                  <label className="is-wide"><span>Link to Playbook calls <small>comma-separated canonical IDs</small></span><input name="play_ids" placeholder="PLAY-..." /></label>
                  <label className="is-wide"><span>Downstream workflow links <small>type:id, comma separated</small></span><input name="linked_record_refs" placeholder="scouting:SCOUT-REPORT-1, game_plan:GAMEPLAN-1, player_development:ASSIGNMENT-1" /></label>
                  <label className="is-wide"><span>Evidence note</span><textarea name="evidence" placeholder="Describe exactly what the frame supports and what remains uncertain." required /></label>
                </div>
                <div className="workbench-form__actions"><p className="workbench-form__hint">Observation and inference remain explicitly separated.</p><button className="button button--primary" disabled={observationMutation.isPending} type="submit"><Plus size={15} /> Save evidence tag</button></div>
                <MutationNotice error={observationMutation.error} pending={observationMutation.isPending} success={observationMutation.isSuccess} successMessage="Evidence tag saved to the Film Room." />
              </form>
            ) : null}

            {canAuthor && tab === 'playlists' ? (
              <form className="workbench-form workbench-pane" onSubmit={submitPlaylist}>
                <div className="workbench-pane__header"><div><h3><ListVideo aria-hidden="true" size={16} /> Build teaching playlist</h3><p>Sequence approved clips for a role-specific install or correction.</p></div></div>
                <div className="workbench-form__grid">
                  <label><span>Name</span><input name="name" placeholder="Third-down pressure answers" required /></label>
                  <label><span>Access roles <small>comma separated</small></span><input defaultValue="program_owner, coach_staff, analyst, player" name="roles" required /></label>
                  <label className="is-wide"><span>Purpose</span><textarea name="purpose" placeholder="What should the audience learn from this sequence?" required /></label>
                  <label className="is-wide"><span>Clip IDs <small>comma separated</small></span><input defaultValue={data?.clips.map((clip) => clip.id).join(', ')} name="clip_ids" required /></label>
                </div>
                <div className="workbench-form__actions"><p className="workbench-form__hint">Every clip is verified against this organization before save.</p><button className="button button--primary" disabled={playlistMutation.isPending} type="submit"><Plus size={15} /> Create playlist</button></div>
                <MutationNotice error={playlistMutation.error} pending={playlistMutation.isPending} success={playlistMutation.isSuccess} successMessage="Teaching playlist created." />
              </form>
            ) : null}

            {canAuthor && tab === 'sessions' ? (
              <>
                <form className="workbench-form workbench-pane" onSubmit={submitSession}>
                  <div className="workbench-pane__header"><div><h3><MessageSquarePlus aria-hidden="true" size={16} /> Open annotation session</h3><p>Bound the session to one clip, authorized evidence domains, and source references.</p></div></div>
                  <div className="workbench-form__grid">
                    <label><span>Clip</span><select name="clip_id" required>{data?.clips.map((clip) => <option key={clip.id} value={clip.id}>{clip.id}</option>)}</select></label>
                    <label><span>Allowed domains</span><input defaultValue="coverage, pressure, technique" name="domains" required /></label>
                    <label className="is-wide"><span>Source references</span><input defaultValue={data?.assets[0]?.id || 'SOURCE-REQUIRED'} name="source_refs" required /></label>
                  </div>
                  <div className="workbench-form__actions"><p className="workbench-form__hint">The session rejects tags outside its declared domains.</p><button className="button button--primary" disabled={sessionMutation.isPending || !data?.clips.length} type="submit"><Plus size={15} /> Open session</button></div>
                  <MutationNotice error={sessionMutation.error} pending={sessionMutation.isPending} success={sessionMutation.isSuccess} successMessage="Annotation session opened." />
                </form>
                {selected?.status === 'open' ? (
                  <form className="workbench-form workbench-pane" onSubmit={(event) => submitObservation(event, selected as FilmAnnotationSession)}>
                    <div className="workbench-pane__header"><div><h3>Append to {selected.id}</h3><p>Create a session-bounded observation for clip {compactValue(selected.clip_id)}.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Domain</span><select defaultValue={String((selected.allowed_domains as string[] | undefined)?.[0] || 'coverage')} name="domain">{((selected.allowed_domains as string[] | undefined) || ['coverage']).map((domain) => <option key={domain}>{domain}</option>)}</select></label>
                      <label><span>Confidence</span><select defaultValue="moderate" name="confidence"><option>low</option><option>moderate</option><option>high</option></select></label>
                      <label><span>Classification</span><select defaultValue="observed" name="classification"><option>observed</option><option>measured</option><option>inferred</option><option>hypothesized</option></select></label>
                      <label><span>Tag label</span><input name="label" required /></label>
                      <label className="is-wide"><span>Downstream workflow links <small>type:id, comma separated</small></span><input name="linked_record_refs" placeholder="scouting:SCOUT-REPORT-1" /></label>
                      <label className="is-wide"><span>Evidence note</span><textarea name="evidence" required /></label>
                    </div>
                    <div className="workbench-form__actions"><span /><button className="button button--primary" disabled={appendMutation.isPending} type="submit"><Plus size={15} /> Append annotation</button></div>
                    <MutationNotice error={appendMutation.error} pending={appendMutation.isPending} success={appendMutation.isSuccess} successMessage="Annotation appended to the session." />
                  </form>
                ) : null}
              </>
            ) : null}
            {!canAuthor ? <p className="approval-boundary">Your current role has Film Room viewing access. Playlist and annotation authoring require owner, coaching, or analyst authority.</p> : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
