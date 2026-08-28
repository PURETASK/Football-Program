import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BellRing, CheckCircle2, Link2, MessageCircle, Plus, Send, UsersRound, Wifi, WifiOff } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
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
import { useCollaborationEventStream, useCollaborationWorkspaceQuery } from '../hooks/useOperationalData';
import {
  ApiError,
  appendCollaborationComment,
  assignCollaborationThread,
  createCollaborationThread,
  leaveCollaborationPresence,
  markCollaborationNotificationsRead,
  resolveCollaborationThread,
  updateCollaborationPresence,
} from '../lib/api';
import {
  enqueueCollaborationAction,
  markCollaborationActionFailed,
  readCollaborationOutbox,
  removeCollaborationAction,
  type CollaborationOutboxAction,
} from '../lib/collaborationOutbox';
import { compactValue, recordId, sentenceCase, splitList } from '../lib/format';
import type { AppSession, CollaborationNotification, CollaborationThread, FootballRecord } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { COLLABORATION_WORKSPACE } from './workspaceDefinitions';

type CollaborationTab = 'threads' | 'notifications' | 'activity';

const AUTHOR_ROLES = new Set(['coach_staff', 'analyst', 'program_owner', 'validator', 'performance_staff']);
const RESOLVE_ROLES = new Set(['coach_staff', 'program_owner', 'validator']);

type PendingCollaborationAction = Pick<CollaborationOutboxAction, 'id' | 'kind' | 'payload'>;

function shouldRetryCollaborationFailure(failure: unknown): boolean {
  if (failure instanceof ApiError) return failure.status === 408 || failure.status === 425 || failure.status === 429 || failure.status >= 500;
  return true;
}

async function deliverCollaborationAction(session: AppSession, action: CollaborationOutboxAction): Promise<void> {
  if (action.kind === 'thread') {
    await createCollaborationThread(session, action.payload);
  } else if (action.kind === 'comment') {
    await appendCollaborationComment(session, action.payload);
  } else if (action.kind === 'assign') {
    await assignCollaborationThread(session, action.payload);
  } else if (action.kind === 'resolve') {
    await resolveCollaborationThread(session, action.payload);
  } else {
    await markCollaborationNotificationsRead(session, action.payload.notificationIds);
  }
}

function threadLabel(thread: CollaborationThread): string {
  return thread.title || thread.id;
}

