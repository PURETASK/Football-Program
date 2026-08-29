import type { PlayDesign, PlayElement, PlayPlayer } from '../types';
import { timelineEventKind, timelineEventStart, timelineEventEnd } from './timelineEvents';

export type DefensiveExchangeRole = 'penetrate_loop' | 'loop_penetrate' | 'rush_replace' | 'drop_replace' | 'carry_transfer' | 'rotate_replace';

export const DEFENSIVE_EXCHANGE_ROLES: Array<{ value: DefensiveExchangeRole; label: string; reciprocal: DefensiveExchangeRole; description: string }> = [
  { value: 'penetrate_loop', label: 'Penetrate → loop', reciprocal: 'loop_penetrate', description: 'This defender penetrates; the partner loops behind the exchange.' },
  { value: 'loop_penetrate', label: 'Loop → penetrate', reciprocal: 'penetrate_loop', description: 'This defender loops; the partner penetrates the first lane.' },
  { value: 'rush_replace', label: 'Rush → replace', reciprocal: 'drop_replace', description: 'This defender rushes while the partner replaces the vacated coverage space.' },
  { value: 'drop_replace', label: 'Drop → replace', reciprocal: 'rush_replace', description: 'This defender drops while the partner replaces the rush lane.' },
  { value: 'carry_transfer', label: 'Carry → transfer', reciprocal: 'carry_transfer', description: 'Carry the threat until the partner takes the next responsibility.' },
  { value: 'rotate_replace', label: 'Rotate → replace', reciprocal: 'rotate_replace', description: 'Rotate into the destination while the partner replaces the shell responsibility.' },
];

export const DEFENSIVE_EXCHANGE_PRESETS: Array<{ value: string; label: string; firstRole: DefensiveExchangeRole; secondRole: DefensiveExchangeRole; description: string }> = [
  { value: 'tex', label: 'TEX — tackle penetrates / end loops', firstRole: 'penetrate_loop', secondRole: 'loop_penetrate', description: 'Interior tackle-end exchange.' },
  { value: 'et', label: 'ET — end penetrates / tackle loops', firstRole: 'penetrate_loop', secondRole: 'loop_penetrate', description: 'Edge end-tackle exchange.' },
  { value: 'cross_dog', label: 'Cross-dog — first penetrates / second loops', firstRole: 'penetrate_loop', secondRole: 'loop_penetrate', description: 'Two-level linebacker cross exchange.' },
  { value: 'rush_replace', label: 'Rush and replace coverage', firstRole: 'rush_replace', secondRole: 'drop_replace', description: 'Rush lane paired with replacement responsibility.' },
  { value: 'carry_transfer', label: 'Carry and transfer', firstRole: 'carry_transfer', secondRole: 'carry_transfer', description: 'Pass the threat between two coverage defenders.' },
];

/** Named relationship metadata keeps a two-player stunt teachable after the
 * individual paths have been edited or exported. */
export const DEFENSIVE_EXCHANGE_CONCEPTS = [
  ['tex', 'TEX · tackle-end exchange'],
  ['et', 'ET · end-tackle exchange'],
  ['cross_dog', 'Cross-dog · linebacker exchange'],
  ['cross_dog_fire', 'Cross-dog fire · pressure exchange'],
  ['rush_replace', 'Rush and replace · coverage exchange'],
  ['carry_transfer', 'Carry and transfer · coverage handoff'],
] as const;

const INTERIOR_POSITIONS = new Set(['DT', 'NT', 'DL', 'TACKLE', 'NOSE', '3T', '4I', '4T', '0T', '1T']);
const EDGE_POSITIONS = new Set(['DE', 'EDGE', 'END', 'OLB', '5T', '6T', '7T', '9T', 'RUSH']);
const LINEBACKER_POSITIONS = new Set(['LB', 'ILB', 'MLB', 'WLB', 'WILL', 'SAM', 'MIKE', 'JACK', 'BUCK', 'LINEBACKER']);

function playerPositionFamily(player: PlayPlayer | undefined): 'interior' | 'edge' | 'linebacker' | 'unknown' {
  const tokens = [player?.position, player?.role, player?.alignment_key].filter(Boolean).map((value) => String(value).trim().toUpperCase());
  if (tokens.some((token) => INTERIOR_POSITIONS.has(token))) return 'interior';
  if (tokens.some((token) => EDGE_POSITIONS.has(token))) return 'edge';
  if (tokens.some((token) => LINEBACKER_POSITIONS.has(token))) return 'linebacker';
  return 'unknown';
}

export function defensiveExchangePresetCompatibility(value: string, first: PlayPlayer | undefined, second: PlayPlayer | undefined): { compatible: boolean; reasons: string[] } {
  if (!['tex', 'et', 'cross_dog'].includes(value)) return { compatible: true, reasons: [] };
  const firstFamily = playerPositionFamily(first);
  const secondFamily = playerPositionFamily(second);
  if (value === 'cross_dog') {
    return firstFamily === 'linebacker' && secondFamily === 'linebacker'
      ? { compatible: true, reasons: [] }
      : { compatible: false, reasons: [`Cross-dog expects two linebacker-family partners; selected ${firstFamily} and ${secondFamily}.`] };
  }
  return new Set([firstFamily, secondFamily]).size === 2 && new Set([firstFamily, secondFamily]).has('interior') && new Set([firstFamily, secondFamily]).has('edge')
    ? { compatible: true, reasons: [] }
    : { compatible: false, reasons: [`${value.toUpperCase()} expects one interior defensive lineman and one edge defender; selected ${firstFamily} and ${secondFamily}.`] };
}

