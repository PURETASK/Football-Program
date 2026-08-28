import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, ClipboardList, CornerDownLeft, Gavel, ShieldAlert, XCircle } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';

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
import { useGovernanceInboxQuery } from '../hooks/useOperationalData';
import { reviewGovernanceItem } from '../lib/api';
import { compactValue, recordId, sentenceCase } from '../lib/format';
import type { GovernanceInboxItem } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { REVIEWS_WORKSPACE } from './workspaceDefinitions';

type ReviewTab = 'queue' | 'evidence' | 'decision';

export function reviewRecordKey(item: Pick<GovernanceInboxItem, 'collection' | 'id'>): string {
  return `${item.collection}:${item.id}`;
}

export function ReviewsPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const inboxQuery = useGovernanceInboxQuery();
  const [tab, setTab] = useState<ReviewTab>('queue');
  const [search, setSearch] = useState('');
  const [collection, setCollection] = useState('all');
  const [status, setStatus] = useState('all');
  const [selectedId, setSelectedId] = useState('');
  const data = inboxQuery.data;
  const isOwner = session?.role === 'program_owner';
  const collections = useMemo(() => [...new Set((data?.items ?? []).map((item) => item.collection))].sort(), [data?.items]);
  const statuses = useMemo(() => [...new Set((data?.items ?? []).map((item) => item.status).filter((value): value is string => Boolean(value)))].sort(), [data?.items]);
  const items = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (data?.items ?? []).filter((item) =>
      (collection === 'all' || item.collection === collection)
      && (status === 'all' || item.status === status)
      && (!needle || compactValue(item).toLowerCase().includes(needle))
    );
  }, [collection, data?.items, search, status]);
  const selected = items.find((item) => reviewRecordKey(item) === selectedId) ?? items[0];
  const blockerCount = (data?.items ?? []).reduce((total, item) => total + item.blockers.length, 0);
  const evidenceCount = (data?.items ?? []).reduce((total, item) => total + item.evidence_refs.length, 0);

  const mutation = useMutation({
    mutationFn: (values: Parameters<typeof reviewGovernanceItem>[1]) => reviewGovernanceItem(session!, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['governance-inbox', session?.organizationId] }),
  });

  function submitDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      collection: selected.collection,
      recordId: selected.id,
      decision: String(form.get('decision')) as 'returned' | 'rejected' | 'approved',
      decisionRef: recordId('DEC-GOV-'),
      rationale: String(form.get('rationale') || ''),
    });
  }

  const canApproveHere = selected?.collection === 'change_requests' && selected.can_approve;

  return (
    <WorkspacePage definition={REVIEWS_WORKSPACE}>
      <WorkbenchFrame
        description="Triage pending organization records, inspect blockers and evidence, then record bounded return, rejection, or canonical change-request approval decisions."
        eyebrow="Human decision operations"
        icon={Gavel}
        title="Reviews and approvals inbox"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Reviews workspace views"
          onChange={(next) => setTab(next as ReviewTab)}
          tabs={[
            { id: 'queue', label: 'Decision queue', count: data?.count },
            { id: 'evidence', label: 'Evidence & blockers', count: blockerCount },
            { id: 'decision', label: 'Decision record' },
          ]}
        />
        <WorkbenchState connected={Boolean(session)} error={inboxQuery.error} loading={inboxQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Pending records', value: data?.count ?? 0, hint: 'all governed types' },
              { label: 'Human review', value: data?.items.filter((item) => item.human_review_required).length ?? 0, hint: 'explicit judgment' },
              { label: 'Blockers / issues', value: blockerCount, hint: 'must remain visible' },
              { label: 'Evidence refs', value: evidenceCount, hint: 'decision support' },
            ]} />
            <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> {data?.approval_boundary}</div>

            <div className="workbench-toolbar">
              <WorkbenchSearch label="Search review queue" onChange={setSearch} placeholder="Search ID, owner, evidence, blocker…" value={search} />
              <div className="workbench-toolbar__group">
                <label className="filter-select"><span className="sr-only">Filter by collection</span><select onChange={(event) => setCollection(event.target.value)} value={collection}><option value="all">All record types</option>{collections.map((item) => <option key={item} value={item}>{sentenceCase(item)}</option>)}</select></label>
                <label className="filter-select"><span className="sr-only">Filter by status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="all">All states</option>{statuses.map((item) => <option key={item} value={item}>{sentenceCase(item)}</option>)}</select></label>
              </div>
            </div>

            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                <div className="workbench-pane__header"><div><h3>Governance queue</h3><p>{items.length} records match the active filters.</p></div></div>
                <RecordList
                  emptyMessage="No governance records match these filters."
                  onSelect={(item) => { setSelectedId(reviewRecordKey(item)); if (tab === 'decision') mutation.reset(); }}
                  records={items}
                  selectedId={selected ? reviewRecordKey(selected) : undefined}
                  subtitle={(item) => `${sentenceCase(item.collection)} · ${item.owner || 'No owner recorded'}`}
                  title={(item) => item.id}
                />
              </div>
              <div className="workbench-pane">
                {selected ? (
                  <RecordInspector
                    eyebrow={sentenceCase(selected.collection)}
                    facts={[
                      { label: 'Record ID', value: selected.id },
                      { label: 'Owner', value: compactValue(selected.owner) },
                      { label: 'Human review', value: selected.human_review_required ? 'Required' : 'Advisory' },
                      { label: 'Approval route', value: canApproveHere ? 'Change-request primitive available here' : 'Owning workflow endpoint required' },
                    ]}
                    note={canApproveHere ? 'This item is a change request, so approval can safely invoke its canonical approval primitive from this inbox.' : 'Return and rejection are available here. Approval must occur in the owning workflow so its domain-specific validation cannot be bypassed.'}
                    status={selected.status}
                    title={selected.id}
                  >
                    {tab === 'evidence' || tab === 'queue' ? (
                      <div className="workbench-split">
                        <div><p className="eyebrow">Blockers and issues</p><ul className="evidence-stack">{selected.blockers.length ? selected.blockers.map((blocker, index) => <li key={index}><strong>Finding {index + 1}</strong><span>{compactValue(blocker)}</span></li>) : <li><strong>No blockers listed</strong><span>Review status or policy may still require an explicit decision.</span></li>}</ul></div>
                        <div><p className="eyebrow">Evidence references</p><ul className="evidence-stack">{selected.evidence_refs.length ? selected.evidence_refs.map((ref) => <li key={ref}><strong>{ref}</strong><span>Supporting organization evidence</span></li>) : <li><strong>No references attached</strong><span>Return the record if its applicable workflow requires supporting evidence.</span></li>}</ul></div>
                      </div>
                    ) : null}
                  </RecordInspector>
                ) : <div className="record-list__empty"><ClipboardList aria-hidden="true" size={22} /> No pending record selected.</div>}
              </div>
            </div>

            {tab === 'decision' && selected ? (
              isOwner ? (
                <form className="workbench-form workbench-pane" onSubmit={submitDecision}>
                  <div className="workbench-pane__header"><div><h3>Record decision for {selected.id}</h3><p>The decision, rationale, actor, timestamp, and generated reference are persisted as immutable governance evidence.</p></div></div>
                  <div className="workbench-form__grid">
                    <label><span>Decision</span><select defaultValue="returned" name="decision"><option value="returned">Return for revision</option><option value="rejected">Reject</option>{canApproveHere ? <option value="approved">Approve change request</option> : null}</select></label>
                    <label className="is-wide"><span>Decision rationale</span><textarea name="rationale" placeholder="Explain what must change, why it is rejected, or why the evidence supports approval." required /></label>
                  </div>
                  <div className="workbench-form__actions"><p className="workbench-form__hint">{canApproveHere ? 'Approval uses the canonical change-request primitive.' : 'Approval is intentionally unavailable in this generic inbox.'}</p><button className="button button--primary" disabled={mutation.isPending} type="submit"><CheckCircle2 size={15} /> Record decision</button></div>
                  <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Governance decision recorded with evidence." />
                  <div className="workbench-toolbar__group" aria-hidden="true"><CornerDownLeft size={14} /><span className="workbench-form__hint">Return preserves the item for revision.</span><XCircle size={14} /><span className="workbench-form__hint">Reject closes it with rationale.</span></div>
                </form>
              ) : <p className="approval-boundary">Your role can inspect the governance inbox. Recording return, rejection, or approval decisions requires program-owner authority.</p>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
