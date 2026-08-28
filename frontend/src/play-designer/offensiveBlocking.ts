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
  const next: Partial<PlayElement> = { ...patch, phase: patch.blocking_primitive === 'screen_release' ? 'release' : 'block' };
  if (patch.protection_mode && PROTECTION_ROLES[patch.protection_mode]) next.protection_path_role = PROTECTION_ROLES[patch.protection_mode];
  return next;
}

const PRIMITIVE_ROLES: Record<string, string> = {
  base: 'fit-and-drive', reach: 'reach-the-play-side-edge', down: 'close-the-near-gap',
  pull: 'pull-to-lead', trap: 'pull-to-trap', wrap: 'pull-to-wrap', fold: 'fold-with-adjacent-blocker',
  combo: 'combination-to-linebacker', climb: 'climb-to-second-level', scoop: 'scoop-backside-gap',
  insert: 'insert-through-declared-gap', arc: 'arc-release-to-force', screen_release: 'release-to-screen',
};

const PROTECTION_ROLES: Record<string, string> = {
  man: 'man-to-man', full_slide: 'slide-full', half_slide_left: 'slide-left',
  half_slide_right: 'slide-right', scan: 'scan-dual-read', screen: 'screen-release',
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
  const partnerId = String(patch.block_partner_element_id ?? element.block_partner_element_id ?? '');
  const partner = partnerId ? design.elements?.find((item) => item.id === partnerId) : undefined;
  const partnerDestination = partner ? pointForTarget(partner, design) : undefined;
  const existing = element.points ?? element.path ?? [];
  if (source && destination && existing.length < 2) {
    const lateral = primitive === 'trap'
      ? (source.x <= destination.x ? -5 : 5)
      : primitive === 'pull' || primitive === 'wrap' ? (source.x <= destination.x ? 5 : -5) : 0;
    const midpoint = { x: (source.x + destination.x) / 2 + lateral, y: (source.y + destination.y) / 2 };
    const points = primitive === 'combo' && partnerDestination
      ? [source, midpoint, destination, { x: (destination.x + partnerDestination.x) / 2, y: (destination.y + partnerDestination.y) / 2 }, partnerDestination]
      : primitive === 'screen_release'
        ? [source, { x: source.x, y: source.y - 3 }, destination]
        : [source, midpoint, destination];
    if (element.points) next.points = points;
    else next.path = points;
  }
  return next;
}
