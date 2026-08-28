import { useDeferredValue, useMemo, useState } from 'react';
import { BookmarkPlus, Check, Layers3, Search, ShieldAlert, Sparkles } from 'lucide-react';

import type { PlayDesign, PlayTemplate } from '../types';

interface TemplateLibraryPanelProps {
  templates: PlayTemplate[];
  design: PlayDesign;
  onApply: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onSave?: (input: { name: string; description: string; tags: string[]; elementIds?: string[] }) => Promise<void>;
  selectedElementIds?: string[];
}

function titleCase(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function TemplatePreview({ template }: { template: PlayTemplate }) {
  const slots = template.alignment?.slots ?? [];
  const slotByKey = new Map(slots.map((slot) => [slot.key, slot]));
  return (
    <svg className="template-preview" viewBox="0 0 100 53" role="img" aria-label={`${template.name} diagram preview`}>
      <rect x="0" y="0" width="100" height="53" rx="3" />
      <line className="template-preview__los" x1="0" x2="100" y1="26.5" y2="26.5" />
      {(template.assignments ?? []).map((assignment) => {
        const slot = slotByKey.get(assignment.slot);
        if (!slot || !assignment.points?.length) return null;
        const points = assignment.points.map((point) => `${slot.x + point.dx},${slot.y + point.dy}`).join(' ');
        return <polyline className={`template-preview__path template-preview__path--${assignment.kind}`} key={assignment.key} points={points} />;
      })}
      {slots.map((slot) => template.unit === 'defense'
        ? <rect className="template-preview__player" key={slot.key} x={slot.x - 1.8} y={slot.y - 1.8} width="3.6" height="3.6" rx="0.5" />
        : <circle className="template-preview__player" key={slot.key} cx={slot.x} cy={slot.y} r="1.8" />)}
    </svg>
  );
}

export function TemplateLibraryPanel({ templates, design, onApply, onSave, selectedElementIds = [] }: TemplateLibraryPanelProps) {
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('all');
  const [replaceConfirmation, setReplaceConfirmation] = useState<string | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateTags, setTemplateTags] = useState('');
  const [captureSelection, setCaptureSelection] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const deferredSearch = useDeferredValue(search);
  const kinds = useMemo(() => [...new Set(templates.map((template) => template.template_kind ?? 'custom'))].sort(), [templates]);
  const filtered = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    return templates.filter((template) => {
      const haystack = [template.name, template.description, template.concept, template.formation, template.front, ...(template.tags ?? []), ...(template.situations ?? [])].filter(Boolean).join(' ').toLowerCase();
      return template.unit === design.unit && (kind === 'all' || template.template_kind === kind) && (!query || haystack.includes(query));
    });
  }, [deferredSearch, design.unit, kind, templates]);

  const replace = (template: PlayTemplate) => {
    if ((design.elements ?? []).length && replaceConfirmation !== template.id) {
      setReplaceConfirmation(template.id);
      return;
    }
    onApply(template, 'replace');
    setReplaceConfirmation(null);
  };

  const save = async () => {
    if (!onSave || !templateName.trim()) return;
    setSaveState('saving');
    try {
      await onSave({ name: templateName.trim(), description: templateDescription.trim(), tags: templateTags.split(',').map((tag) => tag.trim()).filter(Boolean), ...(captureSelection && selectedElementIds.length ? { elementIds: selectedElementIds } : {}) });
      setSaveState('saved');
      setTemplateName('');
      setTemplateDescription('');
      setTemplateTags('');
      setSaveOpen(false);
    } catch {
      setSaveState('error');
    }
  };

  return (
    <div className="template-library">
      <div className="template-library__intro"><Sparkles size={15} /><span><strong>Reusable football packages</strong><small>Apply an approved call or combine compatible concept, protection, coverage, and pressure layers.</small></span></div>
      <div className="template-library__filters">
        <label className="designer-search"><Search size={15} aria-hidden="true" /><span className="sr-only">Search templates</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search concepts and situations..." /></label>
        <label><span className="sr-only">Template type</span><select value={kind} onChange={(event) => setKind(event.target.value)}><option value="all">All package types</option>{kinds.map((value) => <option value={value} key={value}>{titleCase(value)}</option>)}</select></label>
      </div>

      <div className="template-card-list" aria-live="polite">
        {!filtered.length ? <div className="asset-list__empty"><Search size={20} /><strong>No matching packages</strong><span>Try another term or package type.</span></div> : null}
        {filtered.map((template) => {
          const sameFormation = !template.formation || template.formation === design.formation;
          const layerCompatible = sameFormation && template.unit === design.unit;
          const confirming = replaceConfirmation === template.id;
          return <article className="template-card" key={template.id}>
            <TemplatePreview template={template} />
            <header><span><strong>{template.name}</strong><small>{titleCase(template.template_kind ?? 'custom')} · {template.scope ?? 'system'} · v{template.version ?? '1.0.0'}</small></span><span className={`template-status template-status--${template.status ?? 'active'}`}>{template.status ?? 'active'}</span></header>
            <p>{template.description ?? 'Reusable organization football package.'}</p>
            <div className="template-card__meta"><span>{template.formation ?? template.front ?? 'Any look'}</span><span>{template.personnel ?? 'Open personnel'}</span><span>{template.assignments?.length ?? 0} assignments</span></div>
            {template.tags?.length ? <div className="template-tags">{template.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}</div> : null}
            {template.expected_companion_layers?.length ? <small className="template-companion"><Layers3 size={12} /> Pair with: {template.expected_companion_layers.map(titleCase).join(', ')}</small> : <small className="template-companion"><Check size={12} /> Complete package</small>}
            {confirming ? <div className="template-replace-warning" role="alert"><ShieldAlert size={14} /><span>This replaces the current {design.elements?.length ?? 0} assignments. Click again to confirm.</span></div> : null}
            <footer>
              <button type="button" className={confirming ? 'template-action template-action--danger' : 'template-action'} onClick={() => replace(template)}>{confirming ? 'Confirm replace' : 'Use package'}</button>
              <button type="button" className="template-action template-action--secondary" disabled={!layerCompatible} title={layerCompatible ? 'Add without removing the current assignments' : 'Layers require the current formation'} onClick={() => onApply(template, 'layer')}><Layers3 size={13} /> Add layer</button>
            </footer>
          </article>;
        })}
      </div>

      {onSave ? <section className="template-capture">
        <button type="button" className="template-capture__toggle" aria-expanded={saveOpen} disabled={!design._revision || !(design.elements ?? []).length} onClick={() => setSaveOpen((value) => !value)}><BookmarkPlus size={15} /> Save current play as template</button>
        {!design._revision ? <small>Save the play first so the template can retain its immutable source snapshot.</small> : null}
        {saveOpen ? <div className="template-capture__form">
          <label><span>Template name</span><input value={templateName} onChange={(event) => setTemplateName(event.target.value)} placeholder="Third-down package" /></label>
          <label><span>Description</span><textarea rows={2} value={templateDescription} onChange={(event) => setTemplateDescription(event.target.value)} placeholder="When and how staff should use this package." /></label>
          <label><span>Tags</span><input value={templateTags} onChange={(event) => setTemplateTags(event.target.value)} placeholder="third-down, boundary, install-2" /></label>
          {selectedElementIds.length ? <label className="template-capture__scope"><input type="checkbox" checked={captureSelection} onChange={(event) => setCaptureSelection(event.target.checked)} /> Capture only the {selectedElementIds.length} selected assignment{selectedElementIds.length === 1 ? '' : 's'} as a reusable stencil</label> : null}
          <button type="button" disabled={!templateName.trim() || saveState === 'saving'} onClick={() => void save()}>{saveState === 'saving' ? 'Saving...' : captureSelection && selectedElementIds.length ? 'Capture selected stencil' : 'Capture template'}</button>
          {saveState === 'error' ? <span role="alert">The template could not be saved.</span> : null}
        </div> : null}
      </section> : null}
    </div>
  );
}
