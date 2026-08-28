import type { PlayDesign, PlayElement, Point } from '../types';

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

const PRIMITIVE_ROLES: Record<string, string> = {
  base: 'fit-and-drive', reach: 'reach-the-play-side-edge', down: 'close-the-near-gap',
  pull: 'pull-to-lead', trap: 'pull-to-trap', wrap: 'pull-to-wrap', fold: 'fold-with-adjacent-blocker',
  combo: 'combination-to-linebacker', climb: 'climb-to-second-level', scoop: 'scoop-backside-gap',
  insert: 'insert-through-declared-gap', arc: 'arc-release-to-force', screen_release: 'release-to-screen',
};

function pointForTarget(target: PlayElement, design: PlayDesign): Point | undefined {
  const targetPoints = target.points ?? target.path;
  if (targetPoints?.length) return targetPoints[0];
  if (target.player_id) return design.players?.find((player) => player.id === target.player_id)?.start;
  return undefined;
}

/** Build a target-aware starter path without overwriting coach-drawn geometry. */
export function blockingConstructionPatch(element: PlayElement, design: PlayDesign, patch: Partial<PlayElement>): Partial<PlayElement> {
  const next = offensiveBlockingPatch(patch);
  const primitive = String(patch.blocking_primitive ?? element.blocking_primitive ?? '');
  if (primitive && PRIMITIVE_ROLES[primitive]) {
    next.blocking_path_role = PRIMITIVE_ROLES[primitive];
    next.blocking_geometry = 'target-aware';
  }
  const targetId = String(patch.block_target_element_id ?? patch.target_element_id ?? element.block_target_element_id ?? element.target_element_id ?? '');
  const source = (element.points ?? element.path)?.[0] ?? (element.player_id ? design.players?.find((player) => player.id === element.player_id)?.start : undefined);
  const target = targetId ? design.elements?.find((item) => item.id === targetId) : undefined;
  const destination = target ? pointForTarget(target, design) : undefined;
  const existing = element.points ?? element.path ?? [];
  if (source && destination && existing.length < 2) {
    const lateral = primitive === 'pull' || primitive === 'trap' || primitive === 'wrap' ? (source.x <= destination.x ? 5 : -5) : 0;
    const points = [source, { x: (source.x + destination.x) / 2 + lateral, y: (source.y + destination.y) / 2 }, destination];
    if (element.points) next.points = points;
    else next.path = points;
  }
  return next;
}
