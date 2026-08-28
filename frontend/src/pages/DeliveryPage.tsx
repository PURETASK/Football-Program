import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BadgeCheck, CalendarDays, CheckCircle2, FileCheck2, Plus, ShieldAlert } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';

import { useSession } from '../auth/SessionContext';
import { MutationNotice, RecordInspector, RecordList, WorkbenchFrame, WorkbenchSearch, WorkbenchState, WorkbenchStats, WorkbenchTabs } from '../components/OperationalWorkbench';
import { useDeliveryWorkspaceQuery } from '../hooks/useOperationalData';
import { completeDeliveryTask, createDeliveryPacket, createDeliveryTask } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { DeliveryTask } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { DELIVERY_WORKSPACE } from './workspaceDefinitions';

import '../styles/delivery.css';

type DeliveryTab = 'agenda' | 'packets' | 'task' | 'packet';

function dueLabel(task: DeliveryTask): string {
  if (!task.due_at) return 'No due time';
  const point = new Date(task.due_at);
  return Number.isNaN(point.getTime()) ? task.due_at : point.toLocaleString([], { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function LinkedRecordPicker({ options, value, onChange }: { options: Array<{ id: string; label: string }>; value: string[]; onChange: (ids: string[]) => void }) {
  return <label className="is-wide"><span>Choose linked records <small>release, practice, packet, or delivery artifacts</small></span><select aria-label="Linked delivery records" className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); onChange(ids); const input = event.currentTarget.form?.elements.namedItem('linked_records') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, options.length || 4))} value={value}>{options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>;
}

