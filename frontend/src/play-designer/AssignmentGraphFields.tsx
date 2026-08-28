import type { PlayDesign, PlayElement, Point, RouteBranch } from '../types';
import { defaultTimelinePhases, elementTiming, timingPatch } from './timelineModel';
import { ANGLE_PRESETS, anglePatch, depthPatch, LANDMARK_SNAP_OPTIONS, landmarkPatch } from './geometry';
import { DEFENSIVE_PRESETS, defensivePresetPatch } from './defensivePresets';
import { DEFENSIVE_EXCHANGE_PRESETS, DEFENSIVE_EXCHANGE_ROLES, defensiveExchangePresetPatch, exchangePatch, exchangeRole, reciprocalExchangePatch, type DefensiveExchangeRole } from './defensiveExchanges';
import { DEFENSIVE_GAP_OPTIONS, gapOwnerPatch } from './defensiveFront';
import { ROTATION_TRIGGERS, rotationSequencePatch } from './rotationSequencing';
import { OFFENSIVE_BLOCKING_PRIMITIVES, PROTECTION_MODES, blockingConstructionPatch, offensiveBlockingPatch } from './offensiveBlocking';
import { ROUTE_BREAKS, ROUTE_FAMILIES, ROUTE_FINISHES, ROUTE_OPTION_RULES, routeAuthoringPatch, routeConstructionPatch } from './routeAuthoring';
import { addRouteBranch, branchStart } from './routeBranches';
import { coverageMovementPatch } from './coverageShell';

interface AssignmentGraphFieldsProps {
  design: PlayDesign;
  element: PlayElement;
  onElement: (id: string, patch: Partial<PlayElement>) => void;
}

function CommitInput({ label, value, type = 'text', min, max, onCommit }: { label: string; value: string | number | undefined; type?: 'text' | 'number'; min?: number; max?: number; onCommit: (value: string) => void }) {
  const stringValue = value === undefined ? '' : String(value);
  return <label className="inspector-field"><span>{label}</span><input key={stringValue} type={type} min={min} max={max} defaultValue={stringValue} onBlur={(event) => { if (event.target.value !== stringValue) onCommit(event.target.value); }} onKeyDown={(event) => { if (event.key === 'Enter') event.currentTarget.blur(); }} /></label>;
}

function RouteBranchPoints({ element, branch, onElement }: { element: PlayElement; branch: RouteBranch; onElement: (id: string, patch: Partial<PlayElement>) => void }) {
  const patchPoints = (points: Point[]) => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.map((item) => item.id === branch.id ? { ...item, points } : item) }));
  const updatePoint = (pointIndex: number, axis: keyof Point, value: string) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return;
    const point = branch.points[pointIndex];
    const nextPoint: Point = { ...point, [axis]: Math.max(axis === 'x' ? 0 : 0, Math.min(axis === 'x' ? 100 : 53, numeric)) };
    patchPoints(branch.points.map((candidate, index) => index === pointIndex ? nextPoint : candidate));
  };
  const insertPoint = (pointIndex: number) => {
    const current = branch.points[pointIndex];
    const next = branch.points[pointIndex + 1] ?? current;
    const inserted: Point = pointIndex === branch.points.length - 1
      ? { x: Math.max(0, Math.min(100, current.x + (current.x - (branch.points[pointIndex - 1]?.x ?? current.x)) / 2)), y: Math.max(0, Math.min(53, current.y + (current.y - (branch.points[pointIndex - 1]?.y ?? current.y)) / 2)) }
      : { x: (current.x + next.x) / 2, y: (current.y + next.y) / 2 };
    patchPoints([...branch.points.slice(0, pointIndex + 1), inserted, ...branch.points.slice(pointIndex + 1)]);
  };
  const removePoint = (pointIndex: number) => {
    if (branch.points.length <= 2) return;
    patchPoints(branch.points.filter((_, index) => index !== pointIndex));
  };
  return <details className="route-branch-points">
    <summary>Precise path geometry · {branch.points.length} handles</summary>
    <p>Use the canvas handles for direct manipulation or edit exact field coordinates here.</p>
    <div className="route-branch-points__grid">
      {branch.points.map((point, pointIndex) => <div className="route-branch-point" key={`${branch.id}-${pointIndex}`}>
        <strong>Handle {pointIndex + 1}</strong>
        <CommitInput label={`Path ${branch.label} handle ${pointIndex + 1} X`} type="number" min={0} max={100} value={point.x} onCommit={(value) => updatePoint(pointIndex, 'x', value)} />
        <CommitInput label={`Path ${branch.label} handle ${pointIndex + 1} Y`} type="number" min={0} max={53} value={point.y} onCommit={(value) => updatePoint(pointIndex, 'y', value)} />
        <div className="route-branch-point__actions"><button type="button" onClick={() => insertPoint(pointIndex)}>Insert after</button><button type="button" disabled={branch.points.length <= 2} onClick={() => removePoint(pointIndex)}>Remove</button></div>
      </div>)}
    </div>
  </details>;
}

