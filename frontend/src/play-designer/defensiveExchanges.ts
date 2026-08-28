import type { PlayDesign, PlayElement } from '../types';

export type DefensiveExchangeRole = 'penetrate_loop' | 'loop_penetrate' | 'rush_replace' | 'drop_replace' | 'carry_transfer' | 'rotate_replace';

export const DEFENSIVE_EXCHANGE_ROLES: Array<{ value: DefensiveExchangeRole; label: string; reciprocal: DefensiveExchangeRole; description: string }> = [
  { value: 'penetrate_loop', label: 'Penetrate → loop', reciprocal: 'loop_penetrate', description: 'This defender penetrates; the partner loops behind the exchange.' },
  { value: 'loop_penetrate', label: 'Loop → penetrate', reciprocal: 'penetrate_loop', description: 'This defender loops; the partner penetrates the first lane.' },
  { value: 'rush_replace', label: 'Rush → replace', reciprocal: 'drop_replace', description: 'This defender rushes while the partner replaces the vacated coverage space.' },
  { value: 'drop_replace', label: 'Drop → replace', reciprocal: 'rush_replace', description: 'This defender drops while the partner replaces the rush lane.' },
  { value: 'carry_transfer', label: 'Carry → transfer', reciprocal: 'carry_transfer', description: 'Carry the threat until the partner takes the next responsibility.' },
  { value: 'rotate_replace', label: 'Rotate → replace', reciprocal: 'rotate_replace', description: 'Rotate into the destination while the partner replaces the shell responsibility.' },
];

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
}

export function defensiveExchangeLinks(design: PlayDesign): DefensiveExchangeLink[] {
  const elements = design.elements ?? [];
  return elements.flatMap((element) => {
    const partnerId = element.exchange_with;
    if (!partnerId || element.id > partnerId) return [];
    const partner = elements.find((candidate) => candidate.id === partnerId);
    const from = element.points?.at(-1);
    const to = partner?.points?.at(-1);
    if (!partner || !from || !to) return [];
    return [{ id: `${element.id}::${partner.id}`, fromId: element.id, toId: partner.id, role: element.exchange_role, label: exchangeRole(element.exchange_role)?.label ?? 'Defensive exchange', from, to }];
  });
}
