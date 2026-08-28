import {
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  CircleDotDashed,
  ClipboardCheck,
  Film,
  Layers3,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import { DescriptionBox } from '../components/DescriptionBox';
import { EmptyState } from '../components/EmptyState';
import { MetricCard } from '../components/MetricCard';
import { PlayCard } from '../components/PlayCard';
import { StatusPill, statusTone } from '../components/StatusPill';
import { useOperatorSummaryQuery, usePlayDesignsQuery } from '../hooks/useWorkspaceData';

function metricValue(value: number | undefined, connected: boolean): number | string {
  return connected ? value ?? 0 : '—';
}

export function TodayPage() {
  const { session } = useSession();
  const summaryQuery = useOperatorSummaryQuery();
  const playsQuery = usePlayDesignsQuery();
  const summary = summaryQuery.data;
  const plays = playsQuery.data ?? [];
  const population = summary?.organization_population;
  const readiness = population?.required_component_count
    ? Math.round((population.ready_component_count / population.required_component_count) * 100)
    : 0;
  const queuedMedia = Object.values(summary?.media_job_counts ?? {}).reduce((total, count) => total + count, 0);
  const connected = Boolean(session);

  return (
    <div className="page-stack today-page">
      <section className="command-hero">
        <div className="command-hero__content">
          <div className="command-hero__meta">
            <StatusPill label={connected ? 'Team connected' : 'Demo-ready workspace'} tone={connected ? 'good' : 'info'} />
            <span>2026 · Football operations</span>
          </div>
          <p className="eyebrow eyebrow--light">Today’s command center</p>
          <h1>Build the week.<br />Teach the details.</h1>
          <p>
            Plays, film, practice, scouting, and approvals—organized around the decisions your staff needs to make next.
          </p>
          <div className="command-hero__actions">
            <Link className="button button--electric" to="/playbook">
              Open playbook <ArrowRight size={17} />
            </Link>
            <Link className="button button--glass" to="/film">
              Review film <Film size={17} />
            </Link>
          </div>
        </div>
        <div className="readiness-orbit" aria-label={`${readiness}% organization package readiness`}>
          <svg viewBox="0 0 140 140" aria-hidden="true">
            <circle cx="70" cy="70" r="58" pathLength="100" />
            <circle className="readiness-orbit__progress" cx="70" cy="70" r="58" pathLength="100" strokeDasharray={`${readiness} 100`} />
          </svg>
          <div>
            <strong>{connected ? `${readiness}%` : '—'}</strong>
            <span>Package readiness</span>
            <small>
              {population ? `${population.ready_component_count}/${population.required_component_count} ready` : 'Connect to inspect'}
            </small>
          </div>
        </div>
        <div className="command-hero__field-lines" aria-hidden="true" />
      </section>

      <DescriptionBox
        audience="Coaches, analysts, players, and program leadership receive role-appropriate priorities."
        description="Today is the front door to the football operating system. It summarizes readiness, active work, recent plays, and decisions without replacing the individual workspace where each task is completed."
        howItWorks="The page reads the organization-scoped operator summary and routes each action to its dedicated Playbook, Film, Practice, Scouting, Game Plan, Player, Review, or Admin page."
        icon={Sparkles}
        outcome="A prioritized daily picture and direct navigation to the correct individual system."
        title="Today command center"
        tone="cyan"
      />

      {!session ? (
        <section className="connection-callout" aria-labelledby="connect-heading">
          <span className="connection-callout__icon" aria-hidden="true"><Sparkles size={20} /></span>
          <div>
            <h2 id="connect-heading">Your synthetic organization is ready</h2>
            <p>Choose “Connect team” in the top bar and paste the local program-owner token to populate every panel.</p>
          </div>
          <code>ORG-DEMO-FIDOS-001</code>
        </section>
      ) : null}

      {summaryQuery.isError ? (
        <div className="inline-alert inline-alert--danger" role="alert">
          <ShieldAlert size={18} />
          <span>Team data could not be loaded. Refresh the token from the local demo script and reconnect.</span>
          <button type="button" className="button button--quiet" onClick={() => summaryQuery.refetch()}><RefreshCw size={15} /> Retry</button>
        </div>
      ) : null}

      <DescriptionBox
        compact
        description="These cards summarize the volume and readiness of the systems most likely to affect today’s staff decisions. Each metric links conceptually to a dedicated workspace rather than combining every workflow on this page."
        howItWorks="Counts come from the organization-scoped operator summary and play library; they are navigation context, not autonomous grades."
        icon={Layers3}
        label="Section description"
        title="How to read the program pulse"
        tone="blue"
      />

      <section className="metric-grid" aria-label="Program pulse">
        <MetricCard
          detail="Available to the staff"
          icon={BookOpenCheck}
          label="Play designs"
          tone="blue"
          value={metricValue(plays.length, connected)}
        />
        <MetricCard
          detail="Awaiting a human decision"
          icon={ClipboardCheck}
          label="Pending reviews"
          tone="amber"
          value={metricValue(summary?.pending_review_count, connected)}
        />
        <MetricCard
          detail="Authorized teaching clips"
          icon={Film}
          label="Film clips"
          tone="violet"
          value={metricValue(summary?.record_counts.film_clips, connected)}
        />
        <MetricCard
          detail={queuedMedia ? `${queuedMedia} media job in motion` : 'Pipeline clear'}
          icon={Layers3}
          label="Practice plans"
          tone="green"
          value={metricValue(summary?.record_counts.practice_plans, connected)}
        />
      </section>

      <div className="dashboard-grid">
        <section className="panel panel--wide" aria-labelledby="recent-plays-heading">
          <div className="panel__header">
            <div>
              <p className="eyebrow">Recently touched</p>
              <h2 id="recent-plays-heading">Playbook pulse</h2>
              <p className="section-helper">A quick view of recent canonical plays; open a card for its individual designer workspace.</p>
            </div>
            <Link className="text-link text-link--prominent" to="/playbook">View all plays <ArrowRight size={15} /></Link>
          </div>
          {playsQuery.isPending && session ? (
            <div className="skeleton-grid" aria-label="Loading plays">
              <span /><span /><span />
            </div>
          ) : plays.length ? (
            <div className="recent-play-grid">
              {plays.slice(0, 3).map((play) => <PlayCard compact design={play} key={play.id} />)}
            </div>
          ) : (
            <EmptyState
              description={session ? 'No organization-scoped play designs were returned.' : 'Connect the demo organization to load published, review, and branched designs.'}
              icon={BookOpenCheck}
              title="The playbook is waiting"
            />
          )}
        </section>

        <section className="panel decision-panel" aria-labelledby="decisions-heading">
          <div className="panel__header">
            <div>
              <p className="eyebrow">Decision queue</p>
              <h2 id="decisions-heading">What needs attention</h2>
              <p className="section-helper">Human-review work, source freshness, and operating-package readiness that may block downstream use.</p>
            </div>
            <StatusPill label={`${summary?.pending_review_count ?? 0} open`} tone={summary?.pending_review_count ? 'warning' : 'good'} />
          </div>
          <ol className="decision-list">
            <li>
              <span className="decision-list__icon decision-list__icon--amber"><ClipboardCheck size={17} /></span>
              <div><strong>Staff review queue</strong><span>{connected ? `${summary?.pending_review_count ?? 0} artifacts need a human decision` : 'Connect to load reviews'}</span></div>
              <ArrowRight size={15} />
            </li>
            <li>
              <span className="decision-list__icon decision-list__icon--blue"><CircleDotDashed size={17} /></span>
              <div><strong>Source freshness</strong><span>{connected ? `${summary?.stale_source_count ?? 0} source requires verification` : 'Evidence status unavailable'}</span></div>
              <ArrowRight size={15} />
            </li>
            <li>
              <span className="decision-list__icon decision-list__icon--green"><CheckCircle2 size={17} /></span>
              <div><strong>Operating bundle</strong><span>{population ? population.status.replaceAll('_', ' ') : 'Readiness not loaded'}</span></div>
              <ArrowRight size={15} />
            </li>
          </ol>
          <Link className="button button--secondary button--full" to="/reviews">Open review center</Link>
        </section>
      </div>

      <section className="stage-strip" aria-label="Current controlled stage">
        <div><span>Current stage</span><strong>{summary?.stage ?? 'STAGE-0'}</strong></div>
        <span className="stage-strip__line" />
        <div><span>Work package</span><strong>{summary?.work_package ?? 'STAGE-0A'}</strong></div>
        <span className="stage-strip__line" />
        <div><span>Population</span><strong>{population?.status.replaceAll('_', ' ') ?? 'Connect to verify'}</strong></div>
        <StatusPill label="Human controlled" tone={statusTone('under_review')} />
      </section>
    </div>
  );
}
