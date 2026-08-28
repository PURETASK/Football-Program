import { lazy, Suspense, useState, type ReactNode } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  EyeOff,
  GitCompareArrows,
  GitBranch,
  History,
  Layers3,
  Lock,
  MessageSquare,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Unlock,
  UserRound,
} from 'lucide-react';

import type {
  PlayComment,
  PlayDesign,
  PlayDesignDiff,
  PlayDraftValidationReport,
  PlayElement,
  PlayFieldContext,
  PlayLegalityReport,
  PlayAsset,
  PlayPlayer,
  PlayTemplate,
  PlayMergeResult,
  PlayVersionHistory,
  Point,
} from '../types';
import type { EditorSelection } from './editorState';
import { DesignerSectionGuide } from './DesignerSectionGuide';
import { PositionToolkit } from './PositionToolkit';
import { DEFENSIVE_GAP_OPTIONS, defensiveGapOwners, defensiveGapSummary } from './defensiveFront';
import { routeCollisions } from './geometry';
import { DEFENSIVE_ALIGNMENTS, DEFENSIVE_TECHNIQUES, defensiveAlignmentIssues, defensiveAlignmentPatch } from './defensiveAlignment';
import { CoverageShellEditor } from './CoverageShellEditor';
import { rotationLabel } from './rotationSequencing';
import { DEFENSIVE_EXCHANGE_ROLES, clearDefensiveExchangePairPatch, defensiveExchangePairPatch } from './defensiveExchanges';
import { defensiveResponsibilityIssues } from './defensiveResponsibilityValidation';

const AssignmentGraphFields = lazy(() => import('./AssignmentGraphFields').then((module) => ({ default: module.AssignmentGraphFields })));

export type InspectorTab = 'inspect' | 'layers' | 'validate' | 'review';

interface InspectorProps {
  design: PlayDesign;
  selected: EditorSelection[];
  tab: InspectorTab;
  dirty: boolean;
  legality?: PlayLegalityReport | PlayDraftValidationReport;
  versions?: PlayVersionHistory;
  versionDiff?: PlayDesignDiff;
  compareBaseId?: string;
  compareSnapshotId?: string;
  compareVisible?: boolean;
  mergeConflict?: PlayMergeResult;
  comments: PlayComment[];
  actionBusy?: boolean;
  actionMessage?: string;
  validationPending?: boolean;
  validationError?: string;
  onTab: (tab: InspectorTab) => void;
  onSelect: (selection: EditorSelection | null, additive?: boolean) => void;
  onMeta: (patch: Partial<PlayDesign>) => void;
  onFieldContext: (patch: Partial<PlayFieldContext>, translate?: Point) => void;
  onPlayer: (id: string, patch: Partial<PlayPlayer>) => void;
  onElement: (id: string, patch: Partial<PlayElement>) => void;
  onComment: (text: string, elementId?: string) => void;
  onRequestReview: (decisionRef: string) => void;
  onPublish: (decisionRef: string) => void;
  onBranch: (branchId: string) => void;
  onCompare: (baseSnapshotId: string, compareSnapshotId: string) => void;
  onToggleCompare?: (visible: boolean) => void;
  onMerge: (branchId: string) => void;
  assets?: PlayAsset[];
  templates?: PlayTemplate[];
  onChooseAsset?: (asset: PlayAsset) => void;
  onApplyTemplate?: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onMaterializeAsset?: (asset: PlayAsset) => void;
}

const RULE_PROFILES = [
  ['nfl', 'NFL'], ['ncaa', 'NCAA'], ['high_school', 'High school'], ['youth', 'Youth'], ['flag', 'Flag'],
];

const HASH_X: Record<string, number> = { left: 38, middle: 50, right: 62 };
const COVERAGE_ZONE_OPTIONS = [
  ['deep_left', 'Deep left'], ['deep_middle', 'Deep middle'], ['deep_right', 'Deep right'],
  ['deep_half_left', 'Deep half left'], ['deep_half_right', 'Deep half right'],
  ['flat_left', 'Flat left'], ['flat_right', 'Flat right'],
  ['hook_curl_left', 'Hook/curl left'], ['hook_curl_middle', 'Hook/curl middle'], ['hook_curl_right', 'Hook/curl right'],
  ['robber', 'Robber / low hole'], ['man', 'Man coverage'], ['bracket', 'Bracket / double'],
] as const;

const TAB_GUIDANCE: Record<InspectorTab, { title: string; description: string }> = {
  inspect: { title: 'Inspect and edit', description: 'Edit play identity, player alignment, assignment details, timing, and visibility without redrawing the call.' },
  layers: { title: 'Layers and control', description: 'Select, show, hide, lock, and organize every player and assignment in the canonical diagram.' },
  validate: { title: 'Football checks', description: 'Review explainable structural and legality findings for the selected rule profile before staff approval.' },
  review: { title: 'Review and history', description: 'Add linked comments, request a decision, publish or branch the call, and inspect immutable version evidence.' },
};

function reviewValue(value: unknown): string {
  if (value === undefined) return 'Not present';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value); } catch { return String(value); }
}