export function AssignmentGraphFields({ design, element, onElement }: AssignmentGraphFieldsProps) {
  const window = elementTiming(element, Number(design.timeline?.duration_ms ?? 3000));
  const phases = element.timing?.phases?.length ? element.timing.phases : defaultTimelinePhases(element.kind, window.start, window.end);
  const otherElements = (design.elements ?? []).filter((item) => item.id !== element.id);
  const updatePhase = (phaseId: string, patch: { label?: string; start_ms?: number; end_ms?: number }) => {
    onElement(element.id, { timing: { ...element.timing, start_ms: window.start, end_ms: window.end, phases: phases.map((phase) => phase.id === phaseId ? { ...phase, ...patch } : phase) } });
  };

  const isDefense = design.unit === 'defense';
  const canExchange = isDefense && ['rush', 'stunt', 'rotation'].includes(element.kind) && otherElements.length > 0;
  const isRotation = isDefense && (element.kind === 'rotation' || Boolean(element.rotation));
  const isOffensiveBlock = design.unit === 'offense' && ['block', 'run'].includes(element.kind);
  const isRoute = ['route', 'motion'].includes(element.kind);
  const commitExchange = (partnerId: string, role: DefensiveExchangeRole | string | undefined = element.exchange_role) => {
    onElement(element.id, exchangePatch(partnerId, role));
    const partner = otherElements.find((item) => item.id === partnerId);
    if (partner) onElement(partner.id, reciprocalExchangePatch(element.id, role));
  };
  const commitExchangeRole = (role: DefensiveExchangeRole) => {
    onElement(element.id, { exchange_role: role, phase: 'exchange' });
    const partner = otherElements.find((item) => item.id === element.exchange_with);
    if (partner) onElement(partner.id, reciprocalExchangePatch(element.id, role));
  };

  return <div className="assignment-graph-fields">
    {isDefense && <div className="defensive-authoring-panel">
      <div className="defensive-authoring-panel__heading"><span><strong>Defensive responsibility preset</strong><small>Apply a coach-readable fit, coverage, pressure, stunt, or rotation starter.</small></span><span className="defensive-authoring-panel__badge">AUTHORING AID</span></div>
      <label className="inspector-field"><span>Scheme responsibility</span><select aria-label="Defensive responsibility preset" defaultValue="" onChange={(event) => { if (event.target.value) onElement(element.id, defensivePresetPatch(event.target.value)); }}>
        <option value="">Choose a responsibility preset</option>
        {(['fit', 'coverage', 'pressure', 'rotation'] as const).map((category) => <optgroup key={category} label={category[0].toUpperCase() + category.slice(1)}>{DEFENSIVE_PRESETS.filter((preset) => preset.category === category).map((preset) => <option value={preset.value} key={preset.value}>{preset.label} — {preset.description}</option>)}</optgroup>)}
      </select></label>
    </div>}
    <CommitInput label="Objective / win condition" value={element.objective} onCommit={(value) => onElement(element.id, { objective: value })} />
    {isOffensiveBlock ? <fieldset className="offensive-blocking-editor">
      <legend>Blocking and protection primitive</legend>
      <p>Choose the block behavior first, then link the defender or partner it acts on. The path stays editable on the field.</p>
      <label className="inspector-field"><span>Primitive</span><select value={element.blocking_primitive ?? ''} onChange={(event) => onElement(element.id, blockingConstructionPatch(element, design, { blocking_primitive: event.target.value || undefined }))}><option value="">Unspecified</option>{OFFENSIVE_BLOCKING_PRIMITIVES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <div className="inspector-form inspector-form--two inspector-form--nested">
        <label className="inspector-field"><span>Protection mode</span><select value={element.protection_mode ?? ''} onChange={(event) => onElement(element.id, offensiveBlockingPatch({ protection_mode: event.target.value || undefined }))}><option value="">Not specified</option>{PROTECTION_MODES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <CommitInput label="Release after (ms)" type="number" min={0} value={element.release_after_ms} onCommit={(value) => onElement(element.id, offensiveBlockingPatch({ release_after_ms: value.trim() ? Math.max(0, Number(value)) : undefined }))} />
      </div>
      <div className="inspector-form inspector-form--two inspector-form--nested">
        <label className="inspector-field"><span>Block target</span><select value={element.block_target_element_id ?? element.target_element_id ?? ''} onChange={(event) => onElement(element.id, blockingConstructionPatch(element, design, { block_target_element_id: event.target.value || undefined, target_element_id: event.target.value || undefined }))}><option value="">No assignment target</option>{otherElements.map((item) => <option value={item.id} key={item.id}>{item.type ?? item.kind} · {item.id}</option>)}</select></label>
        <label className="inspector-field"><span>Combo / partner</span><select value={element.block_partner_element_id ?? ''} onChange={(event) => onElement(element.id, offensiveBlockingPatch({ block_partner_element_id: event.target.value || undefined }))}><option value="">No partner</option>{otherElements.map((item) => <option value={item.id} key={item.id}>{item.type ?? item.kind} · {item.id}</option>)}</select></label>
      </div>
      <fieldset className="protection-detail-editor">
        <legend>Protection responsibility</legend>
        <p>Make the protected surface and communication order explicit for teaching and synchronized timeline cues.</p>
        <div className="inspector-form inspector-form--two inspector-form--nested">
          <label className="inspector-field"><span>Protected target / threat</span><select aria-label="Protected target / threat" value={(element.protection_target_element_id as string | undefined) ?? ''} onChange={(event) => onElement(element.id, { protection_target_element_id: event.target.value || undefined })}><option value="">No explicit threat</option>{otherElements.map((item) => <option value={item.id} key={item.id}>{item.type ?? item.kind} · {item.id}</option>)}</select></label>
          <label className="inspector-field"><span>Slide direction</span><select aria-label="Protection slide direction" value={(element.protection_slide_direction as string | undefined) ?? ''} onChange={(event) => onElement(element.id, { protection_slide_direction: event.target.value || undefined })}><option value="">Not specified</option><option value="left">Left</option><option value="right">Right</option><option value="away">Away from back</option><option value="toward">Toward back</option></select></label>
        </div>
        <CommitInput label="Scan order / communication" value={element.protection_scan_order as string | undefined} onCommit={(value) => onElement(element.id, { protection_scan_order: value || undefined })} />
      </fieldset>
    </fieldset> : null}
    {isRoute ? <fieldset className="route-authoring-editor">
      <legend>Route construction</legend>
      <p>Define the route’s stem, break, finish, and conversion rule; direct canvas handles remain available for exact geometry.</p>
      <div className="inspector-form inspector-form--two inspector-form--nested">
        <label className="inspector-field"><span>Route family</span><select value={element.route_family ?? ''} onChange={(event) => onElement(element.id, routeAuthoringPatch({ route_family: event.target.value || undefined }))}><option value="">Unspecified</option>{ROUTE_FAMILIES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <CommitInput label="Stem depth (yards)" type="number" min={0} max={60} value={element.stem_depth_yards} onCommit={(value) => onElement(element.id, routeConstructionPatch(element, design, { stem_depth_yards: value.trim() ? Number(value) : undefined }))} />
        <label className="inspector-field"><span>Break</span><select value={element.break_type ?? ''} onChange={(event) => onElement(element.id, routeAuthoringPatch({ break_type: event.target.value || undefined }))}><option value="">Unspecified</option>{ROUTE_BREAKS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <CommitInput label="Break depth (yards)" type="number" min={0} max={60} value={element.break_depth_yards} onCommit={(value) => onElement(element.id, routeConstructionPatch(element, design, { break_depth_yards: value.trim() ? Number(value) : undefined }))} />
        <label className="inspector-field"><span>Finish direction</span><select value={element.finish_direction ?? ''} onChange={(event) => onElement(element.id, routeConstructionPatch(element, design, { finish_direction: event.target.value || undefined }))}><option value="">Unspecified</option>{ROUTE_FINISHES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label className="inspector-field"><span>Option rule</span><select value={element.option_rule ?? 'none'} onChange={(event) => onElement(element.id, routeAuthoringPatch({ option_rule: event.target.value }))}>{ROUTE_OPTION_RULES.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      </div>
      <CommitInput label="Option condition / coaching rule" value={element.option_condition} onCommit={(value) => onElement(element.id, routeAuthoringPatch({ option_condition: value }))} />
      <div className="route-branch-editor">
        <header><span><strong>Alternate paths</strong><small>Give choice or sight routes an executable second path from the primary finish.</small></span><button type="button" onClick={() => { const start = branchStart(element) ?? { x: 50, y: 20 }; const branch = addRouteBranch(element, { label: `Option ${(element.branches?.length ?? 0) + 1}`, condition: 'If leverage changes', points: [start, { x: Math.min(99, start.x + 8), y: Math.max(1, start.y - 5) }], start_ms: window.start, end_ms: window.end }); onElement(element.id, routeAuthoringPatch({ branches: branch })); }}>Add path</button></header>
        {(element.branches ?? []).map((branch, index) => <div className="route-branch-row" key={branch.id}>
          <CommitInput label={`Path ${index + 1} label`} value={branch.label} onCommit={(value) => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.map((item) => item.id === branch.id ? { ...item, label: value } : item) }))} />
          <CommitInput label="Condition" value={branch.condition} onCommit={(value) => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.map((item) => item.id === branch.id ? { ...item, condition: value } : item) }))} />
          <CommitInput label="Start (ms)" type="number" value={branch.start_ms ?? window.start} onCommit={(value) => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.map((item) => item.id === branch.id ? { ...item, start_ms: Number(value), timing: { ...item.timing, start_ms: Number(value) } } : item) }))} />
          <CommitInput label="End (ms)" type="number" value={branch.end_ms ?? window.end} onCommit={(value) => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.map((item) => item.id === branch.id ? { ...item, end_ms: Number(value), timing: { ...item.timing, end_ms: Number(value) } } : item) }))} />
          <RouteBranchPoints element={element} branch={branch} onElement={onElement} />
          <button type="button" aria-label={`Delete ${branch.label}`} onClick={() => onElement(element.id, routeAuthoringPatch({ branches: element.branches?.filter((item) => item.id !== branch.id) }))}>Delete</button>
        </div>)}
      </div>
    </fieldset> : null}
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <CommitInput label="Technique" value={element.technique} onCommit={(value) => onElement(element.id, { technique: value })} />
      <CommitInput label="Landmark" value={element.landmark} onCommit={(value) => onElement(element.id, { landmark: value })} />
      <label className="inspector-field"><span>Snap endpoint to landmark</span><select defaultValue="" onChange={(event) => { if (event.target.value) onElement(element.id, landmarkPatch(element, design, event.target.value)); }}>
        <option value="">Choose a field landmark</option>{LANDMARK_SNAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
      </select></label>
    </div>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <CommitInput label="Depth (yards)" type="number" min={0} max={60} value={element.depth_yards} onCommit={(value) => { const parsed = value.trim() ? Number(value) : undefined; onElement(element.id, depthPatch(element, design, parsed)); }} />
      <label className="inspector-field"><span>Break angle</span><select value={element.angle_preset ?? 'vertical'} onChange={(event) => onElement(element.id, anglePatch(element, design, event.target.value))}>
        {ANGLE_PRESETS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
      </select></label>
      <label className="inspector-field"><span>Leverage</span><select value={element.leverage ?? ''} onChange={(event) => onElement(element.id, { leverage: event.target.value || undefined })}>
        <option value="">Not specified</option><option value="inside">Inside</option><option value="outside">Outside</option><option value="head_up">Head up</option><option value="top_down">Top down</option><option value="trail">Trail</option><option value="stack">Stack</option><option value="free">Free</option>
      </select></label>
    </div>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      {isDefense ? <label className="inspector-field"><span>Gap ownership</span><select value={element.gap_owner ?? ''} onChange={(event) => onElement(element.id, gapOwnerPatch(event.target.value))}>
        <option value="">Unspecified</option>{DEFENSIVE_GAP_OPTIONS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
      </select></label> : null}
      <CommitInput label="Gap / fit" value={element.fit_gap ?? element.gap} onCommit={(value) => onElement(element.id, element.kind === 'fit' ? { fit_gap: value } : { gap: value })} />
      {['coverage', 'rotation'].includes(element.kind) ? <label className="inspector-field"><span>Shell destination</span><select aria-label="Shell destination" value={element.zone ?? element.rotation_to_zone ?? ''} onChange={(event) => onElement(element.id, coverageMovementPatch(element, design, event.target.value))}><option value="">Unspecified</option>{['deep_left', 'deep_middle', 'deep_right', 'deep_half_left', 'deep_half_right', 'flat_left', 'flat_right', 'hook_curl_left', 'hook_curl_middle', 'hook_curl_right', 'robber', 'bracket', 'man'].map((zone) => <option value={zone} key={zone}>{zone.replaceAll('_', ' ')}</option>)}</select></label> : <CommitInput label="Zone" value={element.zone} onCommit={(value) => onElement(element.id, { zone: value })} />}
    </div>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <CommitInput label="Read key" value={element.read_key} onCommit={(value) => onElement(element.id, { read_key: value })} />
      <CommitInput label="Read prompt" value={element.read_prompt} onCommit={(value) => onElement(element.id, { read_prompt: value })} />
    </div>
    <label className="inspector-field"><span>Assignment owner</span><select value={element.player_id ?? ''} onChange={(event) => onElement(element.id, { player_id: event.target.value || null })}>
      <option value="">Unassigned / team cue</option>{(design.players ?? []).map((player) => <option value={player.id} key={player.id}>{player.position ?? player.role ?? player.id}</option>)}
    </select></label>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <label className="inspector-field"><span>Target player</span><select value={element.target_player_id ?? ''} onChange={(event) => onElement(element.id, { target_player_id: event.target.value || undefined })}>
        <option value="">No player target</option>{(design.players ?? []).map((player) => <option value={player.id} key={player.id}>{player.position ?? player.role ?? player.id}</option>)}
      </select></label>
      <label className="inspector-field"><span>Target assignment</span><select value={element.target_element_id ?? ''} onChange={(event) => onElement(element.id, { target_element_id: event.target.value || undefined })}>
        <option value="">No assignment target</option>{otherElements.map((item) => <option value={item.id} key={item.id}>{item.type ?? item.kind} · {item.id}</option>)}
      </select></label>
    </div>
    <label className="inspector-field"><span>Exchange partner</span><select value={element.exchange_with ?? ''} onChange={(event) => canExchange ? commitExchange(event.target.value) : onElement(element.id, { exchange_with: event.target.value || undefined })}>
      <option value="">No exchange</option>{otherElements.map((item) => <option value={item.id} key={item.id}>{item.type ?? item.kind} · {item.id}</option>)}
    </select></label>
    {canExchange ? <div className="defensive-exchange-panel">
      <div><strong>Coordinated exchange</strong><small>Link both assignments so the stunt, replacement, or rotation teaches as one relationship.</small></div>
      <label className="inspector-field"><span>Exchange pattern</span><select aria-label="Defensive exchange pattern" defaultValue="" disabled={!element.exchange_with} onChange={(event) => { const partner = element.exchange_with; if (!partner || !event.target.value) return; defensiveExchangePresetPatch(event.target.value, element.id, partner).forEach(([id, patch]) => onElement(id, patch)); }}>
        <option value="">Choose a named pattern</option>{DEFENSIVE_EXCHANGE_PRESETS.map((preset) => <option value={preset.value} key={preset.value}>{preset.label}</option>)}
      </select><small>{element.exchange_with ? 'Apply to the selected assignment and its partner.' : 'Choose an exchange partner first.'}</small></label>
      <label className="inspector-field"><span>This defender’s exchange role</span><select value={element.exchange_role ?? ''} onChange={(event) => commitExchangeRole(event.target.value as DefensiveExchangeRole)}>
        <option value="">Choose an exchange role</option>{DEFENSIVE_EXCHANGE_ROLES.map((role) => <option value={role.value} key={role.value}>{role.label} — {role.description}</option>)}
      </select></label>
      {element.exchange_with ? <small className="defensive-exchange-panel__status">Linked to {otherElements.find((item) => item.id === element.exchange_with)?.type ?? element.exchange_with}{exchangeRole(element.exchange_role) ? ` · ${exchangeRole(element.exchange_role)?.description}` : ''}</small> : null}
    </div> : null}
    {isRotation ? <fieldset className="rotation-sequence-editor">
      <legend>Post-snap rotation sequence</legend>
      <p>Document the trigger, vacated responsibility, replacement zone, and communication so the shell can be taught in order.</p>
      <div className="inspector-form inspector-form--two inspector-form--nested">
        <label className="inspector-field"><span>Rotation trigger</span><select value={element.rotation_trigger ?? ''} onChange={(event) => onElement(element.id, rotationSequencePatch({ rotation_trigger: event.target.value || undefined }))}><option value="">Choose trigger</option>{ROTATION_TRIGGERS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <CommitInput label="Sequence order" type="number" min={1} value={element.rotation_sequence} onCommit={(value) => onElement(element.id, rotationSequencePatch({ rotation_sequence: value.trim() ? Math.max(1, Number(value)) : undefined }))} />
        <CommitInput label="Vacated zone" value={element.rotation_vacated_zone} onCommit={(value) => onElement(element.id, rotationSequencePatch({ rotation_vacated_zone: value }))} />
        <CommitInput label="Replacement zone" value={element.rotation_to_zone ?? element.zone} onCommit={(value) => onElement(element.id, rotationSequencePatch({ rotation_to_zone: value, zone: value }))} />
      </div>
      <label className="inspector-field"><span>Replacement defender</span><select value={element.rotation_replacement_player_id ?? ''} onChange={(event) => onElement(element.id, rotationSequencePatch({ rotation_replacement_player_id: event.target.value || undefined }))}><option value="">Unassigned</option>{(design.players ?? []).map((player) => <option value={player.id} key={player.id}>{player.position ?? player.role ?? player.id}</option>)}</select></label>
      <CommitInput label="Communication / alert" value={element.rotation_communication} onCommit={(value) => onElement(element.id, rotationSequencePatch({ rotation_communication: value }))} />
    </fieldset> : null}
    <fieldset className="assignment-dependencies"><legend>Prerequisite assignments</legend>
      {!otherElements.length ? <span>No other assignments are available.</span> : otherElements.map((item) => {
        const checked = (element.depends_on ?? []).includes(item.id);
        return <label key={item.id}><input type="checkbox" checked={checked} onChange={(event) => onElement(element.id, { depends_on: event.target.checked ? [...new Set([...(element.depends_on ?? []), item.id])] : (element.depends_on ?? []).filter((id) => id !== item.id) })} /><span>{item.type ?? item.kind}</span><small>{item.id}</small></label>;
      })}
    </fieldset>
    <label className="assignment-exclusive"><input type="checkbox" checked={element.exclusive_assignment === true} onChange={(event) => onElement(element.id, { exclusive_assignment: event.target.checked })} /><span><strong>Exclusive responsibility</strong><small>Flag overlapping owners or duplicate targets as a conflict.</small></span></label>
    <div className="inspector-form inspector-form--two inspector-form--nested">
      <CommitInput label="Start (ms)" type="number" value={window.start} onCommit={(value) => onElement(element.id, timingPatch(element, Number(value), window.end))} />
      <CommitInput label="End (ms)" type="number" value={window.end} onCommit={(value) => onElement(element.id, timingPatch(element, window.start, Number(value)))} />
    </div>
    <div className="assignment-phase-editor">
      <header><span><strong>Teaching phases</strong><small>Precise first step, development, exchange, and finish timing.</small></span><button type="button" onClick={() => onElement(element.id, { timing: { ...element.timing, start_ms: window.start, end_ms: window.end, phases: defaultTimelinePhases(element.kind, window.start, window.end) } })}>Reset</button></header>
      {phases.map((phase) => <div className="assignment-phase-row" key={phase.id}>
        <CommitInput label="Phase" value={phase.label ?? phase.id} onCommit={(value) => updatePhase(phase.id, { label: value })} />
        <CommitInput label="Start" type="number" value={phase.start_ms} onCommit={(value) => updatePhase(phase.id, { start_ms: Number(value) })} />
        <CommitInput label="End" type="number" value={phase.end_ms} onCommit={(value) => updatePhase(phase.id, { end_ms: Number(value) })} />
      </div>)}
    </div>
  </div>;
}
