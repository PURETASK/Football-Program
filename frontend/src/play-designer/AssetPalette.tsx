import { lazy, Suspense, useDeferredValue, useMemo, useState } from 'react';
import { BookOpen, Check, Filter, Search, Sparkles } from 'lucide-react';

import type { PlayAsset, PlayAssetCompatibility, PlayDesign, PlayTemplate, PlayTemplateLineageImpact, PlayTemplateLineageProposal } from '../types';
import { DesignerSectionGuide } from './DesignerSectionGuide';

const TemplateLibraryPanel = lazy(() => import('./TemplateLibraryPanel').then((module) => ({ default: module.TemplateLibraryPanel })));

interface AssetPaletteProps {
  assets: PlayAsset[];
  design: PlayDesign;
  activeAsset: PlayAsset | null;
  templates?: PlayTemplate[];
  loading?: boolean;
  onChoose: (asset: PlayAsset) => void;
  onApplyTemplate?: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onSaveTemplate?: (input: { name: string; description: string; tags: string[]; elementIds?: string[]; parentTemplateId?: string }) => Promise<void>;
  onInspectLineage?: (templateId: string) => Promise<PlayTemplateLineageImpact>;
  onProposeLineage?: (input: { templateId: string; key: string; field: string; value: string }) => Promise<PlayTemplateLineageProposal>;
  onApproveLineage?: (input: { proposalId: string; decisionRef: string }) => Promise<PlayTemplateLineageProposal>;
  canApproveLineage?: boolean;
  onCreateVariants?: (input: { field: 'front' | 'coverage' | 'formation' | 'concept'; labels: string[] }) => Promise<{ variants: PlayDesign[]; count: number }>;
  variantBatches?: Array<{ id: string; variants: PlayDesign[]; count: number; status: string; human_review_required?: boolean; review?: { ready: boolean; ready_count: number; blocked_count: number }; release_bundle?: { id: string; status: string; immutable: boolean; manifest_hash?: string; created_at?: string; production_activation: boolean; integrity_valid?: boolean } }>;
  onRequestVariantReview?: (batchId: string) => Promise<void>;
  onApproveVariantReview?: (batchId: string) => Promise<void>;
  onCreateVariantReleaseBundle?: (batchId: string) => Promise<void>;
  onInspectVariantReleaseBundle?: (bundleId: string) => Promise<{ valid: boolean; expected_manifest_hash?: string; declared_manifest_hash?: string }>;
  onOpenVariant?: (designId: string) => void;
  selectedElementIds?: string[];
}

const CATEGORY_ORDER = [
  'formation', 'route', 'motion', 'run', 'protection', 'block', 'front', 'coverage', 'pressure', 'stunt', 'rotation', 'check', 'teaching',
];

