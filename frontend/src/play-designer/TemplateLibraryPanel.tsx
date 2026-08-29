import { useDeferredValue, useMemo, useState } from 'react';
import { BookmarkPlus, Check, Layers3, Search, ShieldAlert, Sparkles } from 'lucide-react';

import type { PlayDesign, PlayTemplate } from '../types';
import { diffTemplateInheritance, resolveTemplateAssignments } from './templateMaterializer';
import { diffPlayVariant } from './variantDiff';

interface TemplateLibraryPanelProps {
  templates: PlayTemplate[];
  design: PlayDesign;
  onApply: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onSave?: (input: { name: string; description: string; tags: string[]; elementIds?: string[]; parentTemplateId?: string }) => Promise<void>;
  onCreateVariants?: (input: { field: 'front' | 'coverage' | 'formation' | 'concept'; labels: string[]; assignmentPatches?: Array<{ element_id: string; patch: Record<string, unknown> }> }) => Promise<{ variants: PlayDesign[]; count: number }>;
  variantBatches?: Array<{ id: string; variants: PlayDesign[]; count: number; status: string; human_review_required?: boolean; review?: { ready: boolean; ready_count: number; blocked_count: number }; release_bundle?: { id: string; status: string; immutable: boolean; manifest_hash?: string; created_at?: string; production_activation: boolean; integrity_valid?: boolean } }>;
  onRequestVariantReview?: (batchId: string) => Promise<void>;
  onApproveVariantReview?: (batchId: string) => Promise<void>;
  onCreateVariantReleaseBundle?: (batchId: string) => Promise<void>;
  onInspectVariantReleaseBundle?: (bundleId: string) => Promise<{ valid: boolean; expected_manifest_hash?: string; declared_manifest_hash?: string }>;
  onOpenVariant?: (designId: string) => void;
  selectedElementIds?: string[];
}

function titleCase(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function diffDetailLabel(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function diffDetailValue(value: unknown): string {
  if (value === undefined) return '—';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value); } catch { return String(value); }
}

