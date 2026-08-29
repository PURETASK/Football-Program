import { lazy, Suspense, useState, type KeyboardEvent, type ReactNode } from 'react';
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ChevronsDown,
  ChevronsUp,
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
  Users,
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
  PlayPositionOptions,
  PlayPlayer,
  PlayRuleProfile,
  PlayPreSnapStep,
  PlayTemplate,
  PlayMergeResult,
  PlayVersionHistory,
  Point,
} from '../types';
import type { EditorSelection } from './editorState';
import { DesignerSectionGuide } from './DesignerSectionGuide';
import { AssignmentGraphFields } from './AssignmentGraphFields';
import { PositionToolkit } from './PositionToolkit';
import { DEFENSIVE_GAP_OPTIONS, defensiveGapOwners, defensiveGapSummary } from './defensiveFront';
import { routeCollisions } from './geometry';
import { DEFENSIVE_ALIGNMENTS, DEFENSIVE_TECHNIQUES, defensiveAlignmentIssues, defensiveAlignmentLabel, defensiveAlignmentPatch } from './defensiveAlignment';
import { CoverageShellEditor } from './CoverageShellEditor';
import { coverageShellOwners } from './coverageShell';
import { rotationLabel } from './rotationSequencing';
import { DEFENSIVE_EXCHANGE_PRESETS, DEFENSIVE_EXCHANGE_ROLES, clearDefensiveExchangePairPatch, defensiveExchangePairPatch, defensiveExchangePresetPatch, defensiveExchangePresetCompatibility, exchangeConceptPatch } from './defensiveExchanges';
import { defensiveResponsibilityIssues } from './defensiveResponsibilityValidation';
import { offensiveBlockingIssues } from './offensiveBlocking';
import { timelineIntegrityIssues } from './timelineValidation';

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
  onSelectGroup?: (groupId: string) => void;
  onMeta: (patch: Partial<PlayDesign>) => void;
  onFieldContext: (patch: Partial<PlayFieldContext>, translate?: Point) => void;
  onPlayer: (id: string, patch: Partial<PlayPlayer>) => void;
  onElement: (id: string, patch: Partial<PlayElement>) => void;
  onReorderElement?: (id: string, direction: 'up' | 'down' | 'front' | 'back') => void;
  onComment: (text: string, elementId?: string) => void;
  onRequestReview: (decisionRef: string) => void;
  onPublish: (decisionRef: string) => void;
  onBranch: (branchId: string) => void;
  onCompare: (baseSnapshotId: string, compareSnapshotId: string) => void;
  onToggleCompare?: (visible: boolean) => void;
  onMerge: (branchId: string) => void;
  onRequestLegalityOverride?: (values: { issueCode: string; rationale: string; decisionRef: string; evidenceRefs: string[]; expiresAt: string }) => void;
  onApproveLegalityOverride?: (values: { overrideId: string; decisionRef: string }) => void;
  canApproveLegalityOverride?: boolean;
  assets?: PlayAsset[];
  templates?: PlayTemplate[];
  positionOptions?: PlayPositionOptions;
  onChooseAsset?: (asset: PlayAsset) => void;
  onApplyTemplate?: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onMaterializeAsset?: (asset: PlayAsset) => void;
  ruleProfiles?: PlayRuleProfile[];
}

const FALLBACK_RULE_PROFILES: PlayRuleProfile[] = [
  { id: 'nfl', label: 'NFL' }, { id: 'ncaa', label: 'NCAA' }, { id: 'high_school', label: 'High school', requires_local_rules: true }, { id: 'youth', label: 'Youth', requires_local_rules: true }, { id: 'flag', label: 'Flag', requires_local_rules: true },
];

const HASH_X: Record<string, number> = { left: 38, middle: 50, right: 62 };
const COVERAGE_ZONE_OPTIONS = [
  ['deep_left', 'Deep left'], ['deep_middle', 'Deep middle'], ['deep_right', 'Deep right'],
  ['deep_half_left', 'Deep half left'], ['deep_half_right', 'Deep half right'],
  ['flat_left', 'Flat left'], ['flat_right', 'Flat right'],
  ['hook_curl_left', 'Hook/curl left'], ['hook_curl_middle', 'Hook/curl middle'], ['hook_curl_right', 'Hook/curl right'],
  ['robber', 'Robber / low hole'], ['man', 'Man coverage'], ['bracket', 'Bracket / double'],
] as const;