function CommitInput({
  label,
  value,
  type = 'text',
  min,
  max,
  onCommit,
}: {
  label: string;
  value: string | number | undefined;
  type?: 'text' | 'number';
  min?: number;
  max?: number;
  onCommit: (value: string) => void;
}) {
  const stringValue = value === undefined ? '' : String(value);
  return (
    <label className="inspector-field">
      <span>{label}</span>
      <input
        key={stringValue}
        type={type}
        min={min}
        max={max}
        defaultValue={stringValue}
        onBlur={(event) => { if (event.target.value !== stringValue) onCommit(event.target.value); }}
        onKeyDown={(event) => { if (event.key === 'Enter') event.currentTarget.blur(); }}
      />
    </label>
  );
}

function InspectorSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="inspector-section"><h3>{title}</h3>{children}</section>;
}

function DefensiveFrontMap({ design, onSelect }: Pick<InspectorProps, 'design' | 'onSelect'>) {
  const owners = defensiveGapOwners(design);
  const gapSummary = defensiveGapSummary(design);
  const alignmentIssues = defensiveAlignmentIssues(design);
  return <InspectorSection title="Defensive front map">
    <p className="inspector-help">Canonical gap ownership for the current front. Select an owned gap to jump to its assignment; duplicate/conflicting ownership is marked for review.</p>
    <div className={`front-readiness-summary front-readiness-summary--${gapSummary.status}`} role="status"><strong>{gapSummary.owned}/{gapSummary.total} gaps owned</strong><span>{gapSummary.unassigned} unassigned · {gapSummary.conflicts} conflict{gapSummary.conflicts === 1 ? '' : 's'}</span><em>{gapSummary.status === 'ready' ? 'Front ready for review' : 'Front needs review'}</em></div>
    {alignmentIssues.length ? <div className="inspector-diagnostic-list" role="alert" aria-label="Defensive alignment diagnostics"><strong>{alignmentIssues.length} alignment issue{alignmentIssues.length === 1 ? '' : 's'}</strong>{alignmentIssues.map((issue) => <button type="button" key={`${issue.code}-${issue.playerIds.join('-')}`} onClick={() => onSelect({ kind: 'player', id: issue.playerIds[0] })}>{issue.message}</button>)}</div> : null}
    <div className="defensive-front-map" role="group" aria-label="Defensive gap ownership map">
      {DEFENSIVE_GAP_OPTIONS.map(([value, label]) => {
        const owner = owners.get(value);
        return <button type="button" key={value} className={`defensive-front-gap${owner?.conflict ? ' is-conflict' : ''}`} aria-label={`${label}: ${owner?.owner ?? 'Unassigned'}${owner?.conflict ? ', conflict' : ''}`} disabled={!owner} onClick={() => owner && onSelect({ kind: 'element', id: owner.elementId })}>
          <span>{label}</span><strong>{owner?.owner ?? 'Unassigned'}</strong>{owner?.conflict ? <em>Conflict</em> : null}
        </button>;
      })}
    </div>
  </InspectorSection>;
}

function RotationSequencePanel({ design, onSelect }: Pick<InspectorProps, 'design' | 'onSelect'>) {
  const sequence = (design.elements ?? []).filter((element) => element.kind === 'rotation' || element.rotation_sequence !== undefined).sort((a, b) => (a.rotation_sequence ?? 999) - (b.rotation_sequence ?? 999));
  if (!sequence.length) return null;
  return <InspectorSection title="Post-snap rotation lane">
    <p className="inspector-help">Teach the shell in order: each card shows the trigger, replacement zone, and connected exchange responsibility.</p>
    <div className="rotation-sequence-lane" role="list" aria-label="Post-snap defensive rotation sequence">
      {sequence.map((element, index) => <div className="rotation-sequence-step" role="listitem" key={element.id}>
        <button type="button" onClick={() => onSelect({ kind: 'element', id: element.id })} aria-label={`Edit rotation ${index + 1}: ${rotationLabel(element)}`}>
          <span className="rotation-sequence-step__number">{element.rotation_sequence ?? index + 1}</span>
          <span><strong>{element.player_id ?? element.type ?? 'Defender'}</strong><small>{rotationLabel(element)}</small></span>
          {element.exchange_with ? <em>↔ {(design.elements ?? []).find((item) => item.id === element.exchange_with)?.player_id ?? element.exchange_with}</em> : null}
        </button>
        {index < sequence.length - 1 ? <span className="rotation-sequence-step__connector" aria-hidden="true">↓</span> : null}
      </div>)}
    </div>
  </InspectorSection>;
}

