import type { PlayElement } from '../types';

export const OFFENSIVE_BLOCKING_PRIMITIVES = [
  ['base', 'Base block'], ['reach', 'Reach'], ['down', 'Down block'], ['pull', 'Pull'], ['trap', 'Trap'],
  ['wrap', 'Wrap'], ['fold', 'Fold'], ['combo', 'Combo'], ['climb', 'Climb'], ['scoop', 'Scoop'],
  ['insert', 'Insert'], ['arc', 'Arc release'], ['screen_release', 'Screen release'],
] as const;

export const PROTECTION_MODES = [
  ['man', 'Man protection'], ['full_slide', 'Full slide'], ['half_slide_left', 'Half slide left'],
  ['half_slide_right', 'Half slide right'], ['scan', 'Scan / dual read'], ['screen', 'Screen protection'],
] as const;

export function offensiveBlockingPatch(patch: Partial<PlayElement>): Partial<PlayElement> {
  return { ...patch, phase: patch.blocking_primitive === 'screen_release' ? 'release' : 'block' };
}