function PreSnapSequenceEditor({ design, onMeta }: { design: PlayDesign; onMeta: (patch: Partial<PlayDesign>) => void }) {
  const sequence = design.pre_snap_sequence ?? [];
  const update = (id: string, patch: Partial<PlayPreSnapStep>) => onMeta({ pre_snap_sequence: sequence.map((step) => step.id === id ? { ...step, ...patch } : step) });
  const add = () => onMeta({ pre_snap_sequence: [...sequence, { id: `PRE-${Date.now().toString(36).toUpperCase()}`, kind: 'set', label: 'Set and communicate', start_ms: -900, end_ms: -250 }] });
  const remove = (id: string) => onMeta({ pre_snap_sequence: sequence.filter((step) => step.id !== id) });
  return <fieldset className="pre-snap-sequence-editor">
    <legend>Pre-snap sequence</legend>
    <p className="inspector-help">Author the ordered huddle, shift, motion, set, and cadence steps before the snap. These steps remain separate from post-snap assignment timing.</p>
    <div className="pre-snap-sequence" role="list" aria-label="Pre-snap sequence steps">
      {sequence.map((step, index) => <div className="pre-snap-step" role="listitem" key={step.id}>
        <span className="pre-snap-step__index">{index + 1}</span>
        <div className="pre-snap-step__fields">
          <label className="inspector-field"><span>Step type</span><select aria-label={`Step ${index + 1} type`} value={step.kind} onChange={(event) => update(step.id, { kind: event.target.value })}>{['huddle', 'shift', 'motion', 'set', 'cadence'].map((kind) => <option value={kind} key={kind}>{kind}</option>)}</select></label>
          <label className="inspector-field"><span>Label</span><input aria-label={`Step ${index + 1} label`} value={step.label} onChange={(event) => update(step.id, { label: event.target.value })} /></label>
          <div className="inspector-form inspector-form--two inspector-form--nested">
            <label className="inspector-field"><span>Start (ms)</span><input aria-label={`Step ${index + 1} start`} type="number" value={step.start_ms} onChange={(event) => update(step.id, { start_ms: Number(event.target.value) })} /></label>
            <label className="inspector-field"><span>End (ms)</span><input aria-label={`Step ${index + 1} end`} type="number" value={step.end_ms} onChange={(event) => update(step.id, { end_ms: Number(event.target.value) })} /></label>
          </div>
          <label className="inspector-field"><span>Coaching note</span><input aria-label={`Step ${index + 1} note`} value={step.notes ?? ''} onChange={(event) => update(step.id, { notes: event.target.value })} placeholder="Communication or trigger" /></label>
        </div>
        <button className="icon-button" type="button" aria-label={`Remove pre-snap step ${index + 1}`} onClick={() => remove(step.id)}>×</button>
      </div>)}
      {!sequence.length ? <div className="comment-empty">No pre-snap steps authored. Add the first communication or movement step.</div> : null}
    </div>
    <button className="button button--secondary" type="button" onClick={add}>Add pre-snap step</button>
  </fieldset>;
}

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