function SelectionInspector({
  design,
  selected,
  onPlayer,
  onElement,
  assets,
  templates,
  onChooseAsset,
  onApplyTemplate,
  onMaterializeAsset,
}: Pick<InspectorProps, 'design' | 'selected' | 'onPlayer' | 'onElement' | 'assets' | 'templates' | 'onChooseAsset' | 'onApplyTemplate' | 'onMaterializeAsset'>) {
  if (!selected.length) {
    return (
      <div className="inspector-empty">
        <SlidersHorizontal size={24} />
        <strong>Nothing selected</strong>
        <span>Select a player or assignment to edit its football details.</span>
      </div>
    );
  }
  if (selected.length > 1) {
    const selectedElements = selected.filter((item): item is { kind: 'element'; id: string } => item.kind === 'element').map((item) => (design.elements ?? []).find((element) => element.id === item.id)).filter((element): element is PlayElement => Boolean(element));
    if (design.unit === 'defense' && selectedElements.length === 2) return <ExchangePairAuthoring elements={selectedElements} onElement={onElement} />;
    return (
      <div className="multi-selection-card">
        <Layers3 size={20} />
        <div><strong>{selected.length} items selected</strong><span>Duplicate, mirror, group, lock, or delete from the top toolbar.</span></div>
      </div>
    );
  }
  const selection = selected[0];
  if (selection.kind === 'player') {
    const player = (design.players ?? []).find((item) => item.id === selection.id);
    if (!player) return null;
    return (
      <InspectorSection title="Player">
        <div className="selected-object-heading"><span><UserRound size={15} /></span><div><strong>{player.position ?? player.role ?? player.id}</strong><small>{player.id}</small></div></div>
        <div className="inspector-form inspector-form--two">
          <CommitInput label="Position" value={player.position} onCommit={(value) => onPlayer(player.id, { position: value, role: value })} />
          <CommitInput label="Label" value={player.label} onCommit={(value) => onPlayer(player.id, { label: value })} />
          <CommitInput label="Field X" type="number" min={0} max={100} value={player.start?.x} onCommit={(value) => onPlayer(player.id, { start: { x: Number(value), y: player.start?.y ?? 26 } })} />
          <CommitInput label="Field Y" type="number" min={0} max={53} value={player.start?.y} onCommit={(value) => onPlayer(player.id, { start: { x: player.start?.x ?? 50, y: Number(value) } })} />
        </div>
        {design.unit === 'defense' ? <fieldset className="defensive-alignment-editor">
          <legend>Front technique and alignment</legend>
          <p>Set the defender’s technique and relationship to the adjacent offensive surface.</p>
          <label className="inspector-field"><span>Technique</span><select value={player.defensive_technique ?? ''} onChange={(event) => onPlayer(player.id, defensiveAlignmentPatch(event.target.value, player.defensive_alignment ?? ''))}><option value="">Unspecified</option>{DEFENSIVE_TECHNIQUES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          <label className="inspector-field"><span>Alignment relationship</span><select value={player.defensive_alignment ?? ''} onChange={(event) => onPlayer(player.id, defensiveAlignmentPatch(player.defensive_technique ?? '', event.target.value))}><option value="">Unspecified</option>{DEFENSIVE_ALIGNMENTS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        </fieldset> : null}
        <PositionToolkit
          player={player}
          design={design}
          assets={assets ?? []}
          templates={templates ?? []}
          onChooseAsset={onChooseAsset ?? (() => undefined)}
          onApplyTemplate={onApplyTemplate ?? (() => undefined)}
          onMaterializeAsset={onMaterializeAsset}
        />
      </InspectorSection>
    );
  }
  const element = (design.elements ?? []).find((item) => item.id === selection.id);
  if (!element) return null;
  const collisionPairs = element.kind === 'route' ? routeCollisions(design.elements ?? []).filter((pair) => pair.firstId === element.id || pair.secondId === element.id) : [];
  return (
    <InspectorSection title="Assignment">
      <div className="selected-object-heading"><span><GitBranch size={15} /></span><div><strong>{element.type ?? element.kind}</strong><small>{element.id}</small></div></div>
      <div className="inspector-form">
        <CommitInput label="Call / variation" value={element.type} onCommit={(value) => onElement(element.id, { type: value })} />
        <label className="inspector-field"><span>Assignment type</span><select value={element.kind} onChange={(event) => onElement(element.id, { kind: event.target.value, arrow_style: event.target.value })}>
          {['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'rotation', 'fit', 'read', 'annotation'].map((kind) => <option value={kind} key={kind}>{kind}</option>)}
        </select></label>
        <div className="inspector-form inspector-form--two inspector-form--nested">
          <label className="inspector-field"><span>Arrow / line meaning</span><select value={element.arrow_style ?? element.kind} onChange={(event) => onElement(element.id, { arrow_style: event.target.value })}>
            {['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'annotation', 'none'].map((style) => <option value={style} key={style}>{style === 'none' ? 'No arrow' : style}</option>)}
          </select></label>
          <label className="inspector-field"><span>Line treatment</span><select value={element.line_style ?? 'solid'} onChange={(event) => onElement(element.id, { line_style: event.target.value })}>
            {['solid', 'dashed', 'dotted'].map((style) => <option value={style} key={style}>{style}</option>)}
          </select></label>
          <label className="inspector-field"><span>Arrowheads</span><select value={element.arrow_ends ?? 'end'} onChange={(event) => onElement(element.id, { arrow_ends: event.target.value })}>
            <option value="end">At finish</option><option value="start">At start</option><option value="both">Both ends</option><option value="none">None</option>
          </select></label>
          <label className="inspector-field"><span>Path geometry</span><select value={element.path_mode ?? 'smooth'} onChange={(event) => onElement(element.id, { path_mode: event.target.value })}>
            <option value="smooth">Smooth curve</option><option value="sharp">Sharp breaks</option>
          </select></label>
          <CommitInput label="Line weight" type="number" min={0.12} max={0.8} value={element.stroke_width ?? 0.26} onCommit={(value) => onElement(element.id, { stroke_width: Math.max(0.12, Math.min(0.8, Number(value))) })} />
          <label className="inspector-field"><span>Line cap</span><select value={element.line_cap ?? 'round'} onChange={(event) => onElement(element.id, { line_cap: event.target.value })}>
            {['round', 'square', 'butt'].map((cap) => <option value={cap} key={cap}>{cap}</option>)}
          </select></label>
        </div>
        <CommitInput label="Coaching assignment" value={element.assignment ?? element.responsibility ?? element.note} onCommit={(value) => onElement(element.id, { assignment: value })} />
        {element.kind === 'route' ? <fieldset className="route-collision-editor">
          <legend>Route corridor review</legend>
          <p>{collisionPairs.length ? `${collisionPairs.length} route corridor${collisionPairs.length === 1 ? '' : 's'} need review in the active timing window.` : 'No route corridor conflicts found in the active timing window.'}</p>
          <label className="inspector-field"><span>Crossing intent</span><select value={element.collision_intent ?? 'review'} onChange={(event) => onElement(element.id, { collision_intent: event.target.value })}><option value="review">Needs review</option><option value="intentional">Intentional crossing</option><option value="avoid">Avoid crossing</option></select></label>
          <CommitInput label="Clearance corridor (yd)" type="number" min={0.25} max={10} value={element.collision_corridor_yards ?? 1.5} onCommit={(value) => onElement(element.id, { collision_corridor_yards: Math.max(0.25, Math.min(10, Number(value))) })} />
          <CommitInput label="Crossing explanation" value={element.collision_note} onCommit={(value) => onElement(element.id, { collision_note: value })} />
          {collisionPairs.map((pair) => <small key={`${pair.firstId}-${pair.secondId}`} className={pair.intentional ? 'route-collision-note is-intentional' : 'route-collision-note'}>{pair.explanation}</small>)}
        </fieldset> : null}
        <Suspense fallback={<div className="assignment-fields-loading">Loading structured assignment controls…</div>}>
          <AssignmentGraphFields design={design} element={element} onElement={onElement} />
        </Suspense>
        <CommitInput label="Visibility" value={element.visibility ?? 'shared'} onCommit={(value) => onElement(element.id, { visibility: value })} />
      </div>
      <div className="inspector-object-meta">
        <span>{element.points?.length ?? element.path?.length ?? 0} handles</span>
        <span>{(element.depends_on ?? []).length} dependencies</span>
        <span>{element.asset_id ? 'Registry linked' : 'Custom assignment'}</span>
      </div>
    </InspectorSection>
  );
}

function ExchangePairAuthoring({ elements, onElement }: { elements: [PlayElement, PlayElement] | PlayElement[]; onElement: (id: string, patch: Partial<PlayElement>) => void }) {
  const [role, setRole] = useState<string>(elements[0].exchange_role ?? 'penetrate_loop');
  const [vacatedZone, setVacatedZone] = useState<string>(elements[0].gap_owner ?? elements[0].zone ?? '');
  const [replacementZone, setReplacementZone] = useState<string>(elements[1].rotation_to_zone ?? elements[1].zone ?? '');
  const [first, second] = elements;
  return <InspectorSection title="Create defensive exchange">
    <p className="inspector-help">Two defensive assignments are selected. Choose the relationship and create both reciprocal responsibilities together.</p>
    <div className="exchange-pair-preview"><strong>{first.player_id ?? first.type ?? first.id}</strong><span>↔</span><strong>{second.player_id ?? second.type ?? second.id}</strong></div>
    <label className="inspector-field"><span>Exchange relationship</span><select value={role} onChange={(event) => setRole(event.target.value)}>{DEFENSIVE_EXCHANGE_ROLES.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <label className="inspector-field"><span>Vacated gap / zone</span><select value={vacatedZone} onChange={(event) => setVacatedZone(event.target.value)}><option value="">Not specified</option>{DEFENSIVE_GAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label className="inspector-field"><span>Replacement zone</span><select value={replacementZone} onChange={(event) => setReplacementZone(event.target.value)}><option value="">Not specified</option>{DEFENSIVE_GAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    </div>
    <div className="exchange-pair-actions"><button className="button button--secondary" type="button" onClick={() => defensiveExchangePairPatch(first.id, second.id, role, { vacated_zone: vacatedZone || undefined, replacement_zone: replacementZone || undefined }).forEach(([id, patch]) => onElement(id, patch))}>{first.exchange_with === second.id && second.exchange_with === first.id ? 'Update reciprocal exchange' : 'Create reciprocal exchange'}</button>{first.exchange_with === second.id && second.exchange_with === first.id ? <button className="button button--ghost" type="button" onClick={() => clearDefensiveExchangePairPatch(first.id, second.id).forEach(([id, patch]) => onElement(id, patch))}>Clear exchange</button> : null}</div>
  </InspectorSection>;
}

function LayersPanel({ design, selected, onSelect, onPlayer, onElement }: Pick<InspectorProps, 'design' | 'selected' | 'onSelect' | 'onPlayer' | 'onElement'>) {
  return (
    <div className="layer-stack">
      <InspectorSection title={`Players · ${(design.players ?? []).length}`}>
        <div className="layer-list">
          {(design.players ?? []).map((player) => (
            <div className={selected.some((item) => item.kind === 'player' && item.id === player.id) ? 'layer-row is-selected' : 'layer-row'} key={player.id}>
              <button type="button" className="layer-row__name" onClick={() => onSelect({ kind: 'player', id: player.id })}><span className={`layer-swatch layer-swatch--${design.unit}`} />{player.position ?? player.id}</button>
              <button type="button" aria-label={`${player.hidden ? 'Show' : 'Hide'} ${player.position ?? player.id}`} onClick={() => onPlayer(player.id, { hidden: !player.hidden })}>{player.hidden ? <EyeOff size={14} /> : <Eye size={14} />}</button>
              <button type="button" aria-label={`${player.locked ? 'Unlock' : 'Lock'} ${player.position ?? player.id}`} onClick={() => onPlayer(player.id, { locked: !player.locked })}>{player.locked ? <Lock size={14} /> : <Unlock size={14} />}</button>
            </div>
          ))}
        </div>
      </InspectorSection>
      <InspectorSection title={`Assignments · ${(design.elements ?? []).length}`}>
        <div className="layer-list">
          {(design.elements ?? []).map((element) => (
            <div className={selected.some((item) => item.kind === 'element' && item.id === element.id) ? 'layer-row is-selected' : 'layer-row'} key={element.id}>
              <button type="button" className="layer-row__name" onClick={() => onSelect({ kind: 'element', id: element.id })}><span className={`layer-line layer-line--${element.kind}`} />{element.type ?? element.kind}</button>
              <button type="button" aria-label={`${element.hidden ? 'Show' : 'Hide'} ${element.type ?? element.kind}`} onClick={() => onElement(element.id, { hidden: !element.hidden })}>{element.hidden ? <EyeOff size={14} /> : <Eye size={14} />}</button>
              <button type="button" aria-label={`${element.locked ? 'Unlock' : 'Lock'} ${element.type ?? element.kind}`} onClick={() => onElement(element.id, { locked: !element.locked })}>{element.locked ? <Lock size={14} /> : <Unlock size={14} />}</button>
            </div>
          ))}
        </div>
      </InspectorSection>
    </div>
  );
}

function ValidationPanel({ design, legality, validationPending, validationError, onSelect, onTab }: Pick<InspectorProps, 'design' | 'legality' | 'validationPending' | 'validationError' | 'onSelect' | 'onTab'>) {
  const report = legality ?? { status: design.validation?.status ?? 'not_checked', issues: design.validation?.issues ?? [] };
  const localIssues = defensiveResponsibilityIssues(design);
  const issueKeys = new Set(report.issues.map((issue) => `${issue.code ?? ''}:${issue.path ?? ''}`));
  const issues = [...report.issues, ...localIssues.filter((issue) => !issueKeys.has(`${issue.code ?? ''}:${issue.path ?? ''}`))];
  const blocking = issues.filter((issue) => issue.severity === 'error').length;
  const draftReport = legality && 'draft' in legality && legality.draft === true ? legality as PlayDraftValidationReport : undefined;
  const locate = (path?: string) => {
    if (!path) return;
    const elementIndex = /^elements\[(\d+)\]/.exec(path);
    const playerIndex = /^players\[(\d+)\]/.exec(path);
    const element = elementIndex ? design.elements?.[Number(elementIndex[1])] : undefined;
    const player = playerIndex ? design.players?.[Number(playerIndex[1])] : undefined;
    if (element) onSelect({ kind: 'element', id: element.id });
    if (player) onSelect({ kind: 'player', id: player.id });
    if (element || player) onTab('inspect');
  };
  return (
    <div className="validation-panel" aria-live="polite">
      <div className={`validation-hero validation-hero--${report.status}`}>
        {blocking ? <AlertTriangle size={24} /> : <ShieldCheck size={24} />}
        <div><strong>{blocking ? `${blocking} blocking finding${blocking === 1 ? '' : 's'}` : 'Call is structurally clean'}</strong><span>{legality?.profile?.label ?? design.rule_profile?.toUpperCase() ?? 'NFL'} rule profile · explainable server checks</span></div>
      </div>
      <div className="validation-source-line"><span>{validationPending ? 'Checking current draft…' : draftReport ? 'Live unsaved draft checked' : 'Saved server revision'}</span><small>{legality?.profile?.label ?? design.rule_profile?.toUpperCase() ?? 'NFL'} rules</small></div>
      {validationError ? <div className="review-warning"><AlertTriangle size={15} /> Live draft checks are temporarily unavailable: {validationError}</div> : null}
      {draftReport ? <div className="validation-graph-summary">
        <span><strong>{draftReport.assignment_graph.summary.node_count}</strong> assignment nodes</span>
        <span><strong>{draftReport.assignment_graph.summary.edge_count}</strong> relationships</span>
        <span><strong>{draftReport.assignment_graph.summary.warning_count}</strong> graph warnings</span>
        <small>Draft {draftReport.draft_checksum.slice(0, 12)}</small>
      </div> : null}
      {!issues.length ? <div className="validation-empty"><CheckCircle2 size={18} /> No current legality or assignment conflicts.</div> : null}
      <div className="validation-findings">
        {issues.map((issue, index) => (
          <article key={`${issue.code ?? 'finding'}-${index}`} className={`validation-finding validation-finding--${issue.severity ?? 'warning'}`}>
            <header><strong>{issue.code ?? 'VALIDATION'}</strong><span>{issue.status === 'overridden' ? 'Approved override' : issue.severity ?? 'warning'}</span></header>
            <p>{issue.message ?? issue.explanation ?? 'Review this assignment.'}</p>
            {issue.suggestion ? <p className="validation-suggestion"><strong>Suggested action:</strong> {issue.suggestion}</p> : null}
            {issue.path ? <small>{issue.path}</small> : null}
            {issue.path && /^(elements|players)\[\d+\]/.test(issue.path) ? <button type="button" className="validation-locate" onClick={() => locate(issue.path)}>Locate on canvas</button> : null}
            {issue.source?.uri ? <a href={issue.source.uri} target="_blank" rel="noreferrer">{issue.source.title ?? 'Authoritative source'}</a> : null}
          </article>
        ))}
      </div>
      <p className="inspector-help">Exceptions remain finding-specific and require evidence plus program-owner approval in the controlled legality workflow.</p>
    </div>
  );
}

function ReviewPanel({
  design,
  dirty,
  versions,
  comments,
  selected,
  actionBusy,
  actionMessage,
  versionDiff,
  compareBaseId,
  compareSnapshotId,
  compareVisible,
  mergeConflict,
  onComment,
  onRequestReview,
  onPublish,
  onBranch,
  onCompare,
  onToggleCompare,
  onMerge,
}: Pick<InspectorProps, 'design' | 'dirty' | 'versions' | 'versionDiff' | 'compareBaseId' | 'compareSnapshotId' | 'compareVisible' | 'mergeConflict' | 'comments' | 'selected' | 'actionBusy' | 'actionMessage' | 'onComment' | 'onRequestReview' | 'onPublish' | 'onBranch' | 'onCompare' | 'onToggleCompare' | 'onMerge'>) {
  const [comment, setComment] = useState('');
  const [decisionRef, setDecisionRef] = useState('');
  const [branchId, setBranchId] = useState('');
  const [mergeBranchId, setMergeBranchId] = useState('');
  const selectedElementId = selected.length === 1 && selected[0].kind === 'element' ? selected[0].id : undefined;
  const submitComment = () => {
    const value = comment.trim();
    if (!value) return;
    onComment(value, selectedElementId);
    setComment('');
  };
  return (
    <div className="review-panel">
      {dirty ? <div className="review-warning"><AlertTriangle size={15} /> Save changes before starting a controlled review action.</div> : null}
      {actionMessage ? <p className="review-action-message" role="status">{actionMessage}</p> : null}
      <InspectorSection title="Review control">
        <div className="inspector-form">
          <label className="inspector-field"><span>Decision reference</span><input value={decisionRef} onChange={(event) => setDecisionRef(event.target.value)} placeholder="DEC-PLAY-…" /></label>
          <div className="review-actions">
            <button type="button" disabled={dirty || actionBusy || !decisionRef.trim()} onClick={() => onRequestReview(decisionRef.trim())}><Send size={14} /> Request review</button>
            <button type="button" disabled={dirty || actionBusy || !decisionRef.trim()} onClick={() => onPublish(decisionRef.trim())}><ShieldCheck size={14} /> Publish</button>
          </div>
          <label className="inspector-field"><span>New branch ID</span><input value={branchId} onChange={(event) => setBranchId(event.target.value)} placeholder={`${design.id}-BRANCH-…`} /></label>
          <button className="review-branch-button" type="button" disabled={dirty || actionBusy} onClick={() => onBranch(branchId.trim() || `${design.id}-BRANCH-${Date.now().toString(36).toUpperCase()}`)}><GitBranch size={14} /> Create branch</button>
        </div>
      </InspectorSection>
      <InspectorSection title="Branch merge control">
        <p className="inspector-help">Merge a reviewed branch into this target only after the server confirms its immutable merge base and expected revision.</p>
        <label className="inspector-field"><span>Branch ID to merge</span><input value={mergeBranchId} onChange={(event) => setMergeBranchId(event.target.value)} placeholder="Existing branch ID" /></label>
        <button className="review-branch-button" type="button" disabled={dirty || actionBusy || !mergeBranchId.trim()} onClick={() => onMerge(mergeBranchId.trim())}><GitCompareArrows size={14} /> Guarded merge</button>
          {mergeConflict?.status === 'conflict' ? <div className="merge-conflict-card review-warning" role="alert"><strong>Merge paused for human resolution</strong><span>{mergeConflict.conflicts?.length ?? 0} conflict path{mergeConflict.conflicts?.length === 1 ? '' : 's'} found. Review each branch change before retrying.</span>{mergeConflict.conflicts?.slice(0, 6).map((item, index) => <details className="merge-conflict-card__item" key={`${item.path ?? 'conflict'}-${index}`}><summary><code>{item.path ?? 'unidentified path'}</code></summary><div className="merge-conflict-card__values"><span><strong>Base</strong>{reviewValue(item.base)}</span><span><strong>Target</strong>{reviewValue(item.target)}</span><span><strong>Branch</strong>{reviewValue(item.branch)}</span>{item.message ? <small>{item.message}</small> : null}</div></details>)}</div> : null}
      </InspectorSection>
      <InspectorSection title={`Comments · ${comments.length}`}>
        <label className="comment-composer"><span className="sr-only">Add review comment</span><textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={3} placeholder={selectedElementId ? 'Comment on the selected assignment…' : 'Add a staff review note…'} /><button type="button" disabled={!comment.trim() || actionBusy} onClick={submitComment}><Send size={14} /> Send</button></label>
        <div className="comment-list">
          {!comments.length ? <div className="comment-empty"><MessageSquare size={18} /> No staff comments yet.</div> : null}
          {comments.map((item) => (
            <article key={item.id}><header><strong>{item.created_by ?? item.actor ?? 'Staff'}</strong><span>{item.status ?? 'open'}</span></header><p>{item.text}</p>{item.element_id ? <small>Linked to {item.element_id}</small> : null}</article>
          ))}
        </div>
      </InspectorSection>
      <InspectorSection title={`Immutable history · ${versions?.snapshots.length ?? 0}`}>
        <div className="version-list">
          {[...(versions?.snapshots ?? [])].reverse().slice(0, 8).map((snapshot) => (
            <article key={snapshot.id}><span><History size={14} /></span><div><strong>v{snapshot.version ?? '0.1.0'} · {snapshot.source ?? 'save'}</strong><small>{snapshot.checksum?.slice(0, 12) ?? snapshot.id}</small></div></article>
          ))}
          {!versions?.snapshots.length ? <div className="comment-empty"><History size={18} /> Save the design to create its first immutable snapshot.</div> : null}
        </div>
      </InspectorSection>
      <InspectorSection title="Visual version comparison">
        <p className="inspector-help">Compare two immutable snapshots to see which metadata, players, assignments, and timeline cues changed.</p>
        <div className="inspector-form inspector-form--two inspector-form--nested">
          <label className="inspector-field"><span>Base snapshot</span><select value={compareBaseId ?? ''} onChange={(event) => onCompare(event.target.value, compareSnapshotId ?? '')}>
            <option value="">Select base</option>
            {(versions?.snapshots ?? []).map((snapshot) => <option value={snapshot.id} key={snapshot.id}>v{snapshot.version ?? '?'} · {snapshot.id.slice(0, 12)}</option>)}
          </select></label>
          <label className="inspector-field"><span>Compare snapshot</span><select value={compareSnapshotId ?? ''} onChange={(event) => onCompare(compareBaseId ?? '', event.target.value)}>
            <option value="">Select compare</option>
            {(versions?.snapshots ?? []).map((snapshot) => <option value={snapshot.id} key={snapshot.id}>v{snapshot.version ?? '?'} · {snapshot.id.slice(0, 12)}</option>)}
          </select></label>
        </div>
        <button className="review-branch-button" type="button" disabled={!compareBaseId || !compareSnapshotId || compareBaseId === compareSnapshotId || actionBusy} onClick={() => onCompare(compareBaseId ?? '', compareSnapshotId ?? '')}><GitCompareArrows size={14} /> Refresh comparison</button>
        {versionDiff ? (
          <div className="version-diff-card version-list" aria-live="polite">
            <header><strong>v{versionDiff.base_version ?? '?'} → v{versionDiff.compare_version ?? '?'}</strong><span>{versionDiff.diff.timeline_changed ? 'Timeline changed' : 'Timeline unchanged'}</span></header>
            <div className="version-diff-metrics version-list">
              <span><strong>{versionDiff.diff.changed_fields.length}</strong> metadata</span>
              <span><strong>{versionDiff.diff.players.changed.length}</strong> player edits</span>
              <span><strong>{versionDiff.diff.elements.changed.length}</strong> assignment edits</span>
              <span><strong>{versionDiff.diff.elements.added.length + versionDiff.diff.elements.removed.length}</strong> assignment adds/removes</span>
            </div>
            {versionDiff.compare_design ? <button className="review-branch-button version-diff-toggle" type="button" aria-pressed={Boolean(compareVisible)} onClick={() => onToggleCompare?.(!compareVisible)}><span>{compareVisible ? <EyeOff size={14} /> : <Eye size={14} />}</span>{compareVisible ? 'Hide field overlay' : 'Show field overlay'}</button> : null}
            {versionDiff.diff.changed_fields.length ? <p className="version-diff-fields inspector-help"><strong>Changed fields:</strong> {versionDiff.diff.changed_fields.join(', ')}</p> : <p className="version-diff-fields inspector-help">No top-level metadata changed.</p>}
            {versionDiff.diff.elements.changed.length ? <div className="version-diff-list comment-list"><strong>Changed assignments</strong>{versionDiff.diff.elements.changed.slice(0, 8).map((item) => <span key={item.id}><code>{item.id}</code> {item.fields.join(', ')}</span>)}</div> : null}
            {versionDiff.diff.players.added.length || versionDiff.diff.players.removed.length ? <p className="version-diff-fields inspector-help"><strong>Personnel:</strong> +{versionDiff.diff.players.added.length} added · −{versionDiff.diff.players.removed.length} removed</p> : null}
          </div>
        ) : <div className="comment-empty"><GitCompareArrows size={18} /> Choose two different snapshots to inspect changes.</div>}
      </InspectorSection>
    </div>
  );
}

export function DesignerInspector(props: InspectorProps) {
  const guidance = TAB_GUIDANCE[props.tab];
  return (
    <aside className="designer-inspector" aria-label="Play inspector" data-tutorial={props.tab === 'review' ? 'review' : 'inspector'}>
      <div className="inspector-tabs" role="tablist" aria-label="Designer panels">
        <button type="button" role="tab" aria-selected={props.tab === 'inspect'} className={props.tab === 'inspect' ? 'is-active' : ''} onClick={() => props.onTab('inspect')}><SlidersHorizontal size={15} /><span>Inspect</span></button>
        <button type="button" role="tab" aria-selected={props.tab === 'layers'} className={props.tab === 'layers' ? 'is-active' : ''} onClick={() => props.onTab('layers')}><Layers3 size={15} /><span>Layers</span></button>
        <button type="button" role="tab" aria-selected={props.tab === 'validate'} className={props.tab === 'validate' ? 'is-active' : ''} onClick={() => props.onTab('validate')}><ShieldCheck size={15} /><span>Checks</span></button>
        <button type="button" role="tab" aria-selected={props.tab === 'review'} className={props.tab === 'review' ? 'is-active' : ''} onClick={() => props.onTab('review')}><MessageSquare size={15} /><span>Review</span></button>
      </div>
      <div className="inspector-scroll">
        <DesignerSectionGuide title={guidance.title} description={guidance.description} />
        {props.tab === 'inspect' ? (
          <>
            <InspectorSection title="Play identity">
              <div className="inspector-form">
                <CommitInput label="Play name" value={props.design.name ?? props.design.concept} onCommit={(value) => props.onMeta({ name: value, concept: value })} />
                <div className="inspector-form inspector-form--two inspector-form--nested">
                  <CommitInput label="Personnel" value={props.design.personnel} onCommit={(value) => props.onMeta({ personnel: value })} />
                  <CommitInput label="Formation" value={props.design.formation} onCommit={(value) => props.onMeta({ formation: value })} />
                </div>
                {props.design.unit === 'defense' ? <>
                  <div className="inspector-form inspector-form--two inspector-form--nested"><CommitInput label="Front" value={props.design.front} onCommit={(value) => props.onMeta({ front: value })} /><CommitInput label="Coverage family" value={props.design.coverage} onCommit={(value) => props.onMeta({ coverage: value })} /></div>
                  <fieldset className="coverage-shell-editor">
                    <legend>Coverage shell</legend>
                    <p>Author the spatial shell first; Checks will flag any zone that has no assignment owner.</p>
                    <CoverageShellEditor zones={props.design.coverage_zones ?? []} onChange={(zones) => props.onMeta({ coverage_zones: zones })} />
                    <div className="coverage-shell-grid">
                      {COVERAGE_ZONE_OPTIONS.map(([value, label]) => <label key={value}><input type="checkbox" checked={(props.design.coverage_zones ?? []).includes(value)} onChange={(event) => {
                        const zones = event.target.checked ? [...new Set([...(props.design.coverage_zones ?? []), value])] : (props.design.coverage_zones ?? []).filter((zone) => zone !== value);
                        props.onMeta({ coverage_zones: zones });
                      }} /><span>{label}</span></label>)}
                    </div>
                  </fieldset>
                </> : null}
                <label className="inspector-field"><span>Rule profile</span><select value={props.design.rule_profile ?? 'nfl'} onChange={(event) => props.onMeta({ rule_profile: event.target.value })}>{RULE_PROFILES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
              </div>
            </InspectorSection>
            <InspectorSection title="Field and alignment">
              <div className="inspector-form">
                <div className="inspector-form inspector-form--two inspector-form--nested">
                  <label className="inspector-field"><span>Ball hash</span><select value={props.design.field_context?.hash ?? 'middle'} onChange={(event) => {
                    const hash = event.target.value;
                    const currentX = Number(props.design.field_context?.ball_x ?? 50);
                    const targetX = HASH_X[hash] ?? 50;
                    props.onFieldContext({ hash, ball_x: targetX }, { x: targetX - currentX, y: 0 });
                  }}><option value="left">Left hash</option><option value="middle">Middle</option><option value="right">Right hash</option></select></label>
                  <CommitInput label="Line of scrimmage" type="number" min={0} max={53} value={props.design.field_context?.line_of_scrimmage_y ?? 26.5} onCommit={(value) => {
                    const currentY = Number(props.design.field_context?.line_of_scrimmage_y ?? 26.5);
                    const targetY = Math.max(0, Math.min(53, Number(value)));
                    props.onFieldContext({ line_of_scrimmage_y: targetY, ball_y: targetY }, { x: 0, y: targetY - currentY });
                  }} />
                </div>
                <div className="inspector-form inspector-form--two inspector-form--nested">
                  <label className="inspector-field"><span>Formation strength</span><select value={props.design.field_context?.strength ?? 'balanced'} onChange={(event) => props.onFieldContext({ strength: event.target.value })}><option value="balanced">Balanced</option><option value="left">Left</option><option value="right">Right</option></select></label>
                  <label className="inspector-field"><span>Play direction</span><select value={props.design.field_context?.direction ?? 'right'} onChange={(event) => props.onFieldContext({ direction: event.target.value })}><option value="left">Left</option><option value="right">Right</option></select></label>
                </div>
                <label className="inspector-field"><span>Field zone</span><select value={props.design.field_context?.field_zone ?? 'open_field'} onChange={(event) => props.onFieldContext({ field_zone: event.target.value })}><option value="backed_up">Backed up</option><option value="open_field">Open field</option><option value="plus_territory">Plus territory</option><option value="high_red_zone">High red zone</option><option value="low_red_zone">Low red zone</option><option value="goal_line">Goal line</option></select></label>
              </div>
              <p className="inspector-help">Hash and line changes translate every unlocked player and assignment together. Locked objects stay fixed for deliberate exceptions.</p>
            </InspectorSection>
            {props.design.unit === 'defense' ? <DefensiveFrontMap design={props.design} onSelect={props.onSelect} /> : null}
            {props.design.unit === 'defense' ? <RotationSequencePanel design={props.design} onSelect={props.onSelect} /> : null}
            <SelectionInspector {...props} />
          </>
        ) : null}
        {props.tab === 'layers' ? <LayersPanel {...props} /> : null}
        {props.tab === 'validate' ? <ValidationPanel {...props} /> : null}
        {props.tab === 'review' ? <ReviewPanel {...props} /> : null}
      </div>
    </aside>
  );
}
