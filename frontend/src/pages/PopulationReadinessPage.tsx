import { ArrowLeft, ClipboardCheck, LockKeyhole, ShieldAlert } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import { DescriptionBox } from '../components/DescriptionBox';
import { PageHeader } from '../components/PageHeader';
import { StatusPill, statusTone } from '../components/StatusPill';
import { WorkbenchFrame, WorkbenchState, WorkbenchStats } from '../components/OperationalWorkbench';
import { useOrganizationPopulationReadinessQuery } from '../hooks/useOperationalData';
import { compactValue, sentenceCase } from '../lib/format';

export function PopulationReadinessPage() {
  const { session } = useSession();
  const [season, setSeason] = useState('2026');
  const query = useOrganizationPopulationReadinessQuery(season);
  const data = query.data;
  const readyPercent = data?.required_component_count ? Math.round((data.ready_component_count / data.required_component_count) * 100) : 0;

  return (
    <div className="page-stack">
      <PageHeader
        actions={<Link className="button button--secondary" to="/app/admin"><ArrowLeft size={15} /> Back to Admin</Link>}
        description="Inspect the organization-specific operating bundle required to make football systems useful with real terminology, doctrine, roster, media, scouting, analytics, and game-plan data. This page reports readiness only; it never fabricates missing packages or activates the organization."
        eyebrow="Organization population"
        title="Organization population readiness"
      />
      <DescriptionBox
        audience="Program owners, coordinators, analysts, and implementation reviewers"
        description="Each required component is checked against organization scope, season, and the status needed before bundle composition. Missing or invalid components remain explicit blockers."
        howItWorks="Choose a season, inspect the component matrix, then resolve the owning package in its authoritative workflow. The readiness endpoint is read-only and organization-scoped."
        icon={ClipboardCheck}
        outcome="A transparent readiness matrix with accountable blockers and no automatic activation"
        title="Population readiness system"
        tone="green"
      />
      <WorkbenchFrame
        actions={<span className="status-pill status-pill--warning"><LockKeyhole size={13} /> Activation disabled</span>}
        description="The matrix makes the real-data prerequisite visible before staff depend on downstream workflows."
        eyebrow="Operating bundle control"
        icon={ClipboardCheck}
        title="Readiness matrix"
      >
        <WorkbenchState connected={Boolean(session)} error={query.error} loading={query.isLoading}>
          <div className="workbench-body">
            <div className="workbench-toolbar">
              <label className="workbench-search"><span>Season</span><input aria-label="Season" inputMode="numeric" onChange={(event) => setSeason(event.target.value || '2026')} pattern="[0-9]{4}" value={season} /></label>
              <span className="workbench-form__hint">Organization: {data?.organization_id || session?.organizationId || 'not connected'}</span>
            </div>
            <WorkbenchStats stats={[
              { label: 'Readiness', value: `${readyPercent}%`, hint: data?.status ? sentenceCase(data.status) : 'not evaluated' },
              { label: 'Components ready', value: `${data?.ready_component_count ?? 0}/${data?.required_component_count ?? 0}`, hint: 'required package count' },
              { label: 'Blockers', value: data?.blockers.length ?? 0, hint: 'must be resolved by owners' },
              { label: 'External state', value: data?.external_state_changed ? 'Changed' : 'Unchanged', hint: 'read-only inspection' },
            ]} />
            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                <div className="workbench-pane__header"><div><h3>Required operating components</h3><p>Scope, season, and state checks are shown per package.</p></div></div>
                <div className="evidence-stack" role="list" aria-label="Organization population components">
                  {(data?.components ?? []).map((component) => (
                    <article key={component.component} role="listitem">
                      <div><strong>{sentenceCase(component.component)}</strong><span>{component.record_id || 'No record'} · requires {sentenceCase(component.required_status)}</span></div>
                      <StatusPill label={component.ready ? 'ready' : 'blocked'} tone={statusTone(component.ready ? 'ready' : 'blocked')} />
                    </article>
                  ))}
                </div>
              </div>
              <div className="workbench-pane">
                <div className="workbench-pane__header"><div><h3>Explicit blockers</h3><p>Nothing is silently marked complete.</p></div></div>
                {data?.blockers.length ? <ul className="evidence-stack">{data.blockers.map((blocker, index) => <li key={`${blocker.code}-${index}`}><strong>{compactValue(blocker.code)}</strong><span>{compactValue(blocker.message)} · component: {compactValue(blocker.component)}</span></li>)}</ul> : <p className="approval-boundary">All package checks passed for this season; owner review is still required before any bundle action.</p>}
                <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> This report is read-only. It does not create packages, change permissions, advance stages, call providers, or enable production.</div>
              </div>
            </div>
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </div>
  );
}