function DefensiveAlignmentMap({ design, onSelect, onPlayer }: Pick<InspectorProps, 'design' | 'onSelect' | 'onPlayer'>) {
  const players = (design.players ?? []).filter((player) => Boolean(player.start));
  const [drag, setDrag] = useState<{ id: string; pointerId: number } | null>(null);
  const activate = (id: string, event: KeyboardEvent<SVGGElement>) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect({ kind: 'player', id }); }
  };
  const eventPoint = (event: { clientX: number; clientY: number; currentTarget: SVGSVGElement }): Point => {
    const bounds = event.currentTarget.getBoundingClientRect();
    return { x: Math.max(0, Math.min(100, ((event.clientX - bounds.left) / Math.max(1, bounds.width)) * 100)), y: Math.max(0, Math.min(53, ((event.clientY - bounds.top) / Math.max(1, bounds.height)) * 54)) };
  };
  return <InspectorSection title="Defensive alignment board">
    <p className="inspector-help">Drag a defender to adjust the visual front, or select one to edit technique, alignment relationship, and assignment details. The board keeps the front picture visible while you author individual players.</p>
    <svg className="defensive-alignment-board" viewBox="0 0 100 54" role="group" aria-label="Interactive defensive alignment board" onPointerMove={(event) => { if (!drag || drag.pointerId !== event.pointerId) return; onPlayer(drag.id, { start: eventPoint(event) }); }} onPointerUp={(event) => { if (drag?.pointerId === event.pointerId) setDrag(null); }} onPointerCancel={(event) => { if (drag?.pointerId === event.pointerId) setDrag(null); }}>
      <rect x="0.5" y="0.5" width="99" height="53" rx="1.5" className="defensive-alignment-board__field" />
      <line x1="0" y1="27" x2="100" y2="27" className="defensive-alignment-board__line" />
      <text x="2" y="25" className="defensive-alignment-board__label">DEFENSIVE SIDE</text>
      <text x="2" y="31" className="defensive-alignment-board__label">LINE OF SCRIMMAGE</text>
      {players.map((player) => <g key={player.id} role="button" tabIndex={0} aria-label={`${player.position ?? player.role ?? player.id}: ${defensiveAlignmentLabel(player)}`} className="defensive-alignment-board__player" transform={`translate(${player.start!.x} ${player.start!.y})`} onClick={() => { if (!drag) onSelect({ kind: 'player', id: player.id }); }} onKeyDown={(event) => activate(player.id, event)} onPointerDown={(event) => { if (player.locked || event.button !== 0) return; event.stopPropagation(); const svg = event.currentTarget.ownerSVGElement; if (!svg) return; if (typeof svg.setPointerCapture === 'function') svg.setPointerCapture(event.pointerId); setDrag({ id: player.id, pointerId: event.pointerId }); onSelect({ kind: 'player', id: player.id }); }}>
        <circle r="3.1" />
        <text y="0.9" textAnchor="middle">{player.position ?? player.role ?? player.id}</text>
        <title>{defensiveAlignmentLabel(player)}</title>
      </g>)}
    </svg>
    {!players.length ? <div className="validation-empty">Add defensive players with field coordinates to populate the alignment board.</div> : null}
  </InspectorSection>;
}