function fieldLabel(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function templateContextFit(template: PlayTemplate, design: PlayDesign): { compatible: boolean; reasons: string[] } {
  const reasons: string[] = [];
  if (template.unit !== design.unit && template.unit !== 'shared') reasons.push(`Designed for ${template.unit}.`);
  for (const field of ['formation', 'personnel', 'front', 'coverage'] as const) {
    const expected = template[field];
    const actual = design[field];
    if (expected && actual && expected !== actual) reasons.push(`Uses ${field.replaceAll('_', ' ')} ${String(expected).replaceAll('_', ' ')}.`);
  }
  const lifecycle = String(template.status ?? 'active').toLowerCase();
  if (['deprecated', 'retired', 'archived'].includes(lifecycle)) reasons.push(`Template lifecycle state is ${lifecycle}.`);
  return { compatible: reasons.length === 0, reasons };
}

export function templateCanReplace(template: PlayTemplate, design: PlayDesign): boolean {
  const lifecycle = String(template.status ?? 'active').toLowerCase();
  return (template.unit === design.unit || template.unit === 'shared') && !['deprecated', 'retired', 'archived'].includes(lifecycle);
}

function DesignPreview({ design, label }: { design: PlayDesign; label: string }) {
  return <svg className="variant-design-preview" viewBox="0 0 100 53" role="img" aria-label={`${label} structured play diagram`}>
    <rect x="0" y="0" width="100" height="53" rx="3" />
    <line className="template-preview__los" x1="0" x2="100" y1="26.5" y2="26.5" />
    {(design.elements ?? []).map((element) => {
      const points = element.points ?? element.path ?? [];
      if (points.length < 2) return null;
      return <polyline className={`template-preview__path template-preview__path--${element.kind}`} key={element.id} points={points.map((point) => `${point.x},${point.y}`).join(' ')} />;
    })}
    {(design.players ?? []).map((player) => player.start ? <circle className="variant-design-preview__player" key={player.id} cx={player.start.x} cy={player.start.y} r="1.7" /> : null)}
  </svg>;
}

function TemplatePreview({ template }: { template: PlayTemplate }) {
  const slots = template.alignment?.slots ?? [];
  const slotByKey = new Map(slots.map((slot) => [slot.key, slot]));
  return (
    <svg className="template-preview" viewBox="0 0 100 53" role="img" aria-label={`${template.name} diagram preview`}>
      <rect x="0" y="0" width="100" height="53" rx="3" />
      <line className="template-preview__los" x1="0" x2="100" y1="26.5" y2="26.5" />
      {resolveTemplateAssignments(template).map(({ assignment, origin: assignmentOrigin }) => {
        const slot = slotByKey.get(assignment.slot);
        if (!slot || !assignment.points?.length) return null;
        const points = assignment.points.map((point) => `${slot.x + point.dx},${slot.y + point.dy}`).join(' ');
        return <polyline className={`template-preview__path template-preview__path--${assignment.kind} template-preview__path--${assignmentOrigin}`} key={assignment.key} points={points} />;
      })}
      {slots.map((slot) => template.unit === 'defense'
        ? <rect className="template-preview__player" key={slot.key} x={slot.x - 1.8} y={slot.y - 1.8} width="3.6" height="3.6" rx="0.5" />
        : <circle className="template-preview__player" key={slot.key} cx={slot.x} cy={slot.y} r="1.8" />)}
    </svg>
  );
}

export function TemplateLibraryPanel({ templates, design, variantBatches = [], onRequestVariantReview, onApproveVariantReview, onCreateVariantReleaseBundle, onInspectVariantReleaseBundle, onApply, onSave, onCreateVariants, onOpenVariant, selectedElementIds = [] }: TemplateLibraryPanelProps) {
  const [search, setSearch] = useState('');
  const [kind, setKind] = useState('all');
  const [compatibleOnly, setCompatibleOnly] = useState(false);
  const [replaceConfirmation, setReplaceConfirmation] = useState<string | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateTags, setTemplateTags] = useState('');
  const [captureSelection, setCaptureSelection] = useState(false);
  const [parentTemplateId, setParentTemplateId] = useState('');
  const [variantField, setVariantField] = useState<'front' | 'coverage' | 'formation' | 'concept'>('coverage');
  const [variantLabels, setVariantLabels] = useState('Cover 3, Cover 1, Quarters');
  const [variantAssignmentPatches, setVariantAssignmentPatches] = useState('');
  const [variantState, setVariantState] = useState<'idle' | 'saving' | 'error'>('idle');
  const [generatedVariants, setGeneratedVariants] = useState<PlayDesign[]>([]);
  const [reviewBatchId, setReviewBatchId] = useState<string | null>(null);
  const [approveBatchId, setApproveBatchId] = useState<string | null>(null);
  const [releaseBundleBatchId, setReleaseBundleBatchId] = useState<string | null>(null);
  const [inspectionBundleId, setInspectionBundleId] = useState<string | null>(null);
  const [inspectionResults, setInspectionResults] = useState<Record<string, { status: 'verified' | 'mismatch' | 'error'; expected?: string; declared?: string }>>({});
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const deferredSearch = useDeferredValue(search);
  const kinds = useMemo(() => [...new Set(templates.map((template) => template.template_kind ?? 'custom'))].sort(), [templates]);
  const filtered = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    return templates.filter((template) => {
      const haystack = [template.name, template.description, template.concept, template.formation, template.front, ...(template.tags ?? []), ...(template.situations ?? [])].filter(Boolean).join(' ').toLowerCase();
      const fit = templateContextFit(template, design);
      return (template.unit === design.unit || template.unit === 'shared') && (kind === 'all' || template.template_kind === kind) && (!compatibleOnly || fit.compatible) && (!query || haystack.includes(query));
    });
  }, [compatibleOnly, deferredSearch, design, kind, templates]);

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
      await onSave({ name: templateName.trim(), description: templateDescription.trim(), tags: templateTags.split(',').map((tag) => tag.trim()).filter(Boolean), ...(captureSelection && selectedElementIds.length ? { elementIds: selectedElementIds } : {}), ...(parentTemplateId ? { parentTemplateId } : {}) });
      setSaveState('saved');
      setTemplateName('');
      setTemplateDescription('');
      setTemplateTags('');
      setParentTemplateId('');
      setSaveOpen(false);
    } catch {
      setSaveState('error');
    }
  };

  const createVariants = async () => {
    if (!onCreateVariants) return;
    const labels = variantLabels.split(',').map((value) => value.trim()).filter(Boolean).slice(0, 32);
    if (!labels.length) return;
    let assignmentPatches: Array<{ element_id: string; patch: Record<string, unknown> }> | undefined;
    if (variantAssignmentPatches.trim()) {
      try {
        const parsed: unknown = JSON.parse(variantAssignmentPatches);
        if (!Array.isArray(parsed)) throw new Error('Assignment patches must be a JSON array.');
        assignmentPatches = parsed as Array<{ element_id: string; patch: Record<string, unknown> }>;
      } catch { setVariantState('error'); return; }
    }
    setVariantState('saving');
    try { const report = await onCreateVariants({ field: variantField, labels, assignmentPatches }); setGeneratedVariants(report.variants); setVariantState('idle'); } catch { setVariantState('error'); }
  };

  return (
    <div className="template-library">
      <div className="template-library__intro"><Sparkles size={15} /><span><strong>Reusable football packages</strong><small>Apply an approved call or combine compatible concept, protection, coverage, and pressure layers.</small></span></div>
      <div className="template-library__filters">
        <label className="designer-search"><Search size={15} aria-hidden="true" /><span className="sr-only">Search templates</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search concepts and situations..." /></label>
        <label><span className="sr-only">Template type</span><select value={kind} onChange={(event) => setKind(event.target.value)}><option value="all">All package types</option>{kinds.map((value) => <option value={value} key={value}>{titleCase(value)}</option>)}</select></label>
        <label className="template-compatible-toggle"><input type="checkbox" checked={compatibleOnly} onChange={(event) => setCompatibleOnly(event.target.checked)} /> <span>Context fit only</span></label>
      </div>

      <div className="template-card-list" aria-live="polite">
        {!filtered.length ? <div className="asset-list__empty"><Search size={20} /><strong>No matching packages</strong><span>Try another term or package type.</span></div> : null}
        {filtered.map((template) => {
          const fit = templateContextFit(template, design);
          const layerCompatible = fit.compatible;
          const replaceAllowed = templateCanReplace(template, design);
          const confirming = replaceConfirmation === template.id;
          const parent = template.parent_template_id ? templates.find((candidate) => candidate.id === template.parent_template_id) : undefined;
          const inheritanceDiff = parent ? diffTemplateInheritance(parent, template) : undefined;
          return <article className="template-card" key={template.id}>
            <TemplatePreview template={template} />
            <header><span><strong>{template.name}</strong><small>{titleCase(template.template_kind ?? 'custom')} · {template.scope ?? 'system'} · v{template.version ?? '1.0.0'}</small></span><span className={`template-status template-status--${template.status ?? 'active'}`}>{template.status ?? 'active'}</span></header>
            <p>{template.description ?? 'Reusable organization football package.'}</p>
            <p className={`template-context-fit${fit.compatible ? ' is-compatible' : ' is-review'}`} role="status">{fit.compatible ? 'Fits current play context.' : `Review fit: ${fit.reasons.join(' ')}`}</p>
            <div className="template-card__meta"><span>{template.formation ?? template.front ?? 'Any look'}</span><span>{template.personnel ?? 'Open personnel'}</span><span>{resolveTemplateAssignments(template).length} assignments</span>{template.inherited_assignments?.length ? <span>{template.inherited_assignments.length} inherited</span> : null}<span>{template.assignments?.length ?? 0} local</span></div>
            {template.parent_template_id ? <small className="template-companion"><Layers3 size={12} /> Inherits from {templates.find((parent) => parent.id === template.parent_template_id)?.name ?? template.parent_template_id}</small> : null}
            {inheritanceDiff ? <details className="template-inheritance-details"><summary>Inspect inheritance and overrides</summary><div className="template-inheritance-details__body"><span>{inheritanceDiff.inherited.length} inherited unchanged</span><span>{inheritanceDiff.overridden.length} overridden</span><span>{inheritanceDiff.added.length} child additions</span>{inheritanceDiff.overridden.length ? <ul>{inheritanceDiff.overridden.map((item) => <li key={item.key}><code>{item.key}</code><small>Overrides: {item.fields.map(fieldLabel).join(', ')}</small></li>)}</ul> : null}{inheritanceDiff.added.length ? <small>Added assignments: {inheritanceDiff.added.join(', ')}</small> : null}</div></details> : null}
            {template.tags?.length ? <div className="template-tags">{template.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}</div> : null}
            {template.expected_companion_layers?.length ? <small className="template-companion"><Layers3 size={12} /> Pair with: {template.expected_companion_layers.map(titleCase).join(', ')}</small> : <small className="template-companion"><Check size={12} /> Complete package</small>}
            {confirming ? <div className="template-replace-warning" role="alert"><ShieldAlert size={14} /><span>This replaces the current {design.elements?.length ?? 0} assignments. Click again to confirm.</span></div> : null}
            <footer>
              <button type="button" className={confirming ? 'template-action template-action--danger' : 'template-action'} disabled={!replaceAllowed} title={replaceAllowed ? 'Replace the current assignments with this package' : fit.reasons.join(' ')} onClick={() => replace(template)}>{confirming ? 'Confirm replace' : 'Use package'}</button>
              <button type="button" className="template-action template-action--secondary" disabled={!layerCompatible} title={layerCompatible ? 'Add without removing the current assignments' : fit.reasons.join(' ')} onClick={() => onApply(template, 'layer')}><Layers3 size={13} /> Add layer</button>
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
          {templates.some((template) => template.unit === design.unit && template.assignments?.length) ? <label><span>Inherit from existing package <small>(optional)</small></span><select aria-label="Inherit from existing package" value={parentTemplateId} onChange={(event) => setParentTemplateId(event.target.value)}><option value="">No parent package</option>{templates.filter((template) => template.unit === design.unit && template.assignments?.length).map((template) => <option value={template.id} key={template.id}>{template.name} · {template.scope ?? 'system'}</option>)}</select></label> : null}
          <button type="button" disabled={!templateName.trim() || saveState === 'saving'} onClick={() => void save()}>{saveState === 'saving' ? 'Saving...' : captureSelection && selectedElementIds.length ? 'Capture selected stencil' : 'Capture template'}</button>
          {saveState === 'error' ? <span role="alert">The template could not be saved.</span> : null}
        </div> : null}
      </section> : null}
      {onCreateVariants ? <section className="template-capture template-variants">
        <div className="template-library__intro"><Layers3 size={15} /><span><strong>Generate defensive-look variants</strong><small>Create traceable draft children from this play for multiple fronts, coverages, formations, or concepts.</small></span></div>
        <label><span>Variant field</span><select value={variantField} onChange={(event) => setVariantField(event.target.value as typeof variantField)}><option value="coverage">Coverage</option><option value="front">Front</option><option value="formation">Formation</option><option value="concept">Concept</option></select></label>
        <label><span>Look values <small>(comma separated, up to 32)</small></span><input value={variantLabels} onChange={(event) => setVariantLabels(event.target.value)} placeholder="Cover 3, Cover 1, Quarters" /></label>
        <label><span>Optional assignment transformations <small>(JSON; applied to every generated look)</small></span><textarea aria-label="Optional assignment transformations" rows={3} value={variantAssignmentPatches} onChange={(event) => setVariantAssignmentPatches(event.target.value)} placeholder='[{"element_id":"ROUTE-X","patch":{"type":"corner"}}]' /></label>
        <button type="button" disabled={!variantLabels.trim() || variantState === 'saving'} onClick={() => void createVariants()}>{variantState === 'saving' ? 'Generating variants…' : 'Generate draft variants'}</button>
        {variantState === 'error' ? <span role="alert">The variant batch could not be generated.</span> : null}
        {generatedVariants.length ? <div className="variant-review-rail" aria-label="Generated variant review"><strong>Generated review set</strong>{generatedVariants.map((variant) => { const diff = diffPlayVariant(design, variant); return <article className="variant-review-card" key={variant.id}><div className="variant-review-card__diagrams"><div><DesignPreview design={design} label="Source" /><small>Source</small></div><span aria-hidden="true">→</span><div><DesignPreview design={variant} label={variant.variant_look?.label ?? 'Variant'} /><small>{variant.variant_look?.label ?? 'Variant'}</small></div></div><div><strong>{variant.name ?? variant.id}</strong><small>{variant.variant_look?.label ?? 'Look variant'} · {variant.status ?? 'draft'} · v{variant.version ?? '0.1.0'}</small></div><span>{variant.variant_look?.patch ? Object.entries(variant.variant_look.patch as Record<string, unknown>).map(([key, value]) => `${titleCase(key)}: ${String(value)}`).join(' · ') : 'Explicit look patch'}</span><small className="variant-review-card__diff" aria-label={`${diff.metadata.length} metadata changes, ${diff.elements.changed.length} changed assignments, ${diff.elements.added.length} added assignments, ${diff.elements.removed.length} removed assignments`}>{diff.metadata.length} metadata · {diff.elements.changed.length} assignment changes · +{diff.elements.added.length} / −{diff.elements.removed.length} assignments · {diff.unchanged_elements} unchanged</small><details className="variant-review-card__details"><summary>Inspect field-level changes</summary><div className="variant-review-card__details-body">{diff.metadata.length ? <div><strong>Metadata</strong><span>{diff.metadata.map(diffDetailLabel).join(', ')}</span></div> : null}{diff.elements.changed.length ? <div><strong>Changed assignments</strong><ul>{diff.elements.changed.map((item) => <li key={item.id}><code>{item.id}</code><span>{item.changes.map((change) => `${diffDetailLabel(change.field)}: ${diffDetailValue(change.before)} → ${diffDetailValue(change.after)}`).join(' · ')}</span></li>)}</ul></div> : null}{diff.elements.added.length ? <div><strong>Added assignments</strong><span>{diff.elements.added.map((id) => <code key={id}>{id}</code>)}</span></div> : null}{diff.elements.removed.length ? <div><strong>Removed assignments</strong><span>{diff.elements.removed.map((id) => <code key={id}>{id}</code>)}</span></div> : null}{!diff.metadata.length && !diff.elements.changed.length && !diff.elements.added.length && !diff.elements.removed.length ? <span>No field-level changes.</span> : null}</div></details><button type="button" onClick={() => onOpenVariant?.(variant.id)} disabled={!onOpenVariant}>Open variant</button></article>; })}</div> : null}
      </section> : null}
      {variantBatches.length ? <section className="template-capture template-variant-history" aria-label="Persisted variant history">
        <div className="template-library__intro"><Layers3 size={15} /><span><strong>Saved review sets</strong><small>Reopen draft looks generated for this source play. These records remain human-review-required until staff approval.</small></span></div>
        <div className="variant-history-list">{variantBatches.map((batch) => <article className="variant-history-card" key={batch.id}>
          <header><span><strong>{batch.id}</strong><small>{batch.count} draft look{batch.count === 1 ? '' : 's'} · {batch.status}</small></span><span>{batch.review ? `${batch.review.ready_count}/${batch.count} ready for review` : batch.human_review_required ? 'Review required' : 'Recorded'}</span></header>
          {batch.release_bundle ? <div className="variant-history-card__bundle" role="status"><strong>Frozen release bundle · {batch.release_bundle.integrity_valid === false ? 'integrity check failed' : 'integrity verified'}</strong><span>{batch.release_bundle.id}</span><small>Immutable manifest · {batch.release_bundle.manifest_hash?.slice(0, 12)}… · production activation disabled</small>{onInspectVariantReleaseBundle ? <><button type="button" className="variant-history-card__inspect" disabled={inspectionBundleId === batch.release_bundle.id} onClick={async () => { setInspectionBundleId(batch.release_bundle?.id ?? null); try { const result = await onInspectVariantReleaseBundle(batch.release_bundle?.id ?? ''); setInspectionResults((current) => ({ ...current, [batch.release_bundle?.id ?? '']: { status: result.valid ? 'verified' : 'mismatch', expected: result.expected_manifest_hash, declared: result.declared_manifest_hash } })); } catch { setInspectionResults((current) => ({ ...current, [batch.release_bundle?.id ?? '']: { status: 'error' } })); } finally { setInspectionBundleId(null); } }}>{inspectionBundleId === batch.release_bundle.id ? 'Checking manifest…' : 'Verify manifest integrity'}</button>{inspectionResults[batch.release_bundle.id]?.status === 'verified' ? <small role="status">Server read verified the immutable manifest.</small> : null}{inspectionResults[batch.release_bundle.id]?.status === 'mismatch' ? <small role="alert">Server read detected a manifest mismatch. Do not distribute this bundle.</small> : null}{inspectionResults[batch.release_bundle.id]?.status === 'error' ? <small role="alert">The server integrity check could not be completed.</small> : null}</> : null}</div> : null}
          <div className="variant-history-card__looks">{batch.variants.map((variant) => <button type="button" key={variant.id} onClick={() => onOpenVariant?.(variant.id)} disabled={!onOpenVariant}><span>{variant.variant_look?.label ?? variant.name ?? variant.id}</span><small>{variant.id}</small></button>)}</div>
          {onRequestVariantReview && batch.status === 'created' && batch.review?.ready ? <button type="button" className="variant-history-card__review" disabled={reviewBatchId === batch.id} onClick={async () => { setReviewBatchId(batch.id); try { await onRequestVariantReview(batch.id); } finally { setReviewBatchId(null); } }}>{reviewBatchId === batch.id ? 'Requesting review…' : 'Request staff review'}</button> : null}
          {onApproveVariantReview && batch.status === 'under_review' ? <button type="button" className="variant-history-card__approve" disabled={approveBatchId === batch.id} onClick={async () => { setApproveBatchId(batch.id); try { await onApproveVariantReview(batch.id); } finally { setApproveBatchId(null); } }}>{approveBatchId === batch.id ? 'Approving batch…' : 'Approve batch for release'}</button> : null}
          {onCreateVariantReleaseBundle && batch.status === 'approved_for_release' ? <button type="button" className="variant-history-card__release" disabled={releaseBundleBatchId === batch.id} onClick={async () => { setReleaseBundleBatchId(batch.id); try { await onCreateVariantReleaseBundle(batch.id); } finally { setReleaseBundleBatchId(null); } }}>{releaseBundleBatchId === batch.id ? 'Freezing release…' : 'Freeze release bundle'}</button> : null}
        </article>)}</div>
      </section> : null}
    </div>
  );
}
