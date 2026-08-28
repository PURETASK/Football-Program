import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Building2, DatabaseZap, FileCheck2, RefreshCw, ShieldCheck, TriangleAlert } from 'lucide-react';
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
import { useAdminWorkspaceQuery } from '../hooks/useOperationalData';
import { approveOrganizationContext, createPilotDeliveryPackage, evaluatePilotReadiness, refreshKnowledgeSource, registerKnowledgeSource, selectPilotOrganization, submitStageZeroApproval, submitUsabilityFeedback } from '../lib/api';
import { compactValue, isoDate, recordId, recordLabel, sentenceCase, splitList } from '../lib/format';
import type { FootballRecord } from '../types';
import { WorkspacePage } from './WorkspacePage';
import { ADMIN_WORKSPACE } from './workspaceDefinitions';

type AdminTab = 'organization' | 'sources' | 'stage0' | 'pilot';

function parseJsonObject(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed as Record<string, unknown> : {};
  } catch {
    return {};
  }
}

function parseJsonUsers(value: string): Array<Record<string, unknown>> {
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object' && !Array.isArray(item))) : [];
  } catch {
    return [];
  }
}

export function AdminPage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const adminQuery = useAdminWorkspaceQuery();
  const [tab, setTab] = useState<AdminTab>('organization');
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const data = adminQuery.data;
  const isOwner = session?.role === 'program_owner';
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['admin-workspace', session?.organizationId] });
  const organizationMutation = useMutation({ mutationFn: (decisionRef: string) => approveOrganizationContext(session!, decisionRef), onSuccess: refresh });
  const sourceMutation = useMutation({ mutationFn: (values: Parameters<typeof registerKnowledgeSource>[1]) => registerKnowledgeSource(session!, values), onSuccess: refresh });
  const refreshMutation = useMutation({ mutationFn: (sourceId: string) => refreshKnowledgeSource(session!, sourceId), onSuccess: refresh });
  const stageMutation = useMutation({ mutationFn: (values: Parameters<typeof submitStageZeroApproval>[1]) => submitStageZeroApproval(session!, values), onSuccess: refresh });
  const pilotReadinessMutation = useMutation({ mutationFn: (values: Parameters<typeof evaluatePilotReadiness>[1]) => evaluatePilotReadiness(session!, values), onSuccess: refresh });
  const pilotSelectionMutation = useMutation({ mutationFn: (values: Parameters<typeof selectPilotOrganization>[1]) => selectPilotOrganization(session!, values), onSuccess: refresh });
  const pilotPackageMutation = useMutation({ mutationFn: (values: Parameters<typeof createPilotDeliveryPackage>[1]) => createPilotDeliveryPackage(session!, values), onSuccess: refresh });
  const usabilityMutation = useMutation({ mutationFn: (values: Parameters<typeof submitUsabilityFeedback>[1]) => submitUsabilityFeedback(session!, values), onSuccess: refresh });

  const sources = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (data?.sources ?? []).filter((source) => !needle || compactValue(source).toLowerCase().includes(needle));
  }, [data?.sources, search]);
  const selectedSource = sources.find((source) => source.id === selectedId) ?? sources[0];
  const selectedContext = data?.organization.contexts.find((context) => context.id === selectedId) ?? data?.organization.contexts[0];
  const selectedPilotRecord = [
    ...(data?.pilot.reports ?? []),
    ...(data?.pilotSelections ?? []),
    ...(data?.pilotPackages ?? []),
    ...(data?.usabilityFeedback ?? []),
  ].find((record) => record.id === selectedId);

  function submitOrganizationApproval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    organizationMutation.mutate(String(form.get('decision_ref') || ''));
  }

  function submitSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    sourceMutation.mutate({
      sourceId: recordId('SOURCE-'),
      tier: String(form.get('tier') || ''),
      kind: String(form.get('kind') || ''),
      uri: String(form.get('uri') || ''),
      capturedAt: String(form.get('captured_at') || ''),
      effectivePeriod: String(form.get('effective_period') || ''),
      citationLocation: String(form.get('citation_location') || ''),
      allowedDomains: splitList(String(form.get('allowed_domains') || '')),
    });
  }

  function submitStageApproval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    stageMutation.mutate({
      approvalId: recordId('APPROVAL-STAGE0-'),
      rationale: String(form.get('rationale') || ''),
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
      approvedAt: new Date().toISOString(),
    });
  }

  function submitPilotReadiness(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const ownerApprovalText = String(form.get('owner_approval') || '').trim();
    pilotReadinessMutation.mutate({
      waveId: String(form.get('wave_id') || ''),
      pilotUsers: parseJsonUsers(String(form.get('pilot_users') || '[]')),
      completedCapabilities: splitList(String(form.get('completed_capabilities') || '')),
      acceptanceEvidence: splitList(String(form.get('acceptance_evidence') || '')),
      featureFlags: parseJsonObject(String(form.get('feature_flags') || '{}')),
      rollbackTested: String(form.get('rollback_tested') || 'false') === 'true',
      ownerApproval: ownerApprovalText ? parseJsonObject(ownerApprovalText) : undefined,
    });
  }

  function submitPilotSelection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    pilotSelectionMutation.mutate({
      selectionId: String(form.get('selection_id') || ''),
      waveId: String(form.get('wave_id') || ''),
      pilotUsers: parseJsonUsers(String(form.get('pilot_users') || '[]')),
      decisionRef: String(form.get('decision_ref') || ''),
    });
  }

  function submitPilotPackage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    pilotPackageMutation.mutate({
      packageId: String(form.get('package_id') || ''),
      selectionId: String(form.get('selection_id') || ''),
      readinessReportId: String(form.get('readiness_report_id') || ''),
      rollback: parseJsonObject(String(form.get('rollback') || '{}')),
    });
  }

  function submitUsability(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const duration = Number(form.get('duration_seconds'));
    const satisfaction = Number(form.get('satisfaction_score'));
    usabilityMutation.mutate({
      feedbackId: recordId('UX-FEEDBACK-'),
      sessionId: String(form.get('session_id') || ''),
      screenId: String(form.get('screen_id') || ''),
      taskId: String(form.get('task_id') || ''),
      outcome: String(form.get('outcome') || ''),
      severity: String(form.get('severity') || ''),
      feedbackText: String(form.get('feedback_text') || ''),
      submittedAt: new Date().toISOString(),
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
      accessibilityIssue: String(form.get('accessibility_issue') || 'false') === 'true',
      durationSeconds: Number.isFinite(duration) && duration > 0 ? duration : undefined,
      satisfactionScore: Number.isFinite(satisfaction) && satisfaction > 0 ? satisfaction : undefined,
    });
  }

  const gate = data?.stageZero.gate;
  const gateStatus = String(gate?.status || gate?.gate_status || 'not evaluated');

  return (
    <WorkspacePage definition={ADMIN_WORKSPACE}>
      <WorkbenchFrame
        description="Operate organization identity, terminology, source provenance, Stage 0 evidence, and pilot readiness from one authority-aware governance surface."
        eyebrow="Organization control plane"
        icon={ShieldCheck}
        title="Admin and governance console"
      >
        <WorkbenchTabs
          activeTab={tab}
          label="Admin workspace views"
          onChange={(next) => { setTab(next as AdminTab); setSelectedId(''); }}
          tabs={[
            { id: 'organization', label: 'Organization', count: data?.organization.contexts.length },
            { id: 'sources', label: 'Sources', count: data?.sources.length },
            { id: 'stage0', label: 'Stage 0 gate', count: data?.stageZero.approvals.length },
            { id: 'pilot', label: 'Pilot readiness', count: data?.pilot.reports.length },
          ]}
        />
        <div className="workbench-toolbar">
          <Link className="button button--secondary" to="/app/admin/stage-25"><FileCheck2 size={14} /> Open Stage 25 acceptance page</Link>
          <Link className="button button--secondary" to="/app/admin/population-readiness"><FileCheck2 size={14} /> Open population readiness</Link>
          <span className="workbench-form__hint">Specification acceptance is a separate owner-controlled evidence workflow.</span>
        </div>
        <WorkbenchState connected={Boolean(session)} error={adminQuery.error} loading={adminQuery.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Organization contexts', value: data?.organization.contexts.length ?? 0, hint: 'tenant identity' },
              { label: 'Knowledge sources', value: data?.sources.length ?? 0, hint: 'provenance registry' },
              { label: 'Stage 0 evidence', value: data?.stageZero.approvals.length ?? 0, hint: 'owner records' },
              { label: 'Pilot reports', value: data?.pilot.reports.length ?? 0, hint: 'bounded delivery' },
              { label: 'Pilot packages', value: data?.pilotPackages.length ?? 0, hint: 'reviewable handoffs' },
              { label: 'UX evidence', value: data?.usabilityFeedback.length ?? 0, hint: 'moderated findings' },
            ]} />

            {tab === 'organization' ? (
              <>
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <div className="workbench-pane__header"><div><h3>Organization contexts</h3><p>Team identity, season, people, and terminology authority.</p></div></div>
                    <RecordList emptyMessage="No organization context exists." onSelect={(record) => setSelectedId(record.id)} records={data?.organization.contexts ?? []} selectedId={selectedContext?.id} subtitle={(record) => `${compactValue(record.season)} · ${compactValue(record.team_id)}`} title={recordLabel} />
                  </div>
                  <div className="workbench-pane">
                    {selectedContext ? <RecordInspector eyebrow="Organization authority" facts={[
                      { label: 'Season', value: compactValue(selectedContext.season) },
                      { label: 'Team ID', value: compactValue(selectedContext.team_id || selectedContext.team_context_id || selectedContext.id) },
                      { label: 'People', value: compactValue(selectedContext.people) },
                      { label: 'Terminology', value: compactValue(selectedContext.terminology_version) },
                    ]} note="Approval controls the organization context and terminology package only. It does not authorize production implementation or advance Stage 0." status={selectedContext.status} title={recordLabel(selectedContext)} /> : null}
                  </div>
                </div>
                {isOwner && selectedContext && ['draft', 'under_review', 'needs_review', 'pending_approval'].includes(selectedContext.status || '') ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitOrganizationApproval}>
                    <div className="workbench-pane__header"><div><h3><Building2 aria-hidden="true" size={16} /> Approve organization context</h3><p>Record an explicit owner decision through the canonical onboarding approval endpoint.</p></div></div>
                    <div className="approval-boundary"><TriangleAlert aria-hidden="true" size={17} /> Confirm roster identity, terminology, season, and source package before approving.</div>
                    <div className="workbench-form__grid"><label className="is-wide"><span>Decision reference <small>must begin DEC-</small></span><input name="decision_ref" pattern="DEC-.*" placeholder="DEC-ORG-CONTEXT-…" required /></label></div>
                    <div className="workbench-form__actions"><span /><button className="button button--primary" disabled={organizationMutation.isPending} type="submit"><FileCheck2 size={15} /> Record owner approval</button></div>
                    <MutationNotice error={organizationMutation.error} pending={organizationMutation.isPending} success={organizationMutation.isSuccess} successMessage="Organization context and terminology package approved." />
                  </form>
                ) : null}
              </>
            ) : null}

            {tab === 'sources' ? (
              <>
                <div className="workbench-toolbar"><WorkbenchSearch label="Search knowledge sources" onChange={setSearch} placeholder="Search source, tier, domain…" value={search} /><span className="workbench-form__hint">Registration stores provenance metadata; refresh performs a separately authorized retrieval.</span></div>
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <div className="workbench-pane__header"><div><h3>Source registry</h3><p>Freshness, tier, authorization, and domain boundaries.</p></div></div>
                    <RecordList emptyMessage="No sources match the current search." onSelect={(record) => setSelectedId(record.id)} records={sources} selectedId={selectedSource?.id} subtitle={(record) => `${sentenceCase(String(record.tier || ''))} · ${record.stale ? 'stale' : 'current'}`} title={recordLabel} />
                  </div>
                  <div className="workbench-pane">
                    {selectedSource ? <RecordInspector eyebrow="Knowledge source" facts={[
                      { label: 'Tier', value: sentenceCase(String(selectedSource.tier || '')) },
                      { label: 'Kind', value: sentenceCase(String(selectedSource.kind || '')) },
                      { label: 'URI', value: compactValue(selectedSource.uri || selectedSource.ref) },
                      { label: 'Allowed domains', value: compactValue(selectedSource.allowed_domains) },
                      { label: 'Last refresh', value: compactValue(selectedSource.last_refresh) },
                      { label: 'Freshness', value: selectedSource.stale ? 'Stale' : 'Current' },
                    ]} status={selectedSource.status} title={recordLabel(selectedSource)}><button className="button button--secondary" disabled={!isOwner || refreshMutation.isPending} onClick={() => refreshMutation.mutate(selectedSource.id)} type="button"><RefreshCw size={14} /> Refresh authorized source</button><MutationNotice error={refreshMutation.error} pending={refreshMutation.isPending} success={refreshMutation.isSuccess} successMessage="Source refresh completed and evidence was recorded." /></RecordInspector> : null}
                  </div>
                </div>
                {isOwner ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitSource}>
                    <div className="workbench-pane__header"><div><h3><DatabaseZap aria-hidden="true" size={16} /> Register source connector</h3><p>Register HTTPS metadata and an exact host allowlist; no retrieval occurs during registration.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Tier</span><select defaultValue="tier_1_authoritative" name="tier"><option>tier_1_authoritative</option><option>tier_2_team_locked</option><option>tier_3_primary_observation</option><option>tier_4_analytical_research</option><option>tier_5_secondary_commentary</option></select></label>
                      <label><span>Kind</span><input defaultValue="rule" name="kind" required /></label>
                      <label className="is-wide"><span>HTTPS URI</span><input name="uri" placeholder="https://operations.nfl.com/…" required type="url" /></label>
                      <label><span>Captured date</span><input defaultValue={isoDate()} name="captured_at" required type="date" /></label>
                      <label><span>Effective period</span><input defaultValue="2026 season" name="effective_period" required /></label>
                      <label><span>Citation location</span><input name="citation_location" placeholder="Rule 5, Section 1" required /></label>
                      <label><span>Allowed domains</span><input name="allowed_domains" placeholder="operations.nfl.com" required /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">The connector rejects non-HTTPS URLs and hosts outside the explicit allowlist.</p><button className="button button--primary" disabled={sourceMutation.isPending} type="submit"><DatabaseZap size={15} /> Register metadata</button></div>
                    <MutationNotice error={sourceMutation.error} pending={sourceMutation.isPending} success={sourceMutation.isSuccess} successMessage="Knowledge source registered with provenance controls." />
                  </form>
                ) : null}
              </>
            ) : null}

            {tab === 'stage0' ? (
              <>
                <div className="workbench-split">
                  <div className="workbench-pane workbench-pane--soft">
                    <RecordInspector eyebrow="Exit gate evaluation" facts={[
                      { label: 'Gate', value: compactValue(gate?.gate_id) },
                      { label: 'Registry', value: compactValue(gate?.registry_id) },
                      { label: 'Evidence status', value: gateStatus },
                      { label: 'Recorded approvals', value: data?.stageZero.approvals.length ?? 0 },
                    ]} status={gateStatus} title="Stage 0 exit gate" />
                  </div>
                  <div className="workbench-pane">
                    <RecordInspector eyebrow="Safety boundary" facts={[
                      { label: 'Production implementation', value: data?.stageZero.production_implementation_allowed ? 'Allowed' : 'Not allowed' },
                      { label: 'Automatic stage advance', value: data?.stageZero.stage_advance_authorized ? 'Authorized' : 'Not authorized' },
                      { label: 'Blockers', value: compactValue(gate?.blockers) },
                      { label: 'Issues', value: compactValue(gate?.issues) },
                    ]} note="Stage 0 approval records owner evidence only. It deliberately cannot edit the control manifest, enable production, or automatically advance the project stage." status="controlled" title="Non-activating approval evidence" />
                  </div>
                </div>
                {isOwner && gateStatus === 'ready_for_approval' ? (
                  <form className="workbench-form workbench-pane" onSubmit={submitStageApproval}>
                    <div className="workbench-pane__header"><div><h3><FileCheck2 aria-hidden="true" size={16} /> Record Stage 0 owner evidence</h3><p>This is the explicit owner authorization record requested by the control plan.</p></div></div>
                    <div className="approval-boundary"><TriangleAlert aria-hidden="true" size={17} /> Submit only after personally reviewing the Stage 0 registry, gap audit, constraints, and evidence references.</div>
                    <div className="workbench-form__grid"><label className="is-wide"><span>Owner rationale</span><textarea name="rationale" required /></label><label className="is-wide"><span>Evidence references</span><input name="evidence_refs" placeholder="control/stage-0a-registry.json, control/stage-0-gap-audit.json" required /></label></div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">Timestamp and approval ID are generated at submission.</p><button className="button button--primary" disabled={stageMutation.isPending} type="submit"><FileCheck2 size={15} /> Record owner evidence</button></div>
                    <MutationNotice error={stageMutation.error} pending={stageMutation.isPending} success={stageMutation.isSuccess} successMessage="Stage 0 owner approval evidence recorded without activating production." />
                  </form>
                ) : <p className="approval-boundary"><TriangleAlert aria-hidden="true" size={17} /> {isOwner ? `The gate is ${sentenceCase(gateStatus)}; owner evidence cannot be submitted until it is ready for approval.` : 'Only the program owner may record Stage 0 owner evidence.'}</p>}
              </>
            ) : null}

            {tab === 'pilot' ? (
              <>
              <div className="workbench-split">
                <div className="workbench-pane workbench-pane--soft">
                  <div className="workbench-pane__header"><div><h3>Pilot governance records</h3><p>Readiness, organization selection, delivery packaging, and UX evidence remain inspectable and non-activating.</p></div></div>
                  <h4>Pilot readiness reports</h4>
                  <RecordList emptyMessage="No pilot-readiness evaluation has been recorded." onSelect={(record) => setSelectedId(record.id)} records={data?.pilot.reports ?? []} selectedId={selectedId} subtitle={(record) => compactValue(record.wave_id)} title={recordLabel} />
                  <h4>Approved organization selections</h4>
                  <RecordList emptyMessage="No pilot organization selection has been recorded." onSelect={(record) => setSelectedId(record.id)} records={data?.pilotSelections ?? []} selectedId={selectedId} subtitle={(record) => `${compactValue(record.wave_id)} · ${compactValue(record.decision_ref)}`} title={recordLabel} />
                  <h4>Delivery packages</h4>
                  <RecordList emptyMessage="No pilot delivery package has been recorded." onSelect={(record) => setSelectedId(record.id)} records={data?.pilotPackages ?? []} selectedId={selectedId} subtitle={(record) => `${compactValue(record.selection_id)} · ${compactValue(record.readiness_report_id)}`} title={recordLabel} />
                  <h4>Usability and accessibility evidence</h4>
                  <RecordList emptyMessage="No usability evidence has been recorded." onSelect={(record) => setSelectedId(record.id)} records={data?.usabilityFeedback ?? []} selectedId={selectedId} subtitle={(record) => `${compactValue(record.screen_id)} · ${compactValue(record.outcome)}`} title={recordLabel} />
                </div>
                <div className="workbench-pane">
                  {selectedPilotRecord ? <RecordInspector eyebrow="Pilot governance record" facts={[
                    { label: 'Record type', value: selectedPilotRecord.id.startsWith('UX-') ? 'Usability evidence' : selectedPilotRecord.id.includes('PKG') ? 'Delivery package' : selectedPilotRecord.id.includes('SEL') ? 'Organization selection' : 'Readiness report' },
                    { label: 'Wave', value: compactValue(selectedPilotRecord.wave_id) },
                    { label: 'Status', value: compactValue(selectedPilotRecord.status || selectedPilotRecord.outcome) },
                    { label: 'Decision', value: compactValue(selectedPilotRecord.decision_ref || selectedPilotRecord.readiness_report_id) },
                    { label: 'Evidence', value: compactValue(selectedPilotRecord.evidence_refs || selectedPilotRecord.acceptance_evidence) },
                  ]} note="These records document bounded readiness and human findings. They do not activate production, change permissions, or advance the project stage." status={String(selectedPilotRecord.status || selectedPilotRecord.outcome || 'recorded')} title={recordLabel(selectedPilotRecord)} /> : <RecordInspector eyebrow="Pilot safety envelope" facts={[
                    { label: 'Reports', value: data?.pilot.reports.length ?? 0 },
                    { label: 'Selections', value: data?.pilotSelections.length ?? 0 },
                    { label: 'Packages', value: data?.pilotPackages.length ?? 0 },
                    { label: 'UX evidence', value: data?.usabilityFeedback.length ?? 0 },
                    { label: 'Human review', value: data?.pilot.human_review_required ? 'Required' : 'Not required' },
                    { label: 'Production activation', value: data?.pilot.production_implementation_allowed ? 'Allowed' : 'Not allowed' },
                    { label: 'Current role', value: sentenceCase(session?.role) },
                  ]} note="Pilot evaluation requires real users, acceptance evidence, feature-flag settings, and rollback proof. Those external facts are not fabricated by this console." status="human_review" title="Bounded pilot readiness" />}
                </div>
              </div>
              {isOwner ? (
                <>
                  <form className="workbench-form workbench-pane" onSubmit={submitPilotReadiness}>
                    <div className="workbench-pane__header"><div><h3>Evaluate pilot readiness</h3><p>Run the non-live readiness evaluator with explicit capability, evidence, feature-flag, and rollback inputs.</p></div></div>
                    <div className="approval-boundary"><TriangleAlert aria-hidden="true" size={17} /> This produces evidence only. It cannot start a pilot, enable production, or advance the stage.</div>
                    <div className="workbench-form__grid">
                      <label><span>Wave ID</span><input defaultValue="WAVE-001" name="wave_id" required /></label>
                      <label><span>Rollback tested</span><select defaultValue="true" name="rollback_tested"><option value="true">Yes</option><option value="false">No</option></select></label>
                      <label className="is-wide"><span>Pilot users JSON</span><textarea defaultValue='[{"id":"OWNER","role":"program_owner"},{"id":"COACH","role":"coach_staff"},{"id":"ANALYST","role":"analyst"},{"id":"PLAYER","role":"player"}]' name="pilot_users" required /></label>
                      <label className="is-wide"><span>Completed capabilities <small>comma separated</small></span><input name="completed_capabilities" placeholder="CAP-004, CAP-009" required /></label>
                      <label className="is-wide"><span>Acceptance evidence <small>comma separated</small></span><input name="acceptance_evidence" placeholder="TEST-001, BROWSER-001" required /></label>
                      <label className="is-wide"><span>Feature flags JSON</span><input defaultValue='{"production_recommendations":false}' name="feature_flags" required /></label>
                      <label className="is-wide"><span>Owner approval JSON <small>optional until separately authorized</small></span><textarea name="owner_approval" placeholder='{"approval_id":"APPROVAL-..."}' /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">The result remains non-activating and human-reviewable.</p><button className="button button--primary" disabled={pilotReadinessMutation.isPending} type="submit"><FileCheck2 size={15} /> Evaluate readiness</button></div>
                    <MutationNotice error={pilotReadinessMutation.error} pending={pilotReadinessMutation.isPending} success={pilotReadinessMutation.isSuccess} successMessage="Pilot readiness evidence recorded without activation." />
                  </form>
                  <form className="workbench-form workbench-pane" onSubmit={submitPilotSelection}>
                    <div className="workbench-pane__header"><div><h3>Select approved pilot organization</h3><p>Bind a bounded pilot wave to the approved organization context and terminology package.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Selection ID</span><input defaultValue="PILOT-SEL-001" name="selection_id" required /></label>
                      <label><span>Wave ID</span><input defaultValue="WAVE-001" name="wave_id" required /></label>
                      <label className="is-wide"><span>Pilot users JSON</span><textarea defaultValue='[{"id":"OWNER","role":"program_owner"},{"id":"COACH","role":"coach_staff"},{"id":"ANALYST","role":"analyst"},{"id":"PLAYER","role":"player"}]' name="pilot_users" required /></label>
                      <label className="is-wide"><span>Decision reference</span><input name="decision_ref" pattern="DEC-.*" placeholder="DEC-PILOT-..." required /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">Selection remains non-live and requires approved organization context.</p><button className="button button--primary" disabled={pilotSelectionMutation.isPending} type="submit"><ShieldCheck size={15} /> Select bounded organization</button></div>
                    <MutationNotice error={pilotSelectionMutation.error} pending={pilotSelectionMutation.isPending} success={pilotSelectionMutation.isSuccess} successMessage="Pilot organization selection recorded without activation." />
                  </form>
                  <form className="workbench-form workbench-pane" onSubmit={submitPilotPackage}>
                    <div className="workbench-pane__header"><div><h3>Compose pilot delivery package</h3><p>Combine selection, readiness, and rollback evidence into a reviewable bounded package.</p></div></div>
                    <div className="workbench-form__grid">
                      <label><span>Package ID</span><input defaultValue="PILOT-PKG-001" name="package_id" required /></label>
                      <label><span>Selection ID</span><input defaultValue="PILOT-SEL-001" name="selection_id" required /></label>
                      <label className="is-wide"><span>Readiness report ID</span><input name="readiness_report_id" placeholder="PILOT-READINESS-..." required /></label>
                      <label className="is-wide"><span>Rollback result JSON</span><textarea defaultValue='{"status":"passed","external_state_changed":false,"historical_evidence_preserved":true}' name="rollback" required /></label>
                    </div>
                    <div className="workbench-form__actions"><p className="workbench-form__hint">Package creation cannot activate production or contact an external provider.</p><button className="button button--primary" disabled={pilotPackageMutation.isPending} type="submit"><FileCheck2 size={15} /> Compose delivery package</button></div>
                    <MutationNotice error={pilotPackageMutation.error} pending={pilotPackageMutation.isPending} success={pilotPackageMutation.isSuccess} successMessage="Pilot delivery package composed for review." />
                  </form>
                </>
              ) : null}
              <form className="workbench-form workbench-pane" onSubmit={submitUsability}>
                <div className="workbench-pane__header"><div><h3>Record usability and accessibility evidence</h3><p>Capture moderated or deployment-environment feedback without changing permissions, release flags, or stage state.</p></div></div>
                <div className="workbench-form__grid">
                  <label><span>Session ID</span><input defaultValue="UX-SESSION-REACT-001" name="session_id" required /></label>
                  <label><span>Screen</span><select defaultValue="SCREEN-GOVERNANCE" name="screen_id"><option value="SCREEN-GOVERNANCE">Governance</option><option value="SCREEN-PRACTICE-BUILDER">Practice Builder</option><option value="SCREEN-GAMEPLAN">Game Plan</option><option value="SCREEN-FILM-ROOM">Film Room</option><option value="SCREEN-PLAYER-TODAY">Player Today</option></select></label>
                  <label><span>Task ID</span><input defaultValue="TASK-REACT-GOVERNANCE" name="task_id" required /></label>
                  <label><span>Outcome</span><select defaultValue="completed" name="outcome"><option value="completed">Completed</option><option value="partially_completed">Partially completed</option><option value="blocked">Blocked</option></select></label>
                  <label><span>Severity</span><select defaultValue="note" name="severity"><option>note</option><option>minor</option><option>major</option><option>critical</option></select></label>
                  <label><span>Accessibility issue</span><select defaultValue="false" name="accessibility_issue"><option value="false">No</option><option value="true">Yes</option></select></label>
                  <label><span>Duration seconds <small>optional</small></span><input min="0" name="duration_seconds" type="number" /></label>
                  <label><span>Satisfaction score <small>optional</small></span><input min="1" max="5" name="satisfaction_score" type="number" /></label>
                  <label className="is-wide"><span>Feedback</span><textarea name="feedback_text" placeholder="What worked, what was confusing, or what blocked the task?" required /></label>
                  <label className="is-wide"><span>Evidence references <small>comma separated</small></span><input defaultValue="BROWSER-REACT-LOCAL-001" name="evidence_refs" required /></label>
                </div>
                <div className="workbench-form__actions"><p className="workbench-form__hint">Blocked, accessibility, major, and critical findings remain human-review flags.</p><button className="button button--secondary" disabled={usabilityMutation.isPending || !session} type="submit"><FileCheck2 size={15} /> Record feedback</button></div>
                <MutationNotice error={usabilityMutation.error} pending={usabilityMutation.isPending} success={usabilityMutation.isSuccess} successMessage="Usability evidence recorded for review." />
               </form>
              </>
            ) : null}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </WorkspacePage>
  );
}
