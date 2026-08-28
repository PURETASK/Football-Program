import type { PlayDesign, PlayElement, PlayPlayer, PlayTemplate, PlayTemplateAssignment } from '../types';
import { normalizePoint } from './geometry';
import { defaultTimelinePhases } from './timelineModel';

function clone<T>(value: T): T { return structuredClone(value); }
function identifier(value: string): string { return value.toUpperCase().replace(/[^A-Z0-9]+/g, '-').replace(/^-|-$/g, ''); }
const ALIGNMENT_KEYS = ['CB-L', 'CB-R', 'DE-L', 'DE-R', 'DT-L', 'DT-R', 'MLB', 'WLB', 'NB', 'FS', 'SS', 'QB', 'RB', 'LT', 'LG', 'RT', 'RG', 'X', 'Y', 'Z', 'H', 'C'];
function playerAlignmentKey(player: PlayPlayer): string | undefined {
  if (player.alignment_key) return player.alignment_key;
  const label = player.label?.toUpperCase();
  if (label && ALIGNMENT_KEYS.includes(label)) return label;
  const id = player.id.toUpperCase();
  return ALIGNMENT_KEYS.find((key) => id === key || id.endsWith(`-${key}`));
}

function templatePlayers(design: PlayDesign, template: PlayTemplate, replaceAlignment: boolean): PlayPlayer[] {
  const slots = template.alignment?.slots ?? [];
  if (!replaceAlignment || !slots.length) return clone(design.players ?? []);
  const currentByKey = new Map((design.players ?? []).map((player) => [playerAlignmentKey(player), player]));
  const presetBall = template.alignment?.ball;
  const ballX = Number(design.field_context?.ball_x ?? 50);
  const ballY = Number(design.field_context?.ball_y ?? design.field_context?.line_of_scrimmage_y ?? 26.5);
  const offset = { x: ballX - Number(presetBall?.x ?? 50), y: ballY - Number(presetBall?.y ?? 26.5) };
  return slots.map((slot) => {
    const current = currentByKey.get(slot.key);
    return { ...current, id: current?.id ?? `${design.id}-${identifier(slot.key)}`, alignment_key: slot.key, position: slot.position ?? current?.position ?? slot.key, role: slot.role ?? current?.role ?? slot.key, start: normalizePoint({ x: slot.x + offset.x, y: slot.y + offset.y }, false) };
  });
}

function namespaceTimeline(template: PlayTemplate, design: PlayDesign, applicationId: string, mode: 'replace' | 'layer') {
  const source = template.timeline ?? {};
  const current = design.timeline ?? {};
  const namespace = <T extends { id?: string }>(items: T[] | undefined, fallback: string) => (items ?? []).map((item, index) => ({ ...item, id: `${applicationId}-${identifier(item.id ?? `${fallback}-${index + 1}`)}` }));
  const sourceMarkers = namespace(source.markers, 'MARK');
  const sourceNarration = namespace(source.narration, 'NARRATION');
  const sourceEvents = namespace(source.events, 'EVENT');
  const duration = Math.max(Number(current.duration_ms ?? 3000), Number(source.duration_ms ?? 3000));
  if (mode === 'layer') return { ...current, duration_ms: duration, markers: [...(current.markers ?? []), ...sourceMarkers.filter((marker) => marker.kind !== 'snap')], narration: [...(current.narration ?? []), ...sourceNarration], events: [...(current.events ?? []), ...sourceEvents] };
  return { snap_ms: Number(source.snap_ms ?? 0), duration_ms: Math.max(1000, Number(source.duration_ms ?? 3000)), markers: [{ id: `${applicationId}-SNAP`, label: 'Snap', kind: 'snap', ms: 0 }, ...sourceMarkers.filter((marker) => marker.kind !== 'snap')], narration: sourceNarration, events: sourceEvents };
}

export function resolveTemplateAssignments(template: PlayTemplate): Array<{ assignment: PlayTemplateAssignment; origin: 'inherited' | 'local' }> {
  const resolved = new Map<string, { assignment: PlayTemplateAssignment; origin: 'inherited' | 'local' }>();
  for (const assignment of template.inherited_assignments ?? []) resolved.set(assignment.key, { assignment, origin: 'inherited' });
  for (const assignment of template.assignments ?? []) resolved.set(assignment.key, { assignment, origin: 'local' });
  return [...resolved.values()];
}

export interface TemplateInheritanceDiff {
  inherited: string[];
  overridden: Array<{ key: string; fields: string[] }>;
  added: string[];
}