export function exchangeConceptPatch(
  concept: string,
  context: { trigger?: string; communication?: string } = {},
): Partial<PlayElement> {
  const label = DEFENSIVE_EXCHANGE_CONCEPTS.find(([value]) => value === concept)?.[1];
  return {
    exchange_concept: concept || undefined,
    exchange_concept_label: concept ? label : undefined,
    exchange_trigger: concept ? context.trigger ?? 'on_snap' : undefined,
    exchange_communication: concept ? context.communication ?? 'communicate and pass the stunt' : undefined,
    phase: concept ? 'exchange' : undefined,
  };
}

export function exchangeRole(value: string | undefined) {
  return DEFENSIVE_EXCHANGE_ROLES.find((role) => role.value === value);
}

export function exchangePatch(partnerId: string, role: DefensiveExchangeRole | string | undefined): Partial<PlayElement> {
  return {
    exchange_with: partnerId || undefined,
    target_element_id: partnerId || undefined,
    exchange_role: partnerId ? role ?? 'penetrate_loop' : undefined,
    phase: partnerId ? 'exchange' : undefined,
  };
}

export function reciprocalExchangePatch(elementId: string, role: DefensiveExchangeRole | string | undefined): Partial<PlayElement> {
  const reciprocal = exchangeRole(role)?.reciprocal ?? role ?? 'penetrate_loop';
  return exchangePatch(elementId, reciprocal);
}

export function defensiveExchangePairPatch(firstId: string, secondId: string, role: DefensiveExchangeRole | string | undefined, context: { vacated_zone?: string; replacement_zone?: string } = {}): Array<[string, Partial<PlayElement>]> {
  const source = context.vacated_zone ? { responsibility: `Vacate ${context.vacated_zone}` } : {};
  const replacement = context.replacement_zone ? { rotation_to_zone: context.replacement_zone, zone: context.replacement_zone, responsibility: `Replace ${context.replacement_zone}` } : {};
  return [[firstId, { ...exchangePatch(secondId, role), ...source }], [secondId, { ...reciprocalExchangePatch(firstId, role), ...replacement }]];
}

/** Materialize a named coach-facing exchange pattern onto both assignments. */
export function defensiveExchangePresetPatch(value: string, firstId: string, secondId: string, context: { vacated_zone?: string; replacement_zone?: string } = {}): Array<[string, Partial<PlayElement>]> {
  const preset = DEFENSIVE_EXCHANGE_PRESETS.find((item) => item.value === value);
  if (!preset || !firstId || !secondId || firstId === secondId) return [];
  const first = { ...exchangePatch(secondId, preset.firstRole), ...(context.vacated_zone ? { responsibility: `Vacate ${context.vacated_zone}` } : {}) };
  const second = { ...exchangePatch(firstId, preset.secondRole), ...(context.replacement_zone ? { rotation_to_zone: context.replacement_zone, zone: context.replacement_zone, responsibility: `Replace ${context.replacement_zone}` } : {}) };
  return [[firstId, first], [secondId, second]];
}

export function clearDefensiveExchangePairPatch(firstId: string, secondId: string): Array<[string, Partial<PlayElement>]> {
  return [[firstId, exchangePatch('', undefined)], [secondId, exchangePatch('', undefined)]];
}

export interface DefensiveExchangeLink {
  id: string;
  fromId: string;
  toId: string;
  role?: string;
  label: string;
  from: { x: number; y: number };
  to: { x: number; y: number };
  replacement?: { x: number; y: number; label: string };
}

/** Return playback reveal progress for an exchange/rotation cue, if one is authored. */
export function defensiveExchangeProgress(design: PlayDesign, link: DefensiveExchangeLink, timeMs: number | null, fallbackDuration: number): number {
  if (timeMs === null) return 1;
  const event = (design.timeline?.events ?? []).find((candidate) => {
    const kind = timelineEventKind(candidate);
    return (kind === 'exchange' || kind === 'rotation' || kind === 'block_exchange' || kind === 'rush_exchange') && (candidate.element_id === link.fromId || candidate.element_id === link.toId);
  });
  if (!event) return 1;
  const start = timelineEventStart(event);
  const end = timelineEventEnd(event, fallbackDuration);
  return Math.max(0, Math.min(1, (timeMs - start) / Math.max(1, end - start)));
}

const REPLACEMENT_ANCHORS: Record<string, { x: number; y: number }> = {
  flat_left: { x: 14, y: 22 }, flat_right: { x: 86, y: 22 },
  hook_curl_left: { x: 30, y: 20 }, hook_curl_middle: { x: 50, y: 20 }, hook_curl_right: { x: 70, y: 20 },
  deep_left: { x: 18, y: 7 }, deep_middle: { x: 50, y: 7 }, deep_right: { x: 82, y: 7 },
  deep_half_left: { x: 25, y: 7 }, deep_half_right: { x: 75, y: 7 }, robber: { x: 50, y: 31 },
};

export function defensiveExchangeLinks(design: PlayDesign): DefensiveExchangeLink[] {
  const elements = design.elements ?? [];
  return elements.flatMap((element) => {
    const partnerId = element.exchange_with;
    if (!partnerId || element.id > partnerId) return [];
    const partner = elements.find((candidate) => candidate.id === partnerId);
    const from = element.points?.at(-1);
    const to = partner?.points?.at(-1);
    if (!partner || !from || !to) return [];
    const replacementZone = element.rotation_to_zone ?? element.zone ?? partner.rotation_to_zone ?? partner.zone;
    const replacementAnchor = replacementZone ? REPLACEMENT_ANCHORS[replacementZone] : undefined;
    return [{ id: `${element.id}::${partner.id}`, fromId: element.id, toId: partner.id, role: element.exchange_role, label: exchangeRole(element.exchange_role)?.label ?? 'Defensive exchange', from, to,
      replacement: replacementAnchor ? { ...replacementAnchor, label: replacementZone! } : undefined }];
  });
}
