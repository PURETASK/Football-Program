import { AlertTriangle, Database, LoaderCircle, type LucideIcon, Search } from 'lucide-react';
import type { ReactNode } from 'react';

import { StatusPill, statusTone } from './StatusPill';

export interface WorkbenchTab {
  id: string;
  label: string;
  count?: number;
}

export function WorkbenchFrame({
  icon: Icon,
  eyebrow,
  title,
  description,
  actions,
  children,
}: {
  icon: LucideIcon;
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="operational-workbench" aria-labelledby={`workbench-${title.replaceAll(' ', '-').toLowerCase()}`}>
      <header className="operational-workbench__header">
        <span className="operational-workbench__icon" aria-hidden="true"><Icon size={22} /></span>
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={`workbench-${title.replaceAll(' ', '-').toLowerCase()}`}>{title}</h2>
          <p>{description}</p>
        </div>
        {actions ? <div className="operational-workbench__actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}

export function WorkbenchTabs({
  tabs,
  activeTab,
  onChange,
  label,
}: {
  tabs: WorkbenchTab[];
  activeTab: string;
  onChange: (tab: string) => void;
  label: string;
}) {
  return (
    <div className="workbench-tabs" role="tablist" aria-label={label}>
      {tabs.map((tab) => (
        <button
          aria-selected={activeTab === tab.id}
          className={activeTab === tab.id ? 'is-active' : ''}
          key={tab.id}
          onClick={() => onChange(tab.id)}
          role="tab"
          type="button"
        >
          {tab.label}
          {tab.count !== undefined ? <span>{tab.count}</span> : null}
        </button>
      ))}
    </div>
  );
}

export function WorkbenchState({
  connected,
  loading,
  error,
  children,
}: {
  connected: boolean;
  loading: boolean;
  error?: unknown;
  children: ReactNode;
}) {
  if (!connected) {
    return (
      <div className="workbench-state" role="status">
        <Database aria-hidden="true" size={24} />
        <strong>Connect an organization session</strong>
        <p>The controls are ready. Connect from the application header to load organization-scoped records and unlock authorized actions.</p>
      </div>
    );
  }
  if (loading) {
    return (
      <div className="workbench-state" role="status">
        <LoaderCircle aria-hidden="true" className="spin" size={24} />
        <strong>Loading the authoritative workspace</strong>
        <p>Retrieving the latest organization records and control state.</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="workbench-state workbench-state--error" role="alert">
        <AlertTriangle aria-hidden="true" size={24} />
        <strong>Workspace data could not be loaded</strong>
        <p>{error instanceof Error ? error.message : 'Check the API connection and your role permissions, then retry.'}</p>
      </div>
    );
  }
  return <>{children}</>;
}

export function WorkbenchSearch({
  value,
  onChange,
  label,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  placeholder: string;
}) {
  return (
    <label className="workbench-search">
      <span className="sr-only">{label}</span>
      <Search aria-hidden="true" size={16} />
      <input onChange={(event) => onChange(event.target.value)} placeholder={placeholder} type="search" value={value} />
    </label>
  );
}

export function WorkbenchStats({ stats }: { stats: Array<{ label: string; value: ReactNode; hint?: string }> }) {
  return (
    <dl className="workbench-stats">
      {stats.map((stat) => (
        <div key={stat.label}>
          <dt>{stat.label}</dt>
          <dd>{stat.value}</dd>
          {stat.hint ? <small>{stat.hint}</small> : null}
        </div>
      ))}
    </dl>
  );
}

export function RecordList<T extends { id: string; status?: string }>({
  records,
  selectedId,
  onSelect,
  title,
  subtitle,
  emptyMessage = 'No records match the current view.',
}: {
  records: T[];
  selectedId?: string;
  onSelect: (record: T) => void;
  title: (record: T) => string;
  subtitle?: (record: T) => string;
  emptyMessage?: string;
}) {
  if (!records.length) return <div className="record-list__empty">{emptyMessage}</div>;
  return (
    <div className="record-list" role="list">
      {records.map((record) => (
        <button
          aria-current={record.id === selectedId ? 'true' : undefined}
          className={record.id === selectedId ? 'is-selected' : ''}
          key={record.id}
          onClick={() => onSelect(record)}
          role="listitem"
          type="button"
        >
          <span className="record-list__copy">
            <strong>{title(record)}</strong>
            <small>{subtitle?.(record) || record.id}</small>
          </span>
          <StatusPill label={record.status || 'recorded'} tone={statusTone(record.status)} />
        </button>
      ))}
    </div>
  );
}

export function RecordInspector({
  eyebrow,
  title,
  status,
  facts,
  note,
  children,
}: {
  eyebrow: string;
  title: string;
  status?: string;
  facts: Array<{ label: string; value: ReactNode }>;
  note?: string;
  children?: ReactNode;
}) {
  return (
    <article className="record-inspector">
      <header>
        <div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div>
        {status ? <StatusPill label={status} tone={statusTone(status)} /> : null}
      </header>
      <dl>
        {facts.map((fact) => <div key={fact.label}><dt>{fact.label}</dt><dd>{fact.value}</dd></div>)}
      </dl>
      {note ? <p className="record-inspector__note">{note}</p> : null}
      {children}
    </article>
  );
}

export function MutationNotice({
  pending,
  success,
  error,
  successMessage,
}: {
  pending: boolean;
  success: boolean;
  error?: unknown;
  successMessage: string;
}) {
  if (!pending && !success && !error) return null;
  return (
    <p className={`mutation-notice${error ? ' mutation-notice--error' : success ? ' mutation-notice--success' : ''}`} role={error ? 'alert' : 'status'}>
      {pending ? 'Saving to the organization workspace…' : error instanceof Error ? error.message : error ? 'The action could not be completed.' : successMessage}
    </p>
  );
}
