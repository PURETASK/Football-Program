import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BellRing, ExternalLink, Filter, ListChecks, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useSearchParams } from 'react-router-dom';

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
import { useMediaProcessingJobQuery, useOperationsInboxQuery } from '../hooks/useOperationalData';
import { markOperationsNotificationsRead } from '../lib/api';
import { compactValue, sentenceCase } from '../lib/format';
import type { OperationsInboxItem } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { INBOX_WORKSPACE } from './workspaceDefinitions';

type InboxTab = 'all' | 'mine' | 'notifications' | 'reviews' | 'media';

function dueLabel(item: OperationsInboxItem): string {
  if (!item.due_at) return sentenceCase(item.due_state);
  const date = new Date(item.due_at);
  return `${sentenceCase(item.due_state)} · ${Number.isNaN(date.getTime()) ? item.due_at : date.toLocaleString()}`;
}

export function OperationsInboxPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState<InboxTab>('all');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [urgency, setUrgency] = useState('all');
  const [dueState, setDueState] = useState('all');
  const [selectedId, setSelectedId] = useState(() => {
    const jobId = searchParams.get('job');
    return jobId ? `INBOX-media_processing_jobs-${jobId}` : '';
  });
  const filters = useMemo(() => ({
    ...(tab === 'mine' ? { assigned_to_me: 'true' } : {}),
    ...(tab === 'notifications' ? { category: 'notification', unread_only: 'true' } : {}),
    ...(tab === 'reviews' ? { category: 'review' } : {}),
    ...(tab === 'media' ? { origin_category: 'media' } : {}),
  }), [tab]);
  const inboxQuery = useOperationsInboxQuery(filters);
  const mutation = useMutation({
    mutationFn: (notificationIds: string[]) => markOperationsNotificationsRead(session!, notificationIds),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['operations-inbox', session?.organizationId] }),
  });
  const data = inboxQuery.data;
  const statuses = useMemo(() => [...new Set((data?.items ?? []).map((item) => item.status).filter(Boolean))].sort(), [data?.items]);
  const items = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (data?.items ?? []).filter((item) =>
      (status === 'all' || item.status === status)
      && (urgency === 'all' || item.urgency === urgency)
      && (dueState === 'all' || item.due_state === dueState)
      && (!needle || compactValue(item).toLowerCase().includes(needle)),
    );
  }, [data?.items, dueState, search, status, urgency]);
  const selected = items.find((item) => item.id === selectedId) ?? items[0];
  const mediaJobDetailQuery = useMediaProcessingJobQuery(selected?.collection === 'media_processing_jobs' ? selected.record_id : '');
  const blockerCount = items.reduce((total, item) => total + item.blockers.length, 0);
  const evidenceCount = items.reduce((total, item) => total + item.evidence_refs.length, 0);

  return (
    <WorkspacePage definition={INBOX_WORKSPACE}>
      <WorkbenchFrame
        description="Prioritize cross-system work, inspect evidence and blockers, then open the authoritative workflow for the accountable action."
        eyebrow="Cross-system operations"
        icon={ListChecks}
        title="Unified operations inbox"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Operations inbox views"
          onChange={(next) => setTab(next as InboxTab)}
          tabs={[
            { id: 'all', label: 'All work', count: tab === 'all' ? data?.count : undefined },
            { id: 'mine', label: 'Assigned to me' },
            { id: 'notifications', label: 'Unread notifications', count: data?.counts.unread_notifications },
            { id: 'reviews', label: 'Reviews' },
            { id: 'media', label: 'Media processing', count: data?.counts.by_category.media },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={inboxQuery.error} loading={inboxQuery.isLoading}>
          <div className="workbench-body operations-inbox">
            <WorkbenchStats stats={[
              { label: 'Open work', value: data?.count ?? 0, hint: 'visible to this role' },
              { label: 'Overdue', value: data?.counts.overdue ?? 0, hint: 'needs immediate attention' },
              { label: 'Assigned to me', value: data?.counts.assigned_to_me ?? 0, hint: 'accountable next actions' },
              { label: 'Unread alerts', value: data?.counts.unread_notifications ?? 0, hint: 'notifications only' },
            ]} />

            <div className="approval-boundary"><ShieldCheck aria-hidden="true" size={17} /> {data?.automation_boundary}</div>

            <div className="workbench-toolbar">
              <WorkbenchSearch label="Search operations inbox" onChange={setSearch} placeholder="Search work, owner, evidence, blocker…" value={search} />
              <div className="workbench-toolbar__group">
                <label className="filter-select"><span className="sr-only">Filter by status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="all">All states</option>{statuses.map((item) => <option key={item} value={item}>{sentenceCase(item)}</option>)}</select></label>
                <label className="filter-select"><span className="sr-only">Filter by urgency</span><select onChange={(event) => setUrgency(event.target.value)} value={urgency}><option value="all">All urgency</option><option value="critical">Critical</option><option value="high">High</option><option value="normal">Normal</option><option value="low">Low</option></select></label>
                <label className="filter-select"><span className="sr-only">Filter by due state</span><select onChange={(event) => setDueState(event.target.value)} value={dueState}><option value="all">All due states</option><option value="overdue">Overdue</option><option value="due_today">Due today</option><option value="upcoming">Upcoming</option><option value="unscheduled">Unscheduled</option></select></label>
                <Filter aria-hidden="true" size={16} />
              </div>
            </div>

            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                <div className="workbench-pane__header"><div><h3>Accountable work queue</h3><p>{items.length} items match the active filters.</p></div></div>
                <RecordList
                  emptyMessage="No operational work matches these filters."
                  onSelect={(item) => { setSelectedId(item.id); mutation.reset(); if (item.collection === 'media_processing_jobs') setSearchParams({ job: item.record_id }); else setSearchParams({}); }}
                  records={items}
                  selectedId={selected?.id}
                  subtitle={(item) => `${sentenceCase(item.category)} · ${item.owner || item.assigned_to || 'Unassigned'} · ${sentenceCase(item.due_state)}`}
                  title={(item) => item.title}
                />
              </div>
              <div className="workbench-pane">
                {selected ? (
                  <RecordInspector
                    eyebrow={`${sentenceCase(selected.category)} · ${selected.collection}`}
                    facts={[
                      { label: 'Record ID', value: selected.record_id },
                      { label: 'Urgency', value: sentenceCase(selected.urgency) },
                      { label: 'Due state', value: dueLabel(selected) },
                      { label: 'Owner', value: selected.owner || 'Unassigned' },
                      { label: 'Assigned to me', value: selected.assigned_to_me ? 'Yes' : 'No' },
                      ...(selected.operation ? [{ label: 'Operation', value: selected.operation }] : []),
                      ...(selected.asset_id ? [{ label: 'Asset', value: selected.asset_id }] : []),
                      ...(selected.attempt !== undefined ? [{ label: 'Attempt', value: String(selected.attempt) }] : []),
                    ]}
                    note={selected.description || 'Open the owning workspace to inspect the full authoritative record.'}
                    status={selected.status}
                    title={selected.title}
                  >
                    <div className="operations-inbox__actions">
                      <Link className="button button--primary" to={selected.deep_link}><ExternalLink aria-hidden="true" size={15} /> {selected.action_label}</Link>
                      {selected.notification_unread ? <button className="button button--secondary" disabled={mutation.isPending} onClick={() => mutation.mutate([selected.record_id])} type="button"><BellRing aria-hidden="true" size={15} /> Mark read</button> : null}
                    </div>
                    <div className="workbench-split operations-inbox__evidence">
                      <div><p className="eyebrow">Blockers and findings</p><ul className="evidence-stack">{selected.blockers.length ? selected.blockers.map((blocker, index) => <li key={index}><strong>Finding {index + 1}</strong><span>{compactValue(blocker)}</span></li>) : <li><strong>No blockers listed</strong><span>Continue in the owning workspace.</span></li>}</ul></div>
                      <div><p className="eyebrow">Evidence references</p><ul className="evidence-stack">{selected.evidence_refs.length ? selected.evidence_refs.map((ref) => <li key={ref}><strong>{ref}</strong><span>Supporting organization evidence</span></li>) : <li><strong>No evidence references</strong><span>Evidence may be available in the owning system.</span></li>}</ul></div>
                    </div>
                    {selected.last_error ? <div className="approval-boundary"><strong>{selected.last_error.code || 'Media processing error'}</strong> · {selected.last_error.message || 'Review this job in Film Room.'}{selected.next_action ? ` Next action: ${sentenceCase(selected.next_action)}.` : ''}</div> : null}
                    {selected.collection === 'media_processing_jobs' ? <div className="workbench-pane workbench-pane--soft operations-inbox__media-detail"><div className="workbench-pane__header"><div><h4>Processing lifecycle</h4><p>Authoritative history loaded from the organization media store.</p></div></div>{mediaJobDetailQuery.isLoading ? <p className="workbench-form__hint">Loading job history…</p> : mediaJobDetailQuery.error ? <p className="approval-boundary">Detailed history is unavailable. The persisted inbox summary remains available.</p> : mediaJobDetailQuery.data ? <div className="operations-inbox__media-detail-grid"><div><strong>Job status</strong><span>{mediaJobDetailQuery.data.job.status || 'unknown'} · {mediaJobDetailQuery.data.job.attempt ?? 0} attempt{mediaJobDetailQuery.data.job.attempt === 1 ? '' : 's'}</span></div><div><strong>Outputs</strong><span>{mediaJobDetailQuery.data.outputs.length} persisted output{mediaJobDetailQuery.data.outputs.length === 1 ? '' : 's'}</span></div><div><strong>Worker batches</strong><span>{mediaJobDetailQuery.data.batches.length} batch record{mediaJobDetailQuery.data.batches.length === 1 ? '' : 's'}</span></div></div> : null}</div> : null}
                  </RecordInspector>
                ) : <div className="record-list__empty">No operational item selected.</div>}
              </div>
            </div>
            <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Notification marked read and the inbox was refreshed." />
            <p className="workbench-form__hint">{blockerCount} visible blockers · {evidenceCount} visible evidence references · actions remain governed by the owning system.</p>
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
