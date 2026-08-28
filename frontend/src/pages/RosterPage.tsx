import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BadgeCheck, GitBranch, Plus, ShieldCheck, UsersRound } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';

import { useSession } from '../auth/SessionContext';
import { MutationNotice, RecordInspector, RecordList, WorkbenchFrame, WorkbenchSearch, WorkbenchState, WorkbenchStats, WorkbenchTabs } from '../components/OperationalWorkbench';
import { useRosterWorkspaceQuery } from '../hooks/useOperationalData';
import { createRosterPlayer, saveDepthChart, savePersonnelPackage } from '../lib/api';
import { compactValue, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { DepthChart, PersonnelPackage, RosterPlayer } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { ROSTER_WORKSPACE } from './workspaceDefinitions';

type RosterTab = 'players' | 'depth' | 'packages';

export function RosterPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<RosterTab>('players');
  const [search, setSearch] = useState('');
  const [positionGroup, setPositionGroup] = useState('all');
  const [status, setStatus] = useState('all');
  const [selectedId, setSelectedId] = useState('');
  const [depthPlayerIds, setDepthPlayerIds] = useState<string[]>([]);
  const [packagePlayerIds, setPackagePlayerIds] = useState<string[]>([]);
  const rosterQuery = useRosterWorkspaceQuery({ ...(positionGroup === 'all' ? {} : { position_group: positionGroup }), ...(status === 'all' ? {} : { status }) });
  const data = rosterQuery.data;
  const canAuthor = Boolean(session && ['program_owner', 'coach_staff'].includes(session.role));
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['roster-workspace', session?.organizationId] });
  const playerMutation = useMutation({ mutationFn: (player: RosterPlayer) => createRosterPlayer(session!, player), onSuccess: refresh });
  const depthMutation = useMutation({ mutationFn: (chart: DepthChart) => saveDepthChart(session!, chart), onSuccess: refresh });
  const packageMutation = useMutation({ mutationFn: (record: PersonnelPackage) => savePersonnelPackage(session!, record), onSuccess: refresh });
  const records = useMemo(() => {
    const source = tab === 'players' ? data?.players ?? [] : tab === 'depth' ? data?.depth_charts ?? [] : data?.personnel_packages ?? [];
    const needle = search.trim().toLowerCase();
    return needle ? source.filter((record) => compactValue(record).toLowerCase().includes(needle)) : source;
  }, [data, search, tab]);
  const selected = records.find((record) => record.id === selectedId) ?? records[0];

  function submitPlayer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    playerMutation.mutate({ id: recordId('PLAYER-'), display_name: String(form.get('display_name') || ''), position: String(form.get('position') || ''), position_group: String(form.get('position_group') || ''), jersey_number: String(form.get('jersey_number') || ''), aliases: splitList(String(form.get('aliases') || '')), eligibility: splitList(String(form.get('eligibility') || '')), role_groups: splitList(String(form.get('role_groups') || '')), availability: String(form.get('availability') || 'available'), status: String(form.get('status') || 'active'), owner: session?.subject, source_refs: splitList(String(form.get('source_refs') || '')) });
  }

  function submitDepthChart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const playerIds = splitList(String(form.get('player_ids') || ''));
    depthMutation.mutate({ id: recordId('DEPTH-'), unit: String(form.get('unit') || ''), position: String(form.get('position') || ''), season: String(form.get('season') || '2026'), week: String(form.get('week') || ''), slots: playerIds.map((playerId, index) => ({ rank: index + 1, player_id: playerId, role: index === 0 ? 'starter' : 'reserve' })), status: 'ready' });
  }

  function submitPackage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    packageMutation.mutate({ id: recordId('PERSONNEL-'), name: String(form.get('name') || ''), unit: String(form.get('unit') || ''), roles: splitList(String(form.get('roles') || '')), player_ids: splitList(String(form.get('player_ids') || '')), season: String(form.get('season') || '2026'), status: 'ready' });
  }

  return (
    <WorkspacePage definition={ROSTER_WORKSPACE}>
      <WorkbenchFrame description="Inspect canonical players, compose accountable depth charts, and build reusable personnel packages that downstream football systems can reference." eyebrow="People and personnel" icon={UsersRound} title="Roster and personnel workbench">
        <WorkbenchTabs activeTab={tab} label="Roster workspace views" onChange={(next) => { setTab(next as RosterTab); setSelectedId(''); }} tabs={[{ id: 'players', label: 'Player registry', count: data?.counts.players }, { id: 'depth', label: 'Depth charts', count: data?.counts.depth_charts }, { id: 'packages', label: 'Personnel packages', count: data?.counts.personnel_packages }]} />
        <WorkbenchState connected={Boolean(session)} error={rosterQuery.error} loading={rosterQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[{ label: 'Players', value: data?.counts.players ?? 0, hint: 'visible roster records' }, { label: 'Active', value: data?.counts.active ?? 0, hint: 'explicitly active' }, { label: 'Depth charts', value: data?.counts.depth_charts ?? 0, hint: 'unit/position artifacts' }, { label: 'Packages', value: data?.counts.personnel_packages ?? 0, hint: 'reusable personnel' }]} />
            <div className="approval-boundary"><ShieldCheck aria-hidden="true" size={17} /> {data?.privacy_boundary}</div>
            <div className="workbench-toolbar"><WorkbenchSearch label="Search roster" onChange={setSearch} placeholder="Search name, alias, position, role…" value={search} /><div className="workbench-toolbar__group"><label className="filter-select"><span className="sr-only">Filter by position group</span><select onChange={(event) => setPositionGroup(event.target.value)} value={positionGroup}><option value="all">All position groups</option>{data?.position_groups.map((group) => <option key={group} value={group}>{group}</option>)}</select></label><label className="filter-select"><span className="sr-only">Filter by status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="injured">Injured</option><option value="practice_squad">Practice squad</option><option value="reserve">Reserve</option></select></label></div></div>
            <div className="workbench-split"><div className="workbench-pane workbench-pane--soft"><div className="workbench-pane__header"><div><h3>{sentenceCase(tab)}</h3><p>{records.length} records match the current view.</p></div></div><RecordList emptyMessage="No roster records match these filters." onSelect={(record) => setSelectedId(record.id)} records={records} selectedId={selected?.id} subtitle={(record) => tab === 'players' ? `${record.position} · ${record.position_group}` : record.id} title={recordLabel} /></div><div className="workbench-pane">{selected ? <RecordInspector eyebrow={sentenceCase(tab)} facts={tab === 'players' ? [{ label: 'Player ID', value: selected.id }, { label: 'Position', value: compactValue((selected as RosterPlayer).position) }, { label: 'Position group', value: compactValue((selected as RosterPlayer).position_group) }, { label: 'Availability', value: compactValue((selected as RosterPlayer).availability) }, { label: 'Role groups', value: compactValue((selected as RosterPlayer).role_groups) }] : tab === 'depth' ? [{ label: 'Unit / position', value: `${(selected as DepthChart).unit} · ${(selected as DepthChart).position}` }, { label: 'Season / week', value: `${(selected as DepthChart).season} · ${(selected as DepthChart).week || 'full season'}` }, { label: 'Slots', value: (selected as DepthChart).slots.map((slot) => `${slot.rank}. ${slot.player_id}`).join(' · ') }] : [{ label: 'Unit', value: (selected as PersonnelPackage).unit }, { label: 'Roles', value: compactValue((selected as PersonnelPackage).roles) }, { label: 'Players', value: compactValue((selected as PersonnelPackage).player_ids) }]} note={tab === 'players' ? 'Identity and availability are explicit organization records. Downstream systems should reference this player ID rather than duplicate a name.' : 'This artifact is reusable context; changes remain auditable and require the owning workflow authority.'} status={selected.status} title={recordLabel(selected)} /> : <div className="record-list__empty">Choose a roster record to inspect it here.</div>}</div></div>
            {canAuthor && tab === 'players' ? <form className="workbench-form workbench-pane" onSubmit={submitPlayer}><div className="workbench-pane__header"><div><h3><Plus aria-hidden="true" size={16} /> Add roster player</h3><p>Create a stable identity record before using the player in downstream systems.</p></div></div><div className="workbench-form__grid"><label><span>Display name</span><input name="display_name" placeholder="Jordan Example" required /></label><label><span>Position</span><input name="position" placeholder="WR" required /></label><label><span>Position group</span><input name="position_group" placeholder="wide receivers" required /></label><label><span>Jersey number</span><input name="jersey_number" placeholder="11" /></label><label><span>Status</span><select defaultValue="active" name="status"><option>active</option><option>inactive</option><option>injured</option><option>practice_squad</option><option>reserve</option></select></label><label><span>Availability</span><input defaultValue="available" name="availability" required /></label><label><span>Role groups</span><input defaultValue="X, field" name="role_groups" /></label><label><span>Aliases</span><input name="aliases" placeholder="J. Example" /></label><label className="is-wide"><span>Eligibility and source references</span><input defaultValue="eligible, ROSTER-SOURCE-001" name="source_refs" required /></label></div><div className="workbench-form__actions"><span className="workbench-form__hint">Owner: {session?.subject || 'current staff member'}</span><button className="button button--primary" disabled={playerMutation.isPending} type="submit"><Plus size={15} /> Save player</button></div><MutationNotice error={playerMutation.error} pending={playerMutation.isPending} success={playerMutation.isSuccess} successMessage="Roster player saved." /></form> : null}
            {canAuthor && tab === 'depth' ? <form className="workbench-form workbench-pane" onSubmit={submitDepthChart}><div className="workbench-pane__header"><div><h3><GitBranch aria-hidden="true" size={16} /> Build depth chart</h3><p>Reference canonical player IDs in starter-to-reserve order.</p></div></div><div className="workbench-form__grid"><label><span>Unit</span><select defaultValue="offense" name="unit"><option>offense</option><option>defense</option><option>special_teams</option></select></label><label><span>Position</span><input name="position" placeholder="WR" required /></label><label><span>Season</span><input defaultValue="2026" name="season" required /></label><label><span>Week</span><input name="week" placeholder="WEEK-1" /></label><label className="is-wide"><span>Player IDs, starter first</span><input name="player_ids" placeholder="PLAYER-..., PLAYER-..." required /></label><label className="is-wide"><span>Choose from roster <small>Ctrl/Cmd-click preserves starter-to-reserve order</small></span><select className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); setDepthPlayerIds(ids); const input = event.currentTarget.form?.elements.namedItem('player_ids') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, data?.players.length ?? 4))} value={depthPlayerIds}>{(data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name} - {player.position} - {player.availability || 'availability unknown'}</option>)}</select></label></div><div className="workbench-form__actions"><span className="workbench-form__hint">Unknown or duplicate player IDs are rejected by the API; manual IDs remain available for approved imports.</span><button className="button button--primary" disabled={depthMutation.isPending} type="submit"><GitBranch size={15} /> Save depth chart</button></div><MutationNotice error={depthMutation.error} pending={depthMutation.isPending} success={depthMutation.isSuccess} successMessage="Depth chart saved." /></form> : null}
            {canAuthor && tab === 'packages' ? <form className="workbench-form workbench-pane" onSubmit={submitPackage}><div className="workbench-pane__header"><div><h3><BadgeCheck aria-hidden="true" size={16} /> Build personnel package</h3><p>Create reusable role context for play design, practice, scouting, and game plan.</p></div></div><div className="workbench-form__grid"><label><span>Name</span><input name="name" placeholder="11 personnel core" required /></label><label><span>Unit</span><select defaultValue="offense" name="unit"><option>offense</option><option>defense</option><option>special_teams</option></select></label><label><span>Roles</span><input name="roles" placeholder="QB, RB, WR, TE, OL" required /></label><label><span>Season</span><input defaultValue="2026" name="season" required /></label><label className="is-wide"><span>Player IDs</span><input name="player_ids" placeholder="PLAYER-..., PLAYER-..." required /></label><label className="is-wide"><span>Choose personnel from roster <small>catalog-backed package membership</small></span><select className="practice-multi-select" multiple onChange={(event) => { const ids = Array.from(event.target.selectedOptions).map((option) => option.value); setPackagePlayerIds(ids); const input = event.currentTarget.form?.elements.namedItem('player_ids') as HTMLInputElement | null; if (input) input.value = ids.join(', '); }} size={Math.min(8, Math.max(4, data?.players.length ?? 4))} value={packagePlayerIds}>{(data?.players ?? []).map((player) => <option key={player.id} value={player.id}>{player.display_name} - {player.position} - {player.role_groups?.join('/') || 'role not set'}</option>)}</select></label></div><div className="workbench-form__actions"><span className="workbench-form__hint">Packages preserve IDs and role labels; they do not infer personnel usage.</span><button className="button button--primary" disabled={packageMutation.isPending} type="submit"><BadgeCheck size={15} /> Save package</button></div><MutationNotice error={packageMutation.error} pending={packageMutation.isPending} success={packageMutation.isSuccess} successMessage="Personnel package saved." /></form> : null}
            {!canAuthor ? <p className="approval-boundary">Your role can inspect privacy-scoped roster context. Creating players, depth charts, or personnel packages requires coach or program-owner authority.</p> : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
