import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileCheck2, LockKeyhole, ShieldAlert } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import {
  MutationNotice,
  RecordInspector,
  RecordList,
  WorkbenchFrame,
  WorkbenchState,
  WorkbenchStats,
} from '../components/OperationalWorkbench';
import { DescriptionBox } from '../components/DescriptionBox';
import { PageHeader } from '../components/PageHeader';
import { useStage25AcceptanceQuery } from '../hooks/useOperationalData';
import { submitStage25Acceptance } from '../lib/api';
import { compactValue, recordId, recordLabel, splitList } from '../lib/format';

export function Stage25AcceptancePage() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const query = useStage25AcceptanceQuery();
  const [selectedId, setSelectedId] = useState('');
  const data = query.data;
  const selectedAcceptance = data?.acceptances.find((record) => record.id === selectedId) ?? data?.acceptances[0];
  const isOwner = session?.role === 'program_owner';
  const acceptanceMutation = useMutation({
    mutationFn: (values: Parameters<typeof submitStage25Acceptance>[1]) => submitStage25Acceptance(session!, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['stage25-acceptance', session?.organizationId] }),
  });

  function submitAcceptance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    acceptanceMutation.mutate({
      acceptanceId: String(form.get('acceptance_id') || recordId('ACCEPTANCE-STAGE25-')),
      rationale: String(form.get('rationale') || ''),
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
      acceptedAt: new Date().toISOString(),
    });
  }

  const spec = data?.spec;
  const validation = spec?.validation;
  const validationStatus = compactValue(typeof validation === 'object' && validation ? (validation as Record<string, unknown>).status : undefined);

  return (
    <div className="page-stack">
      <PageHeader
        actions={<Link className="button button--secondary" to="/app/admin"><ArrowLeft size={15} /> Back to Admin</Link>}
        description="Review the compiled Master Codex specification and record explicit owner acceptance evidence. This workspace documents readiness; it cannot activate production or advance the project stage."
        eyebrow="Stage 25 governance"
        title="Stage 25 specification acceptance"
      />

      <DescriptionBox
        audience="Program owners and authorized governance reviewers"
        description="The acceptance surface binds the compiled specification to a human decision, rationale, and evidence references so the final build target is inspectable and auditable."
        howItWorks="Inspect the generated specification, review its validation state, then submit one explicit acceptance record. Every request remains organization-scoped and non-activating."
        icon={FileCheck2}
        outcome="A persisted acceptance record that can be reviewed by the control plane"
        title="Specification acceptance system"
        tone="violet"
      />

      <WorkbenchFrame
        actions={<span className="status-pill status-pill--warning"><LockKeyhole size={13} /> Production disabled</span>}
        description="The final specification and owner evidence are shown together so implementation readiness can be reviewed without granting deployment authority."
        eyebrow="Human-controlled release boundary"
        icon={FileCheck2}
        title="Compiled specification review"
      >
        <WorkbenchState connected={Boolean(session)} error={query.error} loading={query.isLoading}>
          <div className="workbench-body">
            <WorkbenchStats stats={[
              { label: 'Spec version', value: compactValue(spec?.version), hint: 'compiled target' },
              { label: 'Validation', value: validationStatus, hint: 'schema and requirement checks' },
              { label: 'Acceptance records', value: data?.acceptances.length ?? 0, hint: 'owner evidence' },
              { label: 'Production implementation', value: data?.production_implementation_allowed ? 'Allowed' : 'Not allowed', hint: 'explicit safety boundary' },
            ]} />

            <div className="workbench-split">
              <div className="workbench-pane workbench-pane--soft">
                {spec ? <RecordInspector
                  eyebrow="Authoritative build target"
                  facts={[
                    { label: 'Specification ID', value: compactValue(spec.spec_id || spec.id) },
                    { label: 'Version', value: compactValue(spec.version) },
                    { label: 'Validation status', value: validationStatus },
                    { label: 'Validation issues', value: compactValue(typeof validation === 'object' && validation ? (validation as Record<string, unknown>).errors : undefined) },
                  ]}
                  note="The compiled specification is evidence for review. It is not a deployment command, and acceptance does not bypass Stage 0, pilot, security, or infrastructure gates."
                  status={validationStatus}
                  title={recordLabel(spec)}
                /> : <p className="workbench-form__hint">No compiled specification is available for this organization.</p>}
                <div className="workbench-pane__header"><div><h3>Acceptance history</h3><p>Prior decisions remain inspectable and immutable through the API record trail.</p></div></div>
                <RecordList
                  emptyMessage="No Stage 25 acceptance evidence has been recorded."
                  onSelect={(record) => setSelectedId(record.id)}
                  records={data?.acceptances ?? []}
                  selectedId={selectedAcceptance?.id}
                  subtitle={(record) => `${compactValue(record.accepted_at)} · ${compactValue(record.evidence_refs)}`}
                  title={recordLabel}
                />
              </div>
              <div className="workbench-pane">
                {selectedAcceptance ? <RecordInspector
                  eyebrow="Owner evidence record"
                  facts={[
                    { label: 'Acceptance ID', value: selectedAcceptance.id },
                    { label: 'Decision', value: compactValue(selectedAcceptance.decision || selectedAcceptance.status) },
                    { label: 'Accepted at', value: compactValue(selectedAcceptance.accepted_at) },
                    { label: 'Evidence', value: compactValue(selectedAcceptance.evidence_refs) },
                    { label: 'Rationale', value: compactValue(selectedAcceptance.rationale) },
                  ]}
                  note="This record proves that an owner reviewed the specification. It does not authorize production implementation or automatic stage advancement."
                  status={String(selectedAcceptance.status || selectedAcceptance.decision || 'recorded')}
                  title={recordLabel(selectedAcceptance)}
                /> : <RecordInspector
                  eyebrow="Acceptance evidence"
                  facts={[
                    { label: 'Current role', value: compactValue(session?.role) },
                    { label: 'Stage advance', value: data?.stage_advance_authorized ? 'Authorized' : 'Not authorized' },
                    { label: 'Production', value: data?.production_implementation_allowed ? 'Allowed' : 'Not allowed' },
                    { label: 'Review state', value: 'Awaiting explicit owner evidence' },
                  ]}
                  note="Review the compiled specification and supporting evidence before submitting."
                  status="review required"
                  title="No acceptance selected"
                />}
              </div>
            </div>

            {isOwner ? <form className="workbench-form workbench-pane" onSubmit={submitAcceptance}>
              <div className="workbench-pane__header"><div><h3><FileCheck2 aria-hidden="true" size={16} /> Record owner acceptance</h3><p>Submit a durable human decision linked to the compiled specification and its evidence.</p></div></div>
              <div className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> Acceptance records evidence only. Production implementation and stage advancement remain disabled.</div>
              <div className="workbench-form__grid">
                <label><span>Acceptance ID</span><input defaultValue={recordId('ACCEPTANCE-STAGE25-')} name="acceptance_id" pattern="ACCEPTANCE-STAGE25-.*" required /></label>
                <label><span>Specification version</span><input defaultValue={String(spec?.version || '')} name="spec_version" readOnly /></label>
                <label className="is-wide"><span>Owner rationale</span><textarea name="rationale" placeholder="Explain what was reviewed and why the compiled specification is accepted." required /></label>
                <label className="is-wide"><span>Evidence references <small>comma separated</small></span><input name="evidence_refs" placeholder="control/master-codex-build-spec.json, TEST-001" required /></label>
              </div>
              <div className="workbench-form__actions"><p className="workbench-form__hint">Acceptance timestamp is generated by the authenticated client at submission.</p><button className="button button--primary" disabled={acceptanceMutation.isPending || !session} type="submit"><FileCheck2 size={15} /> Record acceptance evidence</button></div>
              <MutationNotice error={acceptanceMutation.error} pending={acceptanceMutation.isPending} success={acceptanceMutation.isSuccess} successMessage="Stage 25 acceptance evidence recorded without activation." />
            </form> : <p className="approval-boundary"><ShieldAlert aria-hidden="true" size={17} /> Only the program owner may record Stage 25 acceptance evidence.</p>}
          </div>
        </WorkbenchState>
      </WorkbenchFrame>
    </div>
  );
}