export function DeliveryPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<DeliveryTab>('agenda');
  const [search, setSearch] = useState('');
  const [week, setWeek] = useState('WEEK-1');
  const [selectedId, setSelectedId] = useState(() => new URLSearchParams(window.location.search).get('record') || '');
  const [linkedRecordIds, setLinkedRecordIds] = useState<string[]>([]);
  const dataQuery = useDeliveryWorkspaceQuery(week);
  const data = dataQuery.data;
  const tasks = useMemo(() => { const needle = search.trim().toLowerCase(); return (data?.tasks ?? []).filter((task) => !needle || compactValue(task).toLowerCase().includes(needle)); }, [data?.tasks, search]);
  const selected = tasks.find((task) => task.id === selectedId) ?? tasks[0];
  const linkedRecordOptions = useMemo(() => {
    const records = [...(data?.release_snapshots ?? []), ...(data?.practice_plans ?? []), ...(data?.packets ?? []), ...(data?.delivery_packets ?? [])];
    const seen = new Set<string>();
    return records.filter((record) => {
      if (!record.id || seen.has(record.id)) return false;
      seen.add(record.id);
      return true;
    }).map((record) => ({ id: record.id, label: recordLabel(record) + ' - ' + sentenceCase(String(record.status || 'record')) }));
  }, [data?.delivery_packets, data?.packets, data?.practice_plans, data?.release_snapshots]);
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff', 'analyst'].includes(session.role));
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['delivery-workspace', session?.organizationId, week] });
  const createMutation = useMutation({ mutationFn: (values: Parameters<typeof createDeliveryTask>[1]) => createDeliveryTask(session!, values), onSuccess: () => { refresh(); setTab('agenda'); } });
  const packetMutation = useMutation({ mutationFn: (values: Parameters<typeof createDeliveryPacket>[1]) => createDeliveryPacket(session!, values), onSuccess: () => { refresh(); setTab('packets'); } });
  const completeMutation = useMutation({ mutationFn: (taskId: string) => completeDeliveryTask(session!, taskId), onSuccess: refresh });

  function submitTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const localDue = String(form.get('due_at') || '');
    createMutation.mutate({ taskId: recordId('DELIVERY-TASK-'), title: String(form.get('title') || ''), category: String(form.get('category') || ''), owner: String(form.get('owner') || ''), dueAt: localDue ? new Date(localDue).toISOString() : '', week: String(form.get('week') || week), linkedRecords: splitList(String(form.get('linked_records') || '')), priority: String(form.get('priority') || 'normal') });
  }

  function submitPacket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    packetMutation.mutate({ packetId: recordId('DELIVERY-PACKET-'), packetType: String(form.get('packet_type') || 'coach_packet'), week: String(form.get('week') || week), linkedRecords: splitList(String(form.get('linked_records') || '')) });
  }

  return (
    <WorkspacePage definition={DELIVERY_WORKSPACE}>
      <WorkbenchFrame actions={<div className="workbench-toolbar__group"><button className="button button--secondary" disabled={!canAuthor} onClick={() => setTab('packet')} type="button"><FileCheck2 size={15} /> Assemble packet</button><button className="button button--primary" disabled={!canAuthor} onClick={() => setTab('task')} type="button"><Plus size={15} /> Add responsibility</button></div>} description="Coordinate the game-week handoff across film, scouting, install, practice, approvals, exports, and accountable staff owners." eyebrow="Weekly delivery operations" icon={CalendarDays} title="Game-week delivery center">
        <WorkbenchTabs activeTab={tab} label="Delivery center views" onChange={(next) => setTab(next as DeliveryTab)} tabs={[{ id: 'agenda', label: 'Agenda', count: data?.counts.tasks }, { id: 'packets', label: 'Packet checklist', count: data?.counts.packets }, { id: 'task', label: 'New responsibility' }, { id: 'packet', label: 'Assemble packet' }]} />
        <WorkbenchState connected={Boolean(session)} error={dataQuery.error} loading={dataQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[{ label: 'Open tasks', value: data?.counts.tasks ?? 0, hint: 'week responsibilities' }, { label: 'Overdue', value: data?.counts.overdue ?? 0, hint: 'needs ownership now' }, { label: 'Completed', value: data?.counts.completed ?? 0, hint: 'audited handoffs' }, { label: 'Locked releases', value: data?.counts.locked_releases ?? 0, hint: 'ready snapshots' }]} />
            <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> {data?.boundary || 'Delivery schedules work; owning systems retain content, approval, and external notification authority.'}</div>
            {tab === 'agenda' ? <>
              <div className="workbench-toolbar"><WorkbenchSearch label="Search game-week tasks" onChange={setSearch} placeholder="Search owner, category, linked artifact…" value={search} /><label className="filter-select"><span className="sr-only">Week</span><input onChange={(event) => setWeek(event.target.value)} value={week} /></label></div>
              <div className="workbench-split"><div className="workbench-pane workbench-pane--soft"><div className="workbench-pane__header"><div><h3>Week {week}</h3><p>Sorted by due time and priority. Overdue work stays visible.</p></div></div><RecordList emptyMessage="No delivery tasks are scheduled for this week." onSelect={(task) => setSelectedId(task.id)} records={tasks} selectedId={selected?.id} subtitle={(task) => `${dueLabel(task)} · ${sentenceCase(task.category)} · ${task.owner || 'Unassigned'}`} title={(task) => task.title} /></div><div className="workbench-pane">{selected ? <RecordInspector eyebrow="Delivery responsibility" facts={[{ label: 'Due', value: dueLabel(selected) }, { label: 'Owner', value: compactValue(selected.owner) }, { label: 'Priority', value: sentenceCase(String(selected.priority || 'normal')) }, { label: 'State', value: sentenceCase(String(selected.computed_state || selected.status)) }, { label: 'Linked records', value: compactValue(selected.linked_records) }]} note="Completion records the handoff. It does not alter the linked plan, play, export, or approval state." status={selected.computed_state || selected.status} title={selected.title}><div className="workbench-toolbar__group">{selected.status !== 'completed' && selected.status !== 'complete' ? <button className="button button--primary" disabled={completeMutation.isPending} onClick={() => completeMutation.mutate(selected.id)} type="button"><CheckCircle2 size={14} /> Mark complete</button> : <span className="mutation-notice mutation-notice--success"><BadgeCheck size={14} /> Handoff completed</span>}</div><MutationNotice error={completeMutation.error} pending={completeMutation.isPending} success={completeMutation.isSuccess} successMessage="Delivery responsibility completed and audited." /></RecordInspector> : <div className="record-list__empty">Select a responsibility to inspect its handoff context.</div>}</div></div>
            </> : null}
            {tab === 'packets' ? <div className="workbench-split"><div className="workbench-pane workbench-pane--soft"><div className="workbench-pane__header"><div><h3>Delivery packet outputs</h3><p>Human-controlled outputs expected for this game week.</p></div></div><ul className="evidence-stack">{(data?.delivery_packet_outputs ?? []).map((output) => <li key={output}><strong>{sentenceCase(output)}</strong><span>Reference output · verify its owning release, export, and approval state before handoff.</span></li>)}</ul></div><div className="workbench-pane"><RecordInspector eyebrow="Packet readiness" facts={[{ label: 'Weekly packages', value: data?.packets.length ?? 0 }, { label: 'Practice plans', value: data?.practice_plans.length ?? 0 }, { label: 'Release snapshots', value: data?.release_snapshots.length ?? 0 }, { label: 'Locked releases', value: data?.counts.locked_releases ?? 0 }]} note="Packet generation and exports remain separate governed actions. This center tells staff what must be ready and who owns the handoff." status={data?.human_review_required ? 'review_required' : 'ready'} title="Game-week handoff checklist"><div className="delivery-packet-grid">{(data?.packet_readiness ?? []).map((packet) => <article className="delivery-packet-card" key={packet.id}><div className="delivery-packet-card__header"><h4>{packet.label}</h4><span className={`delivery-packet-status delivery-packet-status--${packet.status}`}>{sentenceCase(packet.status)}</span></div><p>Audience: {packet.audience}</p><p className="delivery-packet-card__links">Linked: {packet.linked_records.length ? packet.linked_records.join(', ') : 'None yet'}</p>{packet.blockers.length ? <details open><summary>{packet.blockers.length} blocker{packet.blockers.length === 1 ? '' : 's'}</summary><ul>{packet.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul></details> : <p>Prerequisites present; staff assembly and approval remain required.</p>}</article>)}</div></RecordInspector></div></div> : null}
            {tab === 'task' ? canAuthor ? <form className="workbench-form workbench-pane" onSubmit={submitTask}><div className="workbench-pane__header"><div><h3><Plus aria-hidden="true" size={16} /> Add game-week responsibility</h3><p>Put one owner, deadline, category, priority, and linked artifact on the calendar.</p></div></div><div className="workbench-form__grid"><label><span>Title</span><input name="title" placeholder="Finalize player install packet" required /></label><label><span>Category</span><select defaultValue="install" name="category"><option>meeting</option><option>film</option><option>scouting</option><option>install</option><option>practice</option><option>approval</option><option>export</option><option>delivery</option></select></label><label><span>Owner</span><input name="owner" placeholder="COACH-OC" required /></label><label><span>Due</span><input name="due_at" required type="datetime-local" /></label><label><span>Week</span><input defaultValue={week} name="week" required /></label><label><span>Priority</span><select defaultValue="normal" name="priority"><option>critical</option><option>high</option><option>normal</option><option>low</option></select></label><label className="is-wide"><span>Linked records <small>comma separated</small></span><input name="linked_records" placeholder="GAMEPLAN-…, RELEASE-SNAPSHOT-…, PRACTICE-…" /></label><LinkedRecordPicker onChange={setLinkedRecordIds} options={linkedRecordOptions} value={linkedRecordIds} /></div><div className="workbench-form__actions"><p className="workbench-form__hint">The task is saved to the organization calendar and appears in the Operations Inbox when due or assigned.</p><button className="button button--primary" disabled={createMutation.isPending} type="submit"><Plus size={15} /> Schedule responsibility</button></div><MutationNotice error={createMutation.error} pending={createMutation.isPending} success={createMutation.isSuccess} successMessage="Game-week responsibility scheduled." /></form> : <p className="approval-boundary">Scheduling responsibilities requires coaching, analyst, or program-owner authority.</p> : null}
            {tab === 'packet' ? canAuthor ? <form className="workbench-form workbench-pane" onSubmit={submitPacket}><div className="workbench-pane__header"><div><h3><FileCheck2 aria-hidden="true" size={16} /> Assemble delivery packet</h3><p>Create a reviewable packet record from the readiness matrix; this does not publish or notify externally.</p></div></div><div className="workbench-form__grid"><label><span>Audience packet</span><select defaultValue="coach_packet" name="packet_type"><option value="coach_packet">Coach packet</option><option value="player_install_packet">Player install packet</option><option value="coordinator_call_sheet">Coordinator call sheet</option><option value="wristband_layout">Wristband layout</option><option value="administrator_audit_packet">Administrator audit packet</option></select></label><label><span>Week</span><input defaultValue={week} name="week" required /></label><label className="is-wide"><span>Additional linked records <small>comma separated</small></span><input name="linked_records" placeholder="PLAY-…, PRACTICE-…, RELEASE-SNAPSHOT-…" /></label><LinkedRecordPicker onChange={setLinkedRecordIds} options={linkedRecordOptions} value={linkedRecordIds} /></div><div className="workbench-form__actions"><p className="workbench-form__hint">The packet captures canonical references and readiness blockers for staff review.</p><button className="button button--primary" disabled={packetMutation.isPending} type="submit"><FileCheck2 size={15} /> Assemble packet record</button></div><MutationNotice error={packetMutation.error} pending={packetMutation.isPending} success={packetMutation.isSuccess} successMessage="Delivery packet assembled for review." /></form> : <p className="approval-boundary">Packet assembly requires coaching, analyst, or program-owner authority.</p> : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
