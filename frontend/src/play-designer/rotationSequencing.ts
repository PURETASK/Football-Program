import type { PlayElement } from '../types';

export const ROTATION_TRIGGERS = [
  ['snap', 'At snap'],
  ['motion', 'Motion declaration'],
  ['route_release', 'Route release'],
  ['qb_flow', 'QB flow / read'],
  ['pressure', 'Pressure confirmation'],
] as const;

export function rotationSequencePatch(patch: Partial<PlayElement>): Partial<PlayElement> {
  return { ...patch, phase: 'rotation' };
}

export function rotationLabel(element: PlayElement): string {
  const trigger = ROTATION_TRIGGERS.find(([value]) => value === element.rotation_trigger)?.[1] ?? element.rotation_trigger ?? 'Unspecified trigger';
  const destination = element.rotation_to_zone ?? 'replacement zone not set';
  return `${trigger} → ${destination}`;
}
