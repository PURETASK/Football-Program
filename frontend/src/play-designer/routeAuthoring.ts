import type { PlayElement } from '../types';

export const ROUTE_FAMILIES = [
  ['quick', 'Quick game'], ['dropback', 'Dropback'], ['intermediate', 'Intermediate'], ['vertical', 'Vertical'],
  ['screen', 'Screen'], ['crossing', 'Crossing'], ['sight', 'Sight-adjust'],
] as const;

export const ROUTE_BREAKS = [
  ['none', 'No break'], ['speed_out', 'Speed out'], ['comeback', 'Comeback'], ['curl', 'Curl'],
  ['dig', 'Dig / in'], ['over', 'Over / deep cross'], ['post', 'Post'], ['corner', 'Corner'],
  ['whip', 'Whip / pivot'], ['choice', 'Choice break'], ['option', 'Option break'],
] as const;

export const ROUTE_FINISHES = [
  ['vertical', 'Finish vertical'], ['inside', 'Finish inside'], ['outside', 'Finish outside'],
  ['settle', 'Settle in window'], ['runaway', 'Run away from leverage'],
] as const;

export const ROUTE_OPTION_RULES = [
  ['none', 'No option'], ['leverage', 'Convert by leverage'], ['safety', 'Convert by safety rotation'],
  ['coverage', 'Convert by coverage'], ['sight', 'Sight-adjust on pressure'],
] as const;

export function routeAuthoringPatch(patch: Partial<PlayElement>): Partial<PlayElement> {
  return { ...patch, phase: 'route' };
}