function CollaborationThreadInspector({
  thread,
  canAuthor,
  canResolve,
  onComment,
  onAssign,
  onResolve,
  commentPending,
  assignPending,
  resolvePending,
  commentError,
  assignError,
  resolveError,
}: {
  thread: CollaborationThread;
  canAuthor: boolean;
  canResolve: boolean;
  onComment: (event: FormEvent<HTMLFormElement>) => void;
  onAssign: (event: FormEvent<HTMLFormElement>) => void;
  onResolve: (decision: 'resolved' | 'reopened') => void;
  commentPending: boolean;
  assignPending: boolean;
  resolvePending: boolean;
  commentError?: unknown;
  assignError?: unknown;
  resolveError?: unknown;
}) {
  return (
    <RecordInspector
      eyebrow={`${sentenceCase(thread.entity_type)} · ${thread.entity_id}`}
      facts={[
        { label: 'Priority', value: sentenceCase(thread.priority) },
        { label: 'Assignee', value: thread.assigned_to || 'Unassigned' },
        { label: 'Due', value: thread.due_at || 'No deadline' },
        { label: 'Participants', value: compactValue(thread.participants) },
      ]}
      note="This collaboration record routes context and accountability. It does not replace the owning system's approval, publishing, validation, or player-status controls."
      status={thread.status}
      title={threadLabel(thread)}
    >
      <div className="comment-stack">
        {(thread.comments ?? []).map((comment) => (
          <article className="comment-card" key={comment.id}>
            <strong>{comment.author || 'Staff'} · {sentenceCase(comment.role)}</strong>
            <p>{comment.body}</p>
            <small>{String(comment.created_at || 'Recorded in organization history')}{comment.mentions?.length ? ` · Mentions: ${comment.mentions.join(', ')}` : ''}</small>
          </article>
        ))}
      </div>

      {thread.deep_link ? <Link className="button button--secondary" to={thread.deep_link}><Link2 size={14} /> Open owning workspace</Link> : null}

      {canAuthor && thread.status === 'open' ? (
        <>
          <form className="workbench-form" onSubmit={onComment}>
            <div className="workbench-pane__header"><div><h4><MessageCircle size={15} /> Reply in thread</h4><p>Keep the discussion attached to the source decision.</p></div></div>
            <label><span>Comment</span><textarea name="body" placeholder="Add context, a question, or a proposed next step…" required /></label>
            <label><span>Mentions <small>comma separated</small></span><input name="mentions" placeholder="coach, analyst" /></label>
            <div className="workbench-form__actions"><span /><button className="button button--primary" disabled={commentPending} type="submit"><Send size={14} /> Reply</button></div>
            <MutationNotice error={commentError} pending={commentPending} success={false} successMessage="Reply added." />
          </form>
          <form className="workbench-form" onSubmit={onAssign}>
            <div className="workbench-pane__header"><div><h4>Assignment and deadline</h4><p>Make the accountable next action visible to the whole staff.</p></div></div>
            <div className="workbench-form__grid"><label><span>Assign to</span><input name="assignee" defaultValue={thread.assigned_to || ''} required /></label><label><span>Priority</span><select defaultValue={thread.priority || 'normal'} name="priority"><option>critical</option><option>high</option><option>normal</option><option>low</option></select></label><label className="is-wide"><span>Due at <small>ISO date/time or team convention</small></span><input defaultValue={thread.due_at || ''} name="due_at" placeholder="2026-08-28T16:00:00Z" /></label></div>
            <div className="workbench-form__actions"><span /><button className="button button--secondary" disabled={assignPending} type="submit">Assign work</button></div>
            <MutationNotice error={assignError} pending={assignPending} success={false} successMessage="Assignment saved." />
          </form>
        </>
      ) : null}

      {canResolve ? (
        <div className="workbench-form__actions">
          <button className="button button--secondary" disabled={resolvePending} onClick={() => onResolve(thread.status === 'resolved' ? 'reopened' : 'resolved')} type="button"><CheckCircle2 size={14} /> {thread.status === 'resolved' ? 'Reopen thread' : 'Resolve thread'}</button>
          <MutationNotice error={resolveError} pending={resolvePending} success={false} successMessage="Thread state saved." />
        </div>
      ) : null}
    </RecordInspector>
  );
}