function assetName(asset: PlayAsset): string {
  return asset.display_name ?? asset.term.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function compatibilityFor(asset: PlayAsset, design: PlayDesign): PlayAssetCompatibility {
  if (asset.compatibility) return asset.compatibility;
  const reasons: string[] = [];
  if (asset.unit !== 'shared' && asset.unit !== design.unit) reasons.push(`Designed for ${asset.unit}.`);
  if (asset.compatible_formations?.length && design.formation && !asset.compatible_formations.includes(design.formation)) reasons.push(`Not cataloged for ${design.formation.replaceAll('_', ' ')}.`);
  if (asset.compatible_personnel?.length && design.personnel && !asset.compatible_personnel.includes(design.personnel)) reasons.push(`Not cataloged for ${design.personnel} personnel.`);
  if (asset.compatible_rule_profiles?.length && design.rule_profile && !asset.compatible_rule_profiles.includes(design.rule_profile)) reasons.push(`Not approved for ${design.rule_profile.replaceAll('_', ' ')} rules.`);
  const selectable = ['active', 'approved'].includes(asset.status ?? 'active');
  if (!selectable) reasons.push(`Lifecycle state is ${asset.status}.`);
  return { compatible: !reasons.length, selectable, score: Math.max(0, 100 - reasons.length * 30), reasons, warnings: [], basis: [] };
}

function previewPoints(asset: PlayAsset): string {
  const key = `${asset.term} ${asset.thumbnail ?? ''}`.toLowerCase();
  if (key.includes('post') || key.includes('glance') || key.includes('dig')) return '12,44 12,24 26,18 58,18';
  if (key.includes('corner') || key.includes('wheel')) return '12,44 12,22 32,16 60,8';
  if (key.includes('out') || key.includes('whip')) return '12,44 12,24 42,24 58,12';
  if (key.includes('slant') || key.includes('angle') || key.includes('cross')) return '12,44 12,22 40,34 64,18';
  if (key.includes('curl') || key.includes('comeback')) return '12,44 12,18 42,18 52,28 38,30';
  if (key.includes('flat') || key.includes('swing') || key.includes('screen')) return '12,44 24,34 52,34 68,27';
  if (key.includes('motion') || asset.kind === 'motion') return '12,38 30,38 48,26 72,26';
  if (asset.kind === 'coverage' || asset.kind === 'rotation') return '12,42 30,26 50,17 70,26';
  if (asset.kind === 'block' || asset.kind === 'run' || asset.kind === 'rush' || asset.kind === 'stunt') return '12,42 38,28 64,28';
  return '12,44 12,18 64,18';
}

function PathPreview({ asset }: { asset: PlayAsset }) {
  const color = asset.unit === 'defense' ? '#ffb547' : '#59d8f7';
  return (
    <svg className="asset-glyph asset-glyph--path-preview" viewBox="0 0 80 53" role="img" aria-label={`${assetName(asset)} diagram preview`}>
      <line className="asset-preview__los" x1="4" x2="76" y1="44" y2="44" />
      <polyline className="asset-preview__path" points={previewPoints(asset)} style={{ stroke: color }} />
      <polygon className="asset-preview__arrow" points="64,28 58,25 59,31" style={{ fill: color }} />
      <circle className="asset-preview__start" cx="12" cy="44" r="3" style={{ fill: color }} />
    </svg>
  );
}

function AssetGlyph({ asset }: { asset: PlayAsset }) {
  const kind = asset.kind;
  const slots = asset.alignment?.slots ?? [];
  if (slots.length) {
    return (
      <span className="asset-glyph asset-glyph--alignment" aria-hidden="true">
        <svg viewBox="0 0 100 53">
          <line x1="0" x2="100" y1="26.5" y2="26.5" />
          {slots.map((slot) => asset.unit === 'defense'
            ? <rect key={slot.key} x={slot.x - 2.2} y={slot.y - 2.2} width="4.4" height="4.4" rx="0.5" />
            : <circle key={slot.key} cx={slot.x} cy={slot.y} r="2.2" />)}
        </svg>
      </span>
    );
  }
  if (['formation', 'front'].includes(kind)) {
    return <span className="asset-glyph asset-glyph--formation" aria-hidden="true"><i /><i /><i /><i /><i /></span>;
  }
  if (['annotation', 'read', 'landmark', 'check'].includes(kind)) {
    return <span className="asset-glyph asset-glyph--teaching" aria-hidden="true">A</span>;
  }
  if (['route', 'motion', 'run', 'block', 'coverage', 'pressure', 'rush', 'stunt', 'rotation'].includes(kind)) {
    return <PathPreview asset={asset} />;
  }
  return <span className={`asset-glyph asset-glyph--${kind}`} aria-hidden="true"><i /></span>;
}

export function AssetPalette({ assets, design, activeAsset, templates = [], variantBatches = [], loading, onChoose, onApplyTemplate, onSaveTemplate, onCreateVariants, onOpenVariant, onRequestVariantReview, onApproveVariantReview, onCreateVariantReleaseBundle, onInspectVariantReleaseBundle, onInspectLineage, onProposeLineage, onApproveLineage, canApproveLineage, selectedElementIds = [] }: AssetPaletteProps) {
  const [libraryMode, setLibraryMode] = useState<'assets' | 'templates'>('assets');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [lifecycle, setLifecycle] = useState('available');
  const [compatibleOnly, setCompatibleOnly] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const categories = useMemo(
    () => [...new Set(assets.map((asset) => asset.category ?? asset.kind))]
      .sort((a, b) => (CATEGORY_ORDER.indexOf(a) === -1 ? 99 : CATEGORY_ORDER.indexOf(a)) - (CATEGORY_ORDER.indexOf(b) === -1 ? 99 : CATEGORY_ORDER.indexOf(b))),
    [assets],
  );
  const filtered = useMemo(() => {
    const term = deferredSearch.trim().toLowerCase();
    return assets.filter((asset) => {
      const haystack = [assetName(asset), asset.term, asset.kind, asset.category, ...(asset.aliases ?? [])].filter(Boolean).join(' ').toLowerCase();
      const categoryMatch = category === 'all' || (asset.category ?? asset.kind) === category;
      const compatibility = compatibilityFor(asset, design);
      const lifecycleMatch = lifecycle === 'all'
        || (lifecycle === 'available' ? compatibility.selectable : (asset.status ?? 'active') === lifecycle);
      return (!term || haystack.includes(term)) && categoryMatch && lifecycleMatch && (!compatibleOnly || compatibility.compatible);
    }).sort((left, right) => {
      const fit = compatibilityFor(right, design).score - compatibilityFor(left, design).score;
      return fit || assetName(left).localeCompare(assetName(right));
    });
  }, [assets, category, compatibleOnly, deferredSearch, design.formation, design.personnel, design.rule_profile, design.unit, lifecycle]);

  return (
    <aside className="asset-palette" aria-label="Play asset library" data-tutorial="assets">
      <header className="designer-panel-heading">
        <div>
          <span className="designer-kicker">Asset registry</span>
          <h2>Build the call</h2>
        </div>
        <span className="asset-count" title={`${libraryMode === 'assets' ? `${filtered.length} matching of ${assets.length} assets` : `${templates.length} reusable packages`}`}>{libraryMode === 'assets' ? `${filtered.length}/${assets.length}` : templates.length}</span>
      </header>

      <div className="library-mode-tabs" role="tablist" aria-label="Play designer library">
        <button type="button" role="tab" aria-selected={libraryMode === 'assets'} className={libraryMode === 'assets' ? 'is-active' : ''} onClick={() => setLibraryMode('assets')}><Sparkles size={14} /> Assets</button>
        <button type="button" role="tab" aria-selected={libraryMode === 'templates'} className={libraryMode === 'templates' ? 'is-active' : ''} onClick={() => setLibraryMode('templates')}><BookOpen size={14} /> Concepts</button>
      </div>

      {libraryMode === 'templates' ? (
        <Suspense fallback={<div className="asset-list__loading"><i /><i /><i /><i /></div>}>
          <TemplateLibraryPanel templates={templates} design={design} variantBatches={variantBatches} selectedElementIds={selectedElementIds} onApply={onApplyTemplate ?? (() => undefined)} onSave={onSaveTemplate} onCreateVariants={onCreateVariants} onOpenVariant={onOpenVariant} onRequestVariantReview={onRequestVariantReview} onApproveVariantReview={onApproveVariantReview} onCreateVariantReleaseBundle={onCreateVariantReleaseBundle} onInspectVariantReleaseBundle={onInspectVariantReleaseBundle} onInspectLineage={onInspectLineage} onProposeLineage={onProposeLineage} onApproveLineage={onApproveLineage} canApproveLineage={canApproveLineage} />
        </Suspense>
      ) : null}

      {libraryMode === 'assets' ? <>

      <DesignerSectionGuide title="Asset library" description="Search approved football building blocks, check compatibility, then choose one to author on the field." />

      <label className="designer-search">
        <Search size={15} aria-hidden="true" />
        <span className="sr-only">Search play assets</span>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search routes, fronts, checks…" />
      </label>

      <div className="asset-palette__filters">
        <label>
          <Filter size={14} aria-hidden="true" />
          <span className="sr-only">Asset category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="all">All categories</option>
            {categories.map((value) => <option value={value} key={value}>{value.replaceAll('_', ' ')}</option>)}
          </select>
        </label>
        <label>
          <span className="sr-only">Asset lifecycle</span>
          <select value={lifecycle} onChange={(event) => setLifecycle(event.target.value)}>
            <option value="available">Available</option>
            <option value="all">All lifecycle states</option>
            <option value="active">Active</option>
            <option value="approved">Approved</option>
            <option value="deprecated">Deprecated</option>
            <option value="retired">Retired</option>
          </select>
        </label>
        <button
          type="button"
          className={compatibleOnly ? 'compatibility-toggle is-active' : 'compatibility-toggle'}
          aria-pressed={compatibleOnly}
          onClick={() => setCompatibleOnly((value) => !value)}
        >
          <Check size={13} /> Fits call
        </button>
      </div>

      <div className="asset-palette__hint"><Sparkles size={14} /> Choose an assignment, then drag it onto the field.</div>

      {activeAsset ? (
        <div className="asset-selection" role="status">
          <div><strong>{assetName(activeAsset)}</strong><span>v{activeAsset.version ?? '1.0.0'}</span></div>
          <p>{activeAsset.description ?? activeAsset.accessibility}</p>
          {activeAsset.aliases?.length ? <small>Also called: {activeAsset.aliases.join(', ')}</small> : null}
        </div>
      ) : null}

      <div className="asset-list" aria-live="polite">
        {loading ? <div className="asset-list__loading"><i /><i /><i /><i /></div> : null}
        {!loading && !filtered.length ? (
          <div className="asset-list__empty"><Search size={20} /><strong>No assets found</strong><span>Try another category or clear compatibility.</span></div>
        ) : null}
        {filtered.map((asset) => {
          const compatibility = compatibilityFor(asset, design);
          const compatible = compatibility.compatible;
          const selectable = compatibility.selectable;
          const active = activeAsset?.id === asset.id;
          const guidance = [...compatibility.reasons, ...compatibility.warnings].join(' ');
          return (
            <button
              key={asset.id}
              type="button"
              className={`asset-card${active ? ' is-active' : ''}${compatible ? '' : ' is-incompatible'}`}
              aria-pressed={active}
              disabled={!selectable}
              title={[asset.description, guidance].filter(Boolean).join(' ')}
              onClick={() => onChoose(asset)}
            >
              <AssetGlyph asset={asset} />
              <span className="asset-card__copy">
                <strong>{assetName(asset)}</strong>
                <small>{asset.category ?? asset.kind} · {asset.status ?? 'active'}{compatibility.replacement_id ? ` → ${compatibility.replacement_id}` : ''}</small>
              </span>
              <span className={compatible ? 'asset-card__fit is-compatible' : 'asset-card__fit'}>{!selectable ? 'Closed' : compatible ? 'Fit' : 'Review'}</span>
            </button>
          );
        })}
      </div>
      </> : null}
    </aside>
  );
}
