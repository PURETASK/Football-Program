import { useDeferredValue, useMemo, useState } from 'react';
import {
  BookOpenText,
  Filter,
  LayoutGrid,
  List,
  Plus,
  Search,
  Shield,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { useSession } from '../auth/SessionContext';
import { EmptyState } from '../components/EmptyState';
import { DescriptionBox } from '../components/DescriptionBox';
import { PageHeader } from '../components/PageHeader';
import { PlayCard } from '../components/PlayCard';
import { StatusPill } from '../components/StatusPill';
import { usePlayDesignsQuery, usePlayTemplatesQuery } from '../hooks/useWorkspaceData';

type ViewMode = 'grid' | 'list';

export function PlaybookPage() {
  const { session } = useSession();
  const playsQuery = usePlayDesignsQuery();
  const templatesQuery = usePlayTemplatesQuery();
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const [unit, setUnit] = useState('all');
  const [status, setStatus] = useState('all');
  const [view, setView] = useState<ViewMode>('grid');
  const designs = playsQuery.data ?? [];

  const filteredDesigns = useMemo(() => {
    const term = deferredSearch.trim().toLowerCase();
    return designs.filter((design) => {
      const searchable = [design.name, design.id, design.formation, design.personnel, design.unit].filter(Boolean).join(' ').toLowerCase();
      return (!term || searchable.includes(term)) && (unit === 'all' || design.unit === unit) && (status === 'all' || design.status === status);
    });
  }, [deferredSearch, designs, status, unit]);

  const published = designs.filter((design) => design.status === 'published').length;
  const review = designs.filter((design) => design.status === 'under_review').length;

  return (
    <div className="page-stack playbook-page">
      <PageHeader
        actions={
          <>
            <Link aria-label="Create offense play" className="button button--primary" to="/playbook/designer/new?unit=offense">
              <Plus size={17} /> Offense play
            </Link>
            <Link aria-label="Create defense play" className="button button--secondary" to="/playbook/designer/new?unit=defense">
              <Shield size={17} /> Defense call
            </Link>
          </>
        }
        description="Browse the visual library, understand install state at a glance, and move directly into design or teaching workflows."
        eyebrow="Football system"
        title="Playbook"
      />

      <DescriptionBox
        compact
        audience="Coordinators, position coaches, quality control, analysts, and approved players through filtered teaching views."
        description="The Playbook is the visual library for canonical offensive, defensive, and special-teams designs. It separates drafts, reviews, branches, and published releases so staff always know which version they are using."
        howItWorks="Search or filter the organization library, open a play in its dedicated designer, or create a registry-backed call from a system template."
        icon={BookOpenText}
        outcome="Validated play records that can feed teaching, practice, game planning, review, and professional exports."
        title="Playbook library system"
        tone="blue"
      />

      <section className="playbook-overview" aria-label="Playbook overview">
        <div className="playbook-overview__feature">
          <span className="playbook-overview__icon"><Workflow size={23} /></span>
          <div><span>Organization designs</span><strong>{session ? designs.length : '—'}</strong><small>Offense, defense, and branches</small></div>
        </div>
        <div><span>Published</span><strong>{session ? published : '—'}</strong><StatusPill label="game-plan ready" tone="good" /></div>
        <div><span>In review</span><strong>{session ? review : '—'}</strong><StatusPill label="staff decision" tone="warning" /></div>
        <div><span>Validation</span><strong>{session ? designs.filter((design) => design.validation?.status === 'valid').length : '—'}</strong><span className="micro-copy"><ShieldCheck size={14} /> structurally valid</span></div>
      </section>

      <section className="library-shell" aria-labelledby="play-library-heading">
        <div className="library-toolbar">
          <div>
            <p className="eyebrow">Visual library</p>
            <h2 id="play-library-heading">All plays</h2>
            <p className="section-helper">Each card is a canonical design with its own status, personnel, formation, validation state, and dedicated editor page.</p>
          </div>
          <label className="search-field">
            <Search size={17} aria-hidden="true" />
            <span className="sr-only">Search plays</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search concept, formation, personnel…" />
          </label>
          <label className="filter-select">
            <Filter size={15} aria-hidden="true" />
            <span className="sr-only">Filter by unit</span>
            <select value={unit} onChange={(event) => setUnit(event.target.value)}>
              <option value="all">All units</option>
              <option value="offense">Offense</option>
              <option value="defense">Defense</option>
              <option value="special_teams">Special teams</option>
            </select>
          </label>
          <label className="filter-select">
            <span className="sr-only">Filter by status</span>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="all">All statuses</option>
              <option value="published">Published</option>
              <option value="under_review">In review</option>
              <option value="draft">Draft</option>
            </select>
          </label>
          <div className="view-toggle" aria-label="Library view">
            <button className={view === 'grid' ? 'is-active' : ''} type="button" aria-label="Grid view" aria-pressed={view === 'grid'} onClick={() => setView('grid')}><LayoutGrid size={16} /></button>
            <button className={view === 'list' ? 'is-active' : ''} type="button" aria-label="List view" aria-pressed={view === 'list'} onClick={() => setView('list')}><List size={16} /></button>
          </div>
        </div>

        {playsQuery.isPending && session ? (
          <div className="play-grid skeleton-grid skeleton-grid--plays" aria-label="Loading play library"><span /><span /><span /></div>
        ) : filteredDesigns.length ? (
          <div className={view === 'grid' ? 'play-grid' : 'play-grid play-grid--list'}>
            {filteredDesigns.map((design) => <PlayCard design={design} key={design.id} />)}
          </div>
        ) : (
          <EmptyState
            action={session ? <button className="button button--secondary" type="button" onClick={() => { setSearch(''); setUnit('all'); setStatus('all'); }}>Clear filters</button> : null}
            description={session ? 'No plays match the current search and filters.' : 'Connect your organization to load the seeded offense, defense, release, and branch.'}
            icon={BookOpenText}
            title={session ? 'No matching plays' : 'Connect to open the playbook'}
          />
        )}
      </section>

      <section className="template-section" aria-labelledby="templates-heading">
        <div className="panel__header">
          <div><p className="eyebrow">Fast start</p><h2 id="templates-heading">Build from a system template</h2><p className="section-helper">Templates establish an approved starting structure; the new design receives its own identity and remains editable before review.</p></div>
          <span className="micro-copy"><Sparkles size={14} /> Registry-backed starting points</span>
        </div>
        <div className="template-grid">
          {(templatesQuery.data ?? []).map((template, index) => (
            <Link className={`template-card template-card--${['cyan', 'amber', 'violet'][index % 3]}`} to={`/playbook/designer/new?template=${encodeURIComponent(template.id)}`} key={template.id}>
              <span className="template-card__diagram" aria-hidden="true"><i /><i /><i /></span>
              <span><strong>{template.name}</strong><small>{template.unit} · {(template.formation ?? 'open').replaceAll('_', ' ')}</small></span>
              <Plus size={17} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