export function CollaborationPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<CollaborationTab>('threads');
  const [status, setStatus] = useState('all');
  const [assigned, setAssigned] = useState('all');
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [outbox, setOutbox] = useState<CollaborationOutboxAction[]>([]);
  const [outboxNotice, setOutboxNotice] = useState('');
  const presenceSessionId = useMemo(() => recordId('COLLAB-SESSION-'), []);
  const dataQuery = useCollaborationWorkspaceQuery({ ...(status !== 'all' ? { status } : {}), ...(assigned === 'mine' ? { assigned_to: 'me' } : {}) });
  const collaborationStream = useCollaborationEventStream();
  const data = dataQuery.data;
  const canAuthor = Boolean(session && AUTHOR_ROLES.has(session.role));
  const canResolve = Boolean(session && RESOLVE_ROLES.has(session.role));
  const refresh = useCallback(() => queryClient.invalidateQueries({ queryKey: ['collaboration-workspace', session?.organizationId] }), [queryClient, session?.organizationId]);
  const queueAction = useCallback(async (action: PendingCollaborationAction) => {
    if (!session) return;
    const next = await enqueueCollaborationAction(session, action);
    setOutbox(next);
    setOutboxNotice('Saved securely to the organization outbox. It will retry when staff sync is available.');
  }, [session]);
  const runWithOfflineQueue = useCallback(async <T,>(action: PendingCollaborationAction, send: () => Promise<T>): Promise<T | null> => {
    if (!session) return null;
    try {
      return await send();
    } catch (failure) {
      if (!shouldRetryCollaborationFailure(failure)) throw failure;
      await queueAction(action);
      return null;
    }
  }, [queueAction, session]);
  const flushOutbox = useCallback(async () => {
    if (!session || typeof navigator !== 'undefined' && navigator.onLine === false) return;
    let pending = await readCollaborationOutbox(session);
    let delivered = 0;
    for (const action of pending) {
      try {
        await deliverCollaborationAction(session, action);
        pending = await removeCollaborationAction(session, action.id);
        delivered += 1;
      } catch (failure) {
        pending = await markCollaborationActionFailed(session, action, failure);
        if (shouldRetryCollaborationFailure(failure)) break;
      }
    }
    setOutbox(pending);
    if (delivered) {
      setOutboxNotice(`${delivered} offline collaboration ${delivered === 1 ? 'action' : 'actions'} synchronized.`);
      await refresh();
    }
  }, [refresh, session]);

  const threadMutation = useMutation({
    mutationFn: (values: Parameters<typeof createCollaborationThread>[1]) => runWithOfflineQueue({ id: values.threadId, kind: 'thread', payload: values }, () => createCollaborationThread(session!, values)),
    onSuccess: (result) => { if (result) void refresh(); },
  });
  const commentMutation = useMutation({
    mutationFn: (values: Parameters<typeof appendCollaborationComment>[1]) => runWithOfflineQueue({ id: values.commentId, kind: 'comment', payload: values }, () => appendCollaborationComment(session!, values)),
    onSuccess: (result) => { if (result) void refresh(); },
  });
  const assignMutation = useMutation({
    mutationFn: (values: Parameters<typeof assignCollaborationThread>[1]) => runWithOfflineQueue({ id: recordId('OUTBOX-ASSIGN-'), kind: 'assign', payload: values }, () => assignCollaborationThread(session!, values)),
    onSuccess: (result) => { if (result) void refresh(); },
  });
  const resolveMutation = useMutation({
    mutationFn: (values: Parameters<typeof resolveCollaborationThread>[1]) => runWithOfflineQueue({ id: recordId('OUTBOX-RESOLVE-'), kind: 'resolve', payload: values }, () => resolveCollaborationThread(session!, values)),
    onSuccess: (result) => { if (result) void refresh(); },
  });
  const notificationMutation = useMutation({
    mutationFn: (ids: string[]) => runWithOfflineQueue({ id: `OUTBOX-NOTIFICATIONS-${ids.join('-')}`, kind: 'mark_notifications_read', payload: { notificationIds: ids } }, () => markCollaborationNotificationsRead(session!, ids)),
    onSuccess: (result) => { if (result) void refresh(); },
  });

  useEffect(() => {
    if (!session) {
      setOutbox([]);
      return undefined;
    }
    let active = true;
    void readCollaborationOutbox(session).then((actions) => { if (active) setOutbox(actions); });
    const onOnline = () => void flushOutbox();
    window.addEventListener('online', onOnline);
    const timer = window.setInterval(onOnline, 20_000);
    void flushOutbox();
    return () => { active = false; window.removeEventListener('online', onOnline); window.clearInterval(timer); };
  }, [flushOutbox, session]);

  useEffect(() => {
    if (!session) return undefined;
    const beat = () => void updateCollaborationPresence(session, presenceSessionId).catch(() => undefined);
    beat();
    const timer = window.setInterval(beat, 20_000);
    return () => { window.clearInterval(timer); void leaveCollaborationPresence(session, presenceSessionId).catch(() => undefined); };
  }, [presenceSessionId, session]);

  const threads = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (data?.threads ?? []).filter((thread) => !needle || compactValue(thread).toLowerCase().includes(needle));
  }, [data?.threads, search]);
  const notifications = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (data?.notifications ?? []).filter((notification) => !needle || compactValue(notification).toLowerCase().includes(needle));
  }, [data?.notifications, search]);
  const selected = threads.find((thread) => thread.id === selectedId) ?? threads[0];

  function submitThread(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    threadMutation.mutate({
      threadId: recordId('COLLAB-THREAD-'), title: String(form.get('title') || ''), body: String(form.get('body') || ''), entityType: String(form.get('entity_type') || 'workspace'), entityId: String(form.get('entity_id') || 'WORKSPACE'), deepLink: String(form.get('deep_link') || '/inbox'), assignee: String(form.get('assignee') || '') || undefined, mentions: splitList(String(form.get('mentions') || '')), participants: splitList(String(form.get('participants') || '')), priority: String(form.get('priority') || 'normal'), dueAt: String(form.get('due_at') || '') || undefined,
    });
  }

  function submitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    commentMutation.mutate({ threadId: selected.id, commentId: recordId('COMMENT-'), body: String(form.get('body') || ''), mentions: splitList(String(form.get('mentions') || '')) });
  }

  function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    assignMutation.mutate({ threadId: selected.id, assignee: String(form.get('assignee') || ''), dueAt: String(form.get('due_at') || '') || undefined, priority: String(form.get('priority') || 'normal') });
  }

  return (
    <WorkspacePage definition={COLLABORATION_WORKSPACE}>
      <WorkbenchFrame
        description="Coordinate decisions across football workspaces with threaded context, accountable assignments, mentions, presence, notifications, and an auditable activity feed."
        eyebrow="Connected staff operations"
        icon={UsersRound}
        title="Staff collaboration hub"
      >
        <WorkbenchTabs activeTab={tab} label="Collaboration workspace views" onChange={(next) => setTab(next as CollaborationTab)} tabs={[{ id: 'threads', label: 'Threads', count: data?.counts.open_threads }, { id: 'notifications', label: 'Notifications', count: data?.counts.unread_notifications }, { id: 'activity', label: 'Activity' }]} />
        <WorkbenchState connected={Boolean(session)} error={dataQuery.error} loading={dataQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[{ label: 'Open threads', value: data?.counts.open_threads ?? 0, hint: 'cross-system decisions' }, { label: 'Assigned to me', value: data?.counts.assigned_to_me ?? 0, hint: 'accountable work' }, { label: 'Unread notifications', value: data?.counts.unread_notifications ?? 0, hint: 'mentions and assignments' }, { label: 'Staff present', value: data?.counts.active_presence ?? 0, hint: 'active sessions' }]} />
            <div className="approval-boundary"><UsersRound aria-hidden="true" size={17} /> {data?.boundary}</div>
            {outbox.length ? <div className="approval-boundary" role="status"><WifiOff aria-hidden="true" size={16} /> {outbox.length} collaboration {outbox.length === 1 ? 'action' : 'actions'} waiting in the encrypted offline outbox{outbox.some((action) => action.lastError) ? ' and marked for retry review' : ''}. <button className="button button--secondary" onClick={() => void flushOutbox()} type="button">Retry now</button></div> : outboxNotice ? <div className="approval-boundary" role="status"><CheckCircle2 aria-hidden="true" size={16} /> {outboxNotice}</div> : null}
            <div className="approval-boundary"><span aria-hidden="true">{collaborationStream.status === 'live' ? <Wifi size={16} /> : <WifiOff size={16} />}</span> {collaborationStream.status === 'live' ? 'Live organization collaboration sync is connected.' : collaborationStream.status === 'offline' ? 'Live sync is reconnecting; the workspace will replay missed events.' : 'Connecting live organization collaboration sync…'}</div>
            <div className="workbench-toolbar"><WorkbenchSearch label="Search collaboration" onChange={setSearch} placeholder="Search threads, people, entities, comments…" value={search} /><div className="workbench-toolbar__group"><label className="filter-select"><span className="sr-only">Filter thread status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="all">All thread states</option><option value="open">Open</option><option value="resolved">Resolved</option></select></label><label className="filter-select"><span className="sr-only">Filter assignment</span><select onChange={(event) => setAssigned(event.target.value)} value={assigned}><option value="all">All assignments</option><option value="mine">Assigned to me</option></select></label></div></div>

            {tab === 'threads' ? <div className="workbench-split"><div className="workbench-pane workbench-pane--soft"><div className="workbench-pane__header"><div><h3>Decision threads</h3><p>{threads.length} organization-scoped threads.</p></div></div><RecordList emptyMessage="No collaboration threads match the current view." onSelect={(thread) => setSelectedId(thread.id)} records={threads} selectedId={selected?.id} subtitle={(thread) => `${sentenceCase(thread.priority)} · ${thread.assigned_to || 'Unassigned'} · ${thread.comments?.length ?? 0} messages`} title={threadLabel} /></div><div className="workbench-pane">{selected ? <CollaborationThreadInspector assignError={assignMutation.error} assignPending={assignMutation.isPending} canAuthor={canAuthor} canResolve={canResolve} commentError={commentMutation.error} commentPending={commentMutation.isPending} onAssign={submitAssignment} onComment={submitComment} onResolve={(decision) => resolveMutation.mutate({ threadId: selected.id, decision, rationale: decision === 'resolved' ? 'Staff decision recorded in the collaboration hub.' : 'Thread reopened for additional evidence or discussion.' })} resolveError={resolveMutation.error} resolvePending={resolveMutation.isPending} thread={selected} /> : <div className="record-list__empty">Select a thread to inspect its context and accountable next action.</div>}</div></div> : null}

            {tab === 'notifications' ? <div className="workbench-pane"><div className="workbench-pane__header"><div><h3><BellRing size={16} /> Notification center</h3><p>Mentions, assignments, and replies addressed to this role.</p></div></div><div className="comment-stack">{notifications.length ? notifications.map((notification: CollaborationNotification) => <article className="comment-card" key={notification.id}><strong>{notification.title}</strong><p>{notification.body || notification.description}</p><small>{String(notification.created_at || 'Recorded')} · {notification.status === 'read' ? 'Read' : 'Unread'}</small>{notification.status !== 'read' ? <button className="button button--secondary" onClick={() => notificationMutation.mutate([notification.id])} type="button"><CheckCircle2 size={14} /> Mark read</button> : null}</article>) : <div className="record-list__empty">No notifications match the current view.</div>}</div></div> : null}

            {tab === 'activity' ? <div className="workbench-pane"><div className="workbench-pane__header"><div><h3>Activity feed</h3><p>Recent collaboration events with actor and subject context.</p></div></div><div className="comment-stack">{data?.activity.length ? data.activity.map((activity) => <article className="comment-card" key={activity.id}><strong>{sentenceCase(activity.event_type)} · {activity.actor || 'Staff'}</strong><p>{activity.subject || activity.id}</p><small>{String(activity.created_at || 'Recorded')} · {compactValue(activity.payload)}</small></article>) : <div className="record-list__empty">No collaboration activity yet.</div>}</div></div> : null}

            {canAuthor ? <form className="workbench-form workbench-pane" onSubmit={submitThread}><div className="workbench-pane__header"><div><h3><Plus size={16} /> Start a cross-system thread</h3><p>Link the conversation to the exact owning record and preserve the navigation path.</p></div></div><div className="workbench-form__grid"><label><span>Title</span><input name="title" placeholder="Confirm third-down pressure answer" required /></label><label><span>Entity type</span><input defaultValue="game_plan" name="entity_type" required /></label><label><span>Entity ID</span><input name="entity_id" placeholder="GAMEPLAN-2026-WK01" required /></label><label><span>Owning route</span><input defaultValue="/game-plan" name="deep_link" required /></label><label><span>Assign to</span><input name="assignee" placeholder="coach-jones" /></label><label><span>Priority</span><select defaultValue="normal" name="priority"><option>critical</option><option>high</option><option>normal</option><option>low</option></select></label><label><span>Due at</span><input name="due_at" placeholder="2026-08-28T16:00:00Z" /></label><label><span>Mentions <small>comma separated</small></span><input name="mentions" placeholder="oc, analyst" /></label><label className="is-wide"><span>Participants <small>comma separated</small></span><input name="participants" placeholder="position-coach, coordinator" /></label><label className="is-wide"><span>Opening context</span><textarea name="body" placeholder="State the decision, evidence, uncertainty, and next action." required /></label></div><div className="workbench-form__actions"><p className="workbench-form__hint">High-impact transitions remain in the owning workflow.</p><button className="button button--primary" disabled={threadMutation.isPending} type="submit"><MessageCircle size={14} /> Open thread</button></div><MutationNotice error={threadMutation.error} pending={threadMutation.isPending} success={threadMutation.isSuccess} successMessage="Collaboration thread created." /></form> : <p className="approval-boundary">Your role can inspect collaboration records and notifications. Creating, assigning, or resolving staff work requires an authorized collaboration role.</p>}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