function OffensivePersonnelLegality({ design, onSelect }: Pick<InspectorProps, 'design' | 'onSelect'>) {
  const profile = String(design.rule_profile ?? 'nfl');
  if (design.unit !== 'offense') return null;
  const flaggedPlayers = ['nfl', 'ncaa'].includes(profile) ? (design.players ?? []).filter((player) => {
    const alignment = player.alignment ?? {};
    const number = typeof alignment.number === 'number' ? alignment.number : undefined;
    return alignment.eligible === true && number !== undefined && number >= 50 && number <= 79 && alignment.reported_eligible !== true;
  }) : [];
  const numberedPlayers = (design.players ?? []).filter((player) => typeof player.alignment?.number === 'number');
  const duplicateNumberGroups = [...numberedPlayers.reduce((groups, player) => {
    const number = player.alignment?.number as number;
    const group = groups.get(number) ?? [];
    group.push(player);
    groups.set(number, group);
    return groups;
  }, new Map<number, PlayPlayer[]>()).entries()].filter(([, players]) => players.length > 1);
  const profileLabel = ['nfl', 'ncaa'].includes(profile) ? (profile === 'ncaa' ? 'NCAA' : 'NFL') : profile.replace('_', ' ');
  const findingCount = flaggedPlayers.length + duplicateNumberGroups.length;
  return <InspectorSection title="Personnel legality review">
    <p className="inspector-help">{profileLabel} offensive personnel is checked across the full play for number-based eligibility and duplicate jersey assignments. Resolve review items before publishing.</p>
    {findingCount ? <div className="personnel-legality-summary personnel-legality-summary--review" role="alert" aria-label="Personnel eligibility review required">
      <strong>{findingCount} personnel finding{findingCount === 1 ? '' : 's'} require review</strong>
      {flaggedPlayers.map((player) => <button type="button" key={`eligibility-${player.id}`} onClick={() => onSelect({ kind: 'player', id: player.id })}>
        <span>{player.position ?? player.role ?? player.id}</span><small>#{player.alignment?.number} · mark reported eligible or revise eligibility/number</small>
      </button>)}
      {duplicateNumberGroups.map(([number, players]) => <button type="button" key={`duplicate-${number}`} onClick={() => onSelect({ kind: 'player', id: players[0].id })}>
        <span>Duplicate jersey number #{number}</span><small>{players.map((player) => player.position ?? player.role ?? player.id).join(' · ')} · assign unique numbers for this personnel group</small>
      </button>)}
    </div> : <div className="personnel-legality-summary personnel-legality-summary--ready" role="status"><CheckCircle2 size={16} /><span>No number-based eligibility exceptions detected.</span></div>}
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
  positionOptions,
  onChooseAsset,
  onApplyTemplate,
  onMaterializeAsset,
}: Pick<InspectorProps, 'design' | 'selected' | 'onPlayer' | 'onElement' | 'assets' | 'templates' | 'positionOptions' | 'onChooseAsset' | 'onApplyTemplate' | 'onMaterializeAsset'>) {
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
    if (design.unit === 'defense' && selectedElements.length === 2) return <ExchangePairAuthoring elements={selectedElements} players={design.players ?? []} onElement={onElement} />;
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
    const alignment = player.alignment ?? {};
    const numberBasedEligibility = design.unit === 'offense' && ['nfl', 'ncaa'].includes(String(design.rule_profile ?? 'nfl'));
    const jerseyNumber = typeof alignment.number === 'number' ? alignment.number : undefined;
    const numberEligibilityWarning = numberBasedEligibility && alignment.eligible === true && jerseyNumber !== undefined && jerseyNumber >= 50 && jerseyNumber <= 79 && alignment.reported_eligible !== true;
    const patchAlignment = (patch: Partial<NonNullable<PlayPlayer['alignment']>>) => onPlayer(player.id, { alignment: { ...alignment, ...patch } });
    return (
      <InspectorSection title="Player">
        <div className="selected-object-heading"><span><UserRound size={15} /></span><div><strong>{player.position ?? player.role ?? player.id}</strong><small>{player.id}</small></div></div>
        <div className="inspector-form inspector-form--two">
          <CommitInput label="Position" value={player.position} onCommit={(value) => onPlayer(player.id, { position: value, role: value })} />
          <CommitInput label="Label" value={player.label} onCommit={(value) => onPlayer(player.id, { label: value })} />
          <CommitInput label="Field X" type="number" min={0} max={100} value={player.start?.x} onCommit={(value) => onPlayer(player.id, { start: { x: Number(value), y: player.start?.y ?? 26 } })} />
          <CommitInput label="Field Y" type="number" min={0} max={53} value={player.start?.y} onCommit={(value) => onPlayer(player.id, { start: { x: player.start?.x ?? 50, y: Number(value) } })} />
        </div>
        <fieldset className="player-legality-editor">
          <legend>Player alignment and eligibility</legend>
          <p>Record the snap-time alignment used by the rule validator and teaching views. The server remains the authority for legality.</p>
          <div className="inspector-form inspector-form--two inspector-form--nested">
            <CommitInput label="Jersey number" type="number" min={0} max={99} value={alignment.number as number | undefined} onCommit={(value) => patchAlignment({ number: value === '' ? undefined : Number(value) })} />
            <label className="inspector-field"><span>Snap alignment</span><select value={alignment.on_line === true ? 'on_line' : alignment.on_line === false ? 'backfield' : ''} onChange={(event) => patchAlignment({ on_line: event.target.value === '' ? undefined : event.target.value === 'on_line' })}><option value="">Unspecified</option><option value="on_line">On line</option><option value="backfield">Backfield</option></select></label>
          </div>
          <label className="inspector-check"><input type="checkbox" checked={alignment.eligible === true} onChange={(event) => patchAlignment({ eligible: event.target.checked })} /><span>Eligible at snap</span></label>
          {numberBasedEligibility ? <>
            <label className="inspector-check"><input type="checkbox" checked={alignment.reported_eligible === true} onChange={(event) => patchAlignment({ reported_eligible: event.target.checked })} /><span>Reported eligible exception</span></label>
            <small className="inspector-help">NFL/NCAA numbers 50–79 require this explicit exception when the player is declared eligible.</small>
            {numberEligibilityWarning ? <div className="player-legality-warning" role="alert" aria-label="Eligibility review required"><strong>Eligibility review required</strong><span>#{jerseyNumber} is in the 50–79 range. Mark the player reported eligible or change the eligibility/number before publishing.</span></div> : null}
          </> : null}
        </fieldset>
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
          positionOptions={positionOptions}
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
          {collisionPairs.map((pair) => <small key={`${pair.firstId}-${pair.secondId}`} className={pair.intentional ? 'route-collision-note is-intentional' : 'route-collision-note'}>{pair.explanation} · Review window {`${(pair.overlapStartMs / 1000).toFixed(2)}–${(pair.overlapEndMs / 1000).toFixed(2)}s`}</small>)}
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

function ExchangePairAuthoring({ elements, players, onElement }: { elements: [PlayElement, PlayElement] | PlayElement[]; players: PlayPlayer[]; onElement: (id: string, patch: Partial<PlayElement>) => void }) {
  const [role, setRole] = useState<string>(elements[0].exchange_role ?? 'penetrate_loop');
  const [concept, setConcept] = useState<string>(typeof elements[0].exchange_concept === 'string' ? elements[0].exchange_concept : '');
  const [vacatedZone, setVacatedZone] = useState<string>(elements[0].gap_owner ?? elements[0].zone ?? '');
  const [replacementZone, setReplacementZone] = useState<string>(elements[1].rotation_to_zone ?? elements[1].zone ?? '');
  const [direction, setDirection] = useState<string>(typeof elements[0].exchange_direction === 'string' ? elements[0].exchange_direction : 'inside');
  const [penetrationLane, setPenetrationLane] = useState<string>(typeof elements[0].penetration_lane === 'string' ? elements[0].penetration_lane : '');
  const [loopLandmark, setLoopLandmark] = useState<string>(typeof elements[1].loop_landmark === 'string' ? elements[1].loop_landmark : '');
  const [first, second] = elements;
  const firstPlayer = players.find((player) => player.id === first.player_id);
  const secondPlayer = players.find((player) => player.id === second.player_id);
  const conceptFit = defensiveExchangePresetCompatibility(concept, firstPlayer, secondPlayer);
  return <InspectorSection title="Create defensive exchange">
    <p className="inspector-help">Two defensive assignments are selected. Choose the relationship and create both reciprocal responsibilities together.</p>
    <div className="exchange-pair-preview"><strong>{first.player_id ?? first.type ?? first.id}</strong><span>↔</span><strong>{second.player_id ?? second.type ?? second.id}</strong></div>
    <label className="inspector-field"><span>Named exchange concept</span><select value={concept} onChange={(event) => setConcept(event.target.value)}><option value="">Generic relationship</option>{DEFENSIVE_EXCHANGE_PRESETS.map((preset) => <option value={preset.value} key={preset.value}>{preset.label}</option>)}</select></label>
    {concept ? <p className="inspector-help">{DEFENSIVE_EXCHANGE_PRESETS.find((preset) => preset.value === concept)?.description} The concept is stored on both assignments for teaching, validation, and export.</p> : null}
    {concept && !conceptFit.compatible ? <div className="player-legality-warning exchange-compatibility-warning" role="alert" aria-label="Exchange partner compatibility review"><strong>Partner compatibility review</strong><span>{conceptFit.reasons.join(' ')}</span><small>The server will preserve this as a coach-review warning until the partner positions or concept are corrected.</small></div> : null}
    <label className="inspector-field"><span>Exchange relationship</span><select value={role} onChange={(event) => setRole(event.target.value)}>{DEFENSIVE_EXCHANGE_ROLES.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label>
    {concept ? <div className="inspector-form inspector-form--two inspector-form--nested">
      <label className="inspector-field"><span>Stunt direction</span><select value={direction} onChange={(event) => setDirection(event.target.value)}><option value="inside">Inside</option><option value="outside">Outside</option><option value="left">Left</option><option value="right">Right</option></select></label>
      <label className="inspector-field"><span>Penetration lane</span><select value={penetrationLane} onChange={(event) => setPenetrationLane(event.target.value)}><option value="">Choose lane</option>{['A', 'B', 'C', 'edge', 'contain'].map((lane) => <option value={lane} key={lane}>{lane} gap / lane</option>)}</select></label>
      <label className="inspector-field"><span>Loop landmark</span><select value={loopLandmark} onChange={(event) => setLoopLandmark(event.target.value)}><option value="">Choose landmark</option>{[['near_hip', 'Near hip'], ['far_hip', 'Far hip'], ['heels', 'Heels'], ['second_level', 'Second level'], ['replace', 'Replace vacated lane']].map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    </div> : null}
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <label className="inspector-field"><span>Vacated gap / zone</span><select value={vacatedZone} onChange={(event) => setVacatedZone(event.target.value)}><option value="">Not specified</option>{DEFENSIVE_GAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label className="inspector-field"><span>Replacement zone</span><select value={replacementZone} onChange={(event) => setReplacementZone(event.target.value)}><option value="">Not specified</option>{DEFENSIVE_GAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    </div>
    <div className="exchange-pair-actions"><button className="button button--secondary" type="button" onClick={() => {
      const pair = concept
        ? defensiveExchangePresetPatch(concept, first.id, second.id, { vacated_zone: vacatedZone || undefined, replacement_zone: replacementZone || undefined })
        : defensiveExchangePairPatch(first.id, second.id, role, { vacated_zone: vacatedZone || undefined, replacement_zone: replacementZone || undefined });
      pair.forEach(([id, patch]) => onElement(id, {
        ...patch,
        ...exchangeConceptPatch(concept),
        exchange_direction: concept ? direction : undefined,
        ...(patch.exchange_role === 'penetrate_loop' ? { penetration_lane: penetrationLane || undefined } : {}),
        ...(patch.exchange_role === 'loop_penetrate' ? { loop_landmark: loopLandmark || undefined } : {}),
      }));
    }}>{first.exchange_with === second.id && second.exchange_with === first.id ? 'Update reciprocal exchange' : 'Create reciprocal exchange'}</button>{first.exchange_with === second.id && second.exchange_with === first.id ? <button className="button button--ghost" type="button" onClick={() => clearDefensiveExchangePairPatch(first.id, second.id).forEach(([id, patch]) => onElement(id, patch))}>Clear exchange</button> : null}</div>
  </InspectorSection>;
}

function LayersPanel({ design, selected, onSelect, onSelectGroup, onPlayer, onElement, onReorderElement }: Pick<InspectorProps, 'design' | 'selected' | 'onSelect' | 'onSelectGroup' | 'onPlayer' | 'onElement' | 'onReorderElement'>) {
  return (
    <div className="layer-stack">
      <InspectorSection title={`Players · ${(design.players ?? []).length}`}>
        <div className="layer-list">
          {(design.players ?? []).map((player) => (
            <div className={selected.some((item) => item.kind === 'player' && item.id === player.id) ? 'layer-row is-selected' : 'layer-row'} key={player.id}>
              <button type="button" className="layer-row__name" onClick={() => onSelect({ kind: 'player', id: player.id })}><span className={`layer-swatch layer-swatch--${design.unit}`} />{player.position ?? player.id}</button>
              {player.group_id ? <button type="button" aria-label={`Select group ${player.group_id}`} title={`Select group ${player.group_id}`} onClick={() => onSelectGroup?.(player.group_id!)}><Users size={14} /></button> : null}
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
              {typeof element.group_id === 'string' ? <button type="button" aria-label={`Select group ${element.group_id}`} title={`Select group ${element.group_id}`} onClick={() => onSelectGroup?.(element.group_id as string)}><Users size={14} /></button> : null}
              <button type="button" aria-label={`${element.hidden ? 'Show' : 'Hide'} ${element.type ?? element.kind}`} onClick={() => onElement(element.id, { hidden: !element.hidden })}>{element.hidden ? <EyeOff size={14} /> : <Eye size={14} />}</button>
              <button type="button" aria-label={`${element.locked ? 'Unlock' : 'Lock'} ${element.type ?? element.kind}`} onClick={() => onElement(element.id, { locked: !element.locked })}>{element.locked ? <Lock size={14} /> : <Unlock size={14} />}</button>
              <button type="button" aria-label={`Bring ${element.type ?? element.kind} forward`} title="Bring forward" disabled={!onReorderElement} onClick={() => onReorderElement?.(element.id, 'up')}><ArrowUp size={14} /></button>
              <button type="button" aria-label={`Send ${element.type ?? element.kind} backward`} title="Send backward" disabled={!onReorderElement} onClick={() => onReorderElement?.(element.id, 'down')}><ArrowDown size={14} /></button>
              <button type="button" aria-label={`Bring ${element.type ?? element.kind} to front`} title="Bring to front" disabled={!onReorderElement} onClick={() => onReorderElement?.(element.id, 'front')}><ChevronsUp size={14} /></button>
              <button type="button" aria-label={`Send ${element.type ?? element.kind} to back`} title="Send to back" disabled={!onReorderElement} onClick={() => onReorderElement?.(element.id, 'back')}><ChevronsDown size={14} /></button>
            </div>
          ))}
        </div>
      </InspectorSection>
    </div>
  );
}

function ValidationPanel({ design, legality, validationPending, validationError, onSelect, onTab, onRequestLegalityOverride, onApproveLegalityOverride, canApproveLegalityOverride }: Pick<InspectorProps, 'design' | 'legality' | 'validationPending' | 'validationError' | 'onSelect' | 'onTab' | 'onRequestLegalityOverride' | 'onApproveLegalityOverride' | 'canApproveLegalityOverride'>) {
  const [overrideIssue, setOverrideIssue] = useState<string | null>(null);
  const [approvalRefs, setApprovalRefs] = useState<Record<string, string>>({});
  const report = legality ?? { status: design.validation?.status ?? 'not_checked', issues: design.validation?.issues ?? [] };
  const localIssues = [...defensiveResponsibilityIssues(design), ...offensiveBlockingIssues(design), ...timelineIntegrityIssues(design)];
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
            {issue.overrideable && issue.status !== 'overridden' && onRequestLegalityOverride ? <>
              <button type="button" className="validation-locate" aria-expanded={overrideIssue === (issue.code ?? String(index))} onClick={() => setOverrideIssue((current) => current === (issue.code ?? String(index)) ? null : (issue.code ?? String(index)))}>Request owner override</button>
              {overrideIssue === (issue.code ?? String(index)) ? <form className="legality-override-form" onSubmit={(event) => {
                event.preventDefault();
                const form = new FormData(event.currentTarget);
                onRequestLegalityOverride({ issueCode: issue.code ?? 'VALIDATION', rationale: String(form.get('rationale') || ''), decisionRef: String(form.get('decision_ref') || ''), evidenceRefs: String(form.get('evidence_refs') || '').split(',').map((value) => value.trim()).filter(Boolean), expiresAt: String(form.get('expires_at') || '') });
                setOverrideIssue(null);
              }}>
                <label htmlFor={`override-rationale-${index}`}><span>Rationale</span><textarea id={`override-rationale-${index}`} name="rationale" required placeholder="Explain the local rule context and why this exception needs owner review." /></label>
                <label htmlFor={`override-decision-${index}`}><span>Decision reference</span><input id={`override-decision-${index}`} name="decision_ref" required placeholder="DEC-LEGALITY-001" /></label>
                <label htmlFor={`override-evidence-${index}`}><span>Evidence references <small>comma separated</small></span><input id={`override-evidence-${index}`} name="evidence_refs" required placeholder="SOURCE-001, FILM-CLIP-001" /></label>
                <label htmlFor={`override-expires-${index}`}><span>Expires at <small>ISO-8601</small></span><input id={`override-expires-${index}`} name="expires_at" required type="datetime-local" /></label>
                <button className="button button--secondary" type="submit">Submit governed request</button>
              </form> : null}
            </> : null}
          </article>
        ))}
      </div>
      {legality && 'overrides' in legality && legality.overrides.some((item) => item.status === 'pending_owner_approval') ? <section className="legality-override-queue" aria-label="Pending legality override requests">
        <header><strong>Owner approval queue</strong><span>{legality.overrides.filter((item) => item.status === 'pending_owner_approval').length} pending</span></header>
        {legality.overrides.filter((item) => item.status === 'pending_owner_approval').map((item) => {
          const overrideId = String(item.id ?? '');
          return <article key={overrideId}><div><strong>{String(item.issue_code ?? 'Legality exception')}</strong><small>{String(item.rationale ?? 'No rationale recorded')}</small><small>Evidence: {Array.isArray(item.evidence_refs) ? item.evidence_refs.join(', ') : 'Not provided'}</small></div>{canApproveLegalityOverride && onApproveLegalityOverride ? <form onSubmit={(event) => { event.preventDefault(); const decisionRef = approvalRefs[overrideId]?.trim(); if (!decisionRef) return; onApproveLegalityOverride({ overrideId, decisionRef }); }}><label><span className="sr-only">Approval decision reference for {overrideId}</span><input aria-label={`Approval decision reference for ${overrideId}`} value={approvalRefs[overrideId] ?? ''} onChange={(event) => setApprovalRefs((current) => ({ ...current, [overrideId]: event.target.value }))} placeholder="APPROVAL-LEGALITY-001" required /></label><button className="button button--secondary" type="submit">Approve override</button></form> : <span className="approval-boundary">Program-owner approval required</span>}</article>;
        })}
      </section> : null}
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
            <article key={snapshot.id}><span><History size={14} /></span><div><strong>v{snapshot.version ?? '0.1.0'} · {snapshot.source ?? 'save'}</strong><small>{snapshot.checksum?.slice(0, 12) ?? snapshot.id}</small></div><em className={snapshot.integrity?.valid === false ? 'version-integrity version-integrity--invalid' : 'version-integrity'}>{snapshot.integrity?.valid === false ? 'Integrity review' : 'Verified'}</em></article>
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
  const selectedRuleProfile = String(props.design.rule_profile ?? 'nfl');
  const ruleProfiles = props.ruleProfiles?.length ? props.ruleProfiles : FALLBACK_RULE_PROFILES;
  const selectedProfileMetadata = ruleProfiles.find((profile) => profile.id === selectedRuleProfile);
  const localRuleProfile = selectedProfileMetadata?.requires_local_rules ?? ['high_school', 'youth', 'flag'].includes(selectedRuleProfile);
  const localRuleConstraints = props.design.local_rule_constraints && typeof props.design.local_rule_constraints === 'object'
    ? props.design.local_rule_constraints as Record<string, unknown>
    : {};
  const commitLocalRuleConstraint = (key: string, value: unknown) => props.onMeta({ local_rule_constraints: { ...localRuleConstraints, [key]: value } });
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
                    <CoverageShellEditor zones={props.design.coverage_zones ?? []} owners={coverageShellOwners(props.design)} onChange={(zones) => props.onMeta({ coverage_zones: zones })} />
                    <div className="coverage-shell-grid">
                      {COVERAGE_ZONE_OPTIONS.map(([value, label]) => <label key={value}><input type="checkbox" checked={(props.design.coverage_zones ?? []).includes(value)} onChange={(event) => {
                        const zones = event.target.checked ? [...new Set([...(props.design.coverage_zones ?? []), value])] : (props.design.coverage_zones ?? []).filter((zone) => zone !== value);
                        props.onMeta({ coverage_zones: zones });
                      }} /><span>{label}</span></label>)}
                    </div>
                  </fieldset>
                </> : null}
                <label className="inspector-field"><span>Rule profile</span><select value={selectedRuleProfile} onChange={(event) => props.onMeta({ rule_profile: event.target.value })}>{ruleProfiles.map((profile) => <option value={profile.id} key={profile.id}>{profile.label ?? profile.id}</option>)}</select></label>
                {selectedProfileMetadata?.source ? <p className="inspector-help rule-profile-source"><strong>Source basis:</strong> {selectedProfileMetadata.source.title ?? 'Controlled profile'}{selectedProfileMetadata.source.rule_refs?.length ? ` · ${selectedProfileMetadata.source.rule_refs.join(', ')}` : ''}</p> : null}
                {localRuleProfile ? <fieldset className="rule-profile-editor">
                  <legend>Local adoption rules</legend>
                  <p className="inspector-help">High school, youth, and flag rules vary by jurisdiction. Record the local source and explicit constraints so the validator can check this call without silently assuming a universal rulebook.</p>
                  <CommitInput label="Local rule source reference" value={props.design.local_rule_source_ref as string | undefined} onCommit={(value) => props.onMeta({ local_rule_source_ref: value })} />
                  <div className="inspector-form inspector-form--two inspector-form--nested">
                    <CommitInput label="Players on field" type="number" min={1} max={11} value={localRuleConstraints.players_on_field as number | undefined} onCommit={(value) => commitLocalRuleConstraint('players_on_field', value === '' ? null : Number(value))} />
                    <CommitInput label="Max motion at snap" type="number" min={0} max={11} value={localRuleConstraints.max_motion_at_snap as number | undefined} onCommit={(value) => commitLocalRuleConstraint('max_motion_at_snap', value === '' ? null : Number(value))} />
                  </div>
                  <label className="inspector-field"><span>Blocking/contact model</span><select value={localRuleConstraints.allow_blocking === false ? 'false' : localRuleConstraints.allow_blocking === true ? 'true' : ''} onChange={(event) => commitLocalRuleConstraint('allow_blocking', event.target.value === '' ? null : event.target.value === 'true')}><option value="">Not specified locally</option><option value="true">Blocking allowed</option><option value="false">No blocking/contact</option></select></label>
                </fieldset> : null}
              </div>
            </InspectorSection>
            <OffensivePersonnelLegality design={props.design} onSelect={props.onSelect} />
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
            <InspectorSection title="Pre-snap communication">
              <PreSnapSequenceEditor design={props.design} onMeta={props.onMeta} />
            </InspectorSection>
            {props.design.unit === 'defense' ? <DefensiveAlignmentMap design={props.design} onSelect={props.onSelect} onPlayer={props.onPlayer} /> : null}
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
