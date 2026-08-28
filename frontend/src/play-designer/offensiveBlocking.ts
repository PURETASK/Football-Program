import type { PlayDesign, PlayElement, Point, ValidationIssue } from '../types';

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

function blockingIssue(code: string, message: string, path: string, suggestion: string, severity: ValidationIssue['severity'] = 'warning'): ValidationIssue {
  return { code, message, path, suggestion, severity };
}

/** Local authoring diagnostics; the server remains authoritative for legality and release decisions. */
export function offensiveBlockingIssues(design: PlayDesign): ValidationIssue[] {
  if (design.unit !== 'offense') return [];
  const elements = design.elements ?? [];
  const ids = new Set(elements.map((element) => element.id));
  const issues: ValidationIssue[] = [];
  elements.forEach((element, index) => {
    if (!['block', 'run'].includes(element.kind)) return;
    const primitive = String(element.blocking_primitive ?? '');
    const targetId = element.block_target_element_id ?? element.target_element_id;
    const partnerId = element.block_partner_element_id;
    if (targetId === element.id || partnerId === element.id) issues.push(blockingIssue('BLOCKING_SELF_REFERENCE', `${element.type ?? element.kind} cannot target or partner with itself.`, `elements[${index}]`, 'Choose another assignment or clear the self-reference.', 'error'));
    if (targetId && !ids.has(targetId)) issues.push(blockingIssue('BLOCKING_TARGET_MISSING', `${element.type ?? element.kind} references a block target that is not in this play.`, `elements[${index}].block_target_element_id`, 'Choose an existing assignment as the block target.', 'error'));
    if (partnerId && !ids.has(partnerId)) issues.push(blockingIssue('BLOCKING_PARTNER_MISSING', `${element.type ?? element.kind} references a combo partner that is not in this play.`, `elements[${index}].block_partner_element_id`, 'Choose an existing assignment as the combo partner.', 'error'));
    if (['pull', 'trap', 'wrap', 'fold', 'insert', 'arc'].includes(primitive) && !targetId) issues.push(blockingIssue('BLOCKING_TARGET_REQUIRED', `${primitive} needs an explicit assignment target before it can be taught or released.`, `elements[${index}].block_target_element_id`, 'Choose the defender or surface this blocker acts on.'));
    if (primitive === 'combo' && !partnerId) issues.push(blockingIssue('COMBO_PARTNER_REQUIRED', 'Combo block has no second blocker or partner assignment.', `elements[${index}].block_partner_element_id`, 'Choose the adjacent blocker or partner assignment.'));
    if (primitive === 'combo' && !targetId) issues.push(blockingIssue('COMBO_TARGET_REQUIRED', 'Combo block has no second-level or declared target.', `elements[${index}].block_target_element_id`, 'Choose the linebacker or target assignment the combo climbs to.'));
    if (primitive === 'screen_release' && element.protection_mode !== 'screen') issues.push(blockingIssue('SCREEN_PROTECTION_MODE', 'Screen release is not paired with screen protection mode.', `elements[${index}].protection_mode`, 'Set Protection mode to Screen or choose another blocking primitive.'));
  });
  return issues;
}

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
