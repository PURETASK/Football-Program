import { ArrowRight, CheckCircle2, Info, type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { useSession } from '../auth/SessionContext';
import { DescriptionBox } from '../components/DescriptionBox';
import { PageHeader } from '../components/PageHeader';
import { StatusPill } from '../components/StatusPill';
import { useOperatorSummaryQuery } from '../hooks/useWorkspaceData';
import type { WorkspaceDefinition, WorkspaceMetric } from './workspaceDefinitions';

function metricValue(metric: WorkspaceMetric, connected: boolean, summary: ReturnType<typeof useOperatorSummaryQuery>['data']): number | string {
  if (!connected) return '—';
  if (metric.label === 'Pending decisions' || metric.label === 'Pending reviews') return summary?.pending_review_count ?? 0;
  if (metric.label === 'Validation findings') return summary?.stale_source_count ?? 0;
  return metric.recordKey ? summary?.record_counts[metric.recordKey] ?? 0 : 0;
}

function FeatureCard({ feature, index }: { feature: WorkspaceDefinition['features'][number]; index: number }) {
  const Icon: LucideIcon = feature.icon;
  return (
    <article className="workspace-feature" id={feature.id}>
      <header className="workspace-feature__header">
        <span className="workspace-feature__number">{String(index + 1).padStart(2, '0')}</span>
        <span className="workspace-feature__icon" aria-hidden="true"><Icon size={20} /></span>
        <div><p>Feature system</p><h2>{feature.title}</h2></div>
        <StatusPill label={feature.status} tone={feature.status.includes('next') ? 'info' : feature.status.includes('gated') || feature.status.includes('required') ? 'warning' : 'good'} />
      </header>
      <p className="workspace-feature__description">{feature.description}</p>
      <div className="workspace-feature__operation">
        <strong>How it operates</strong>
        <p>{feature.howItWorks}</p>
      </div>
      <dl className="workspace-feature__io">
        <div><dt>Uses</dt><dd>{feature.input}</dd></div>
        <ArrowRight aria-hidden="true" size={17} />
        <div><dt>Produces</dt><dd>{feature.output}</dd></div>
      </dl>
    </article>
  );
}

export function WorkspacePage({ definition, children }: { definition: WorkspaceDefinition; children?: ReactNode }) {
  const { session } = useSession();
  const summaryQuery = useOperatorSummaryQuery();
  const Icon = definition.icon;

  return (
    <div className={`page-stack workspace-page workspace-page--${definition.tone}`}>
      <PageHeader eyebrow={definition.eyebrow} title={definition.title} description={definition.description} />

      <DescriptionBox
        audience={definition.audience}
        description={definition.description}
        howItWorks={definition.howItWorks}
        icon={Icon}
        outcome={definition.outcome}
        title={`${definition.title} system`}
        tone={definition.tone}
      />

      <section className="workspace-metrics" aria-label={`${definition.title} system status`}>
        {definition.metrics.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metricValue(metric, Boolean(session), summaryQuery.data)}</strong>
            <p>{metric.description}</p>
          </article>
        ))}
      </section>

      {children}

      <section className="workspace-feature-section" aria-labelledby={`${definition.slug}-features`}>
        <DescriptionBox
          compact
          description={`Every major ${definition.title.toLowerCase()} feature is separated below with its purpose, operating method, inputs, outputs, and current control state.`}
          howItWorks="Choose the feature relevant to the current task; its data remains organization-scoped and governed by the authoritative API."
          icon={Info}
          label="Feature directory"
          title="What each feature does"
          tone={definition.tone}
        />
        <h2 className="sr-only" id={`${definition.slug}-features`}>{definition.title} features</h2>
        <div className="workspace-feature-grid">
          {definition.features.map((feature, index) => <FeatureCard feature={feature} index={index} key={feature.id} />)}
        </div>
      </section>

      <section className="workspace-workflow" aria-label={`${definition.title} operating workflow`}>
        <DescriptionBox
          compact
          description={`This sequence explains how information moves through ${definition.title} from an initial input to a controlled football outcome.`}
          icon={CheckCircle2}
          label="Operating workflow"
          title="How this page works"
          tone={definition.tone}
        />
        <ol>
          {definition.workflow.map((step, index) => (
            <li key={step.title}>
              <span>{index + 1}</span>
              <div><strong>{step.title}</strong><p>{step.description}</p></div>
            </li>
          ))}
        </ol>
      </section>

      <DescriptionBox
        compact
        description={definition.boundary}
        icon={Info}
        label="Authority and migration boundary"
        title="What this system will not do silently"
        tone="amber"
      />
    </div>
  );
}