/** Compare a child package's resolved assignments with its direct parent for lineage review. */
export function diffTemplateInheritance(parent: PlayTemplate, child: PlayTemplate): TemplateInheritanceDiff {
  const parentAssignments = new Map(resolveTemplateAssignments(parent).map(({ assignment }) => [assignment.key, assignment]));
  const childAssignments = new Map(resolveTemplateAssignments(child).map(({ assignment, origin }) => [assignment.key, { assignment, origin }]));
  const inherited: string[] = [];
  const overridden: Array<{ key: string; fields: string[] }> = [];
  const added: string[] = [];
  for (const [key, item] of childAssignments) {
    const parentAssignment = parentAssignments.get(key);
    if (!parentAssignment) {
      added.push(key);
      continue;
    }
    if (item.origin !== 'local') {
      inherited.push(key);
      continue;
    }
    const fields = [...new Set([...Object.keys(parentAssignment), ...Object.keys(item.assignment)])]
      .filter((field) => field !== 'key')
      .filter((field) => JSON.stringify(parentAssignment[field as keyof PlayTemplateAssignment]) !== JSON.stringify(item.assignment[field as keyof PlayTemplateAssignment]));
    if (fields.length) overridden.push({ key, fields });
    else inherited.push(key);
  }
  return { inherited, overridden, added };
}

/** Materialize a reusable slot-relative package into this team's canonical play record. */
export function applyPlayTemplate(design: PlayDesign, template: PlayTemplate, mode: 'replace' | 'layer' = 'replace'): PlayDesign {
  if (template.unit !== design.unit) return design;
  const resolvedAssignments = resolveTemplateAssignments(template);
  const assignments = resolvedAssignments.map(({ assignment }) => assignment);
  if (!assignments.length) return { ...design, formation: template.formation ?? design.formation, front: template.front ?? design.front, coverage: template.coverage ?? design.coverage, personnel: template.personnel ?? design.personnel, concept: template.concept ?? design.concept };
  const priorApplications = Array.isArray(design.template_applications) ? design.template_applications as Array<Record<string, unknown>> : [];
  const applicationId = `APP-${identifier(template.id)}-${priorApplications.length + 1}`;
  const players = templatePlayers(design, template, mode === 'replace');
  const playerBySlot = new Map(players.map((player) => [playerAlignmentKey(player), player]));
  const existingIds = new Set((mode === 'layer' ? design.elements ?? [] : []).map((element) => element.id));
  const idByKey = new Map<string, string>();
  for (const assignment of assignments) {
    const base = `${applicationId}-${identifier(assignment.key)}`;
    let id = base; let copy = 2;
    while (existingIds.has(id)) { id = `${base}-${copy}`; copy += 1; }
    existingIds.add(id); idByKey.set(assignment.key, id);
  }
  const materialized = resolvedAssignments.map(({ assignment, origin: assignmentOrigin }) => {
    const { key, slot, points: offsets, depends_on: dependencyKeys, exchange_with: exchangeKey, target_element_key: targetKey, timing: sourceTiming, ...fields } = assignment;
    const player = playerBySlot.get(slot);
    const origin = player?.start ?? { x: Number(design.field_context?.ball_x ?? 50), y: Number(design.field_context?.ball_y ?? 26.5) };
    const points = (offsets ?? []).map((point) => normalizePoint({ x: origin.x + point.dx, y: origin.y + point.dy }, false));
    const timingStart = Number(sourceTiming?.start_ms ?? fields.start_ms ?? 0);
    const timingEnd = Math.max(timingStart + 1, Number(sourceTiming?.end_ms ?? fields.end_ms ?? 1200));
    const timing = { ...sourceTiming, start_ms: timingStart, end_ms: timingEnd, phases: sourceTiming?.phases?.length ? clone(sourceTiming.phases) : defaultTimelinePhases(String(fields.kind), timingStart, timingEnd) };
    const element: PlayElement = { ...fields, id: idByKey.get(key)!, player_id: player?.id ?? null, asset_id: fields.asset_id ?? template.id, template_id: template.id, template_assignment_key: key, template_assignment_origin: assignmentOrigin, start_ms: timingStart, end_ms: timingEnd, timing, depends_on: (dependencyKeys ?? []).map((dependency) => idByKey.get(dependency)).filter((id): id is string => Boolean(id)), exchange_with: exchangeKey ? idByKey.get(exchangeKey) : undefined, target_element_id: targetKey ? idByKey.get(targetKey) : undefined };
    if (points.length) element.points = points;
    return element;
  });
  const elements = mode === 'layer' ? [...(design.elements ?? []), ...materialized] : materialized;
  const coverageZones = [...new Set([...(mode === 'layer' ? design.coverage_zones ?? [] : []), ...materialized.filter((element) => element.kind === 'coverage' && element.zone).map((element) => String(element.zone))])];
  const templateNotes = template.coaching_points ?? [];
  return { ...design, players, elements, formation: mode === 'replace' ? template.formation ?? design.formation : design.formation ?? template.formation, front: template.front ?? design.front, coverage: template.coverage ?? design.coverage, personnel: mode === 'replace' ? template.personnel ?? design.personnel : design.personnel, concept: ['route_concept', 'run_rpo', 'coverage_call', 'coverage'].includes(template.layer ?? '') ? template.concept ?? design.concept : design.concept, coverage_zones: coverageZones.length ? coverageZones : design.coverage_zones, coaching_notes: mode === 'replace' ? [...templateNotes] : [...(design.coaching_notes ?? []), ...templateNotes], timeline: namespaceTimeline(template, design, applicationId, mode), template_applications: [...priorApplications, { id: applicationId, template_id: template.id, template_version: template.version, mode, layer: template.layer }], validation: { status: 'not_checked', issues: [] } };
}
