import type { PlayAlignmentSlot, PlayDesign, PlayPlayer } from '../types';

export const DEFENSIVE_TECHNIQUES = [
  ['0', '0-technique / head up center'], ['1', '1-technique / shaded center'], ['2i', '2i-technique / inside guard'],
  ['2', '2-technique / head up guard'], ['3', '3-technique / outside guard'], ['4i', '4i-technique / inside tackle'],
  ['4', '4-technique / head up tackle'], ['5', '5-technique / head up tackle'], ['7', '7-technique / inside tight end'],
  ['9', '9-technique / wide edge'],
] as const;

export const DEFENSIVE_ALIGNMENTS = [
  ['head_up', 'Head up'], ['inside_eye', 'Inside eye'], ['outside_eye', 'Outside eye'],
  ['inside_shade', 'Inside shade'], ['outside_shade', 'Outside shade'], ['wide', 'Wide / apex'],
] as const;

export function defensiveAlignmentPatch(technique: string, alignment: string): Partial<PlayPlayer> {
  return { defensive_technique: technique || undefined, defensive_alignment: alignment || undefined, alignment_key: technique && alignment ? `${technique}:${alignment}` : undefined };
}

export function defensiveAlignmentLabel(player: PlayPlayer): string {
  return [player.defensive_technique && `${player.defensive_technique}-tech`, player.defensive_alignment?.replaceAll('_', ' ')].filter(Boolean).join(' · ') || 'Alignment not specified';
}

/**
 * Convert the compact role language used by a front preset into executable
 * technique metadata. Front slots remain the positional source of truth; the
 * derived fields make the same placement teachable and auditable.
 */
export function defensiveSlotAlignmentPatch(slot: Pick<PlayAlignmentSlot, 'role' | 'position'>): Partial<PlayPlayer> {
  const role = String(slot.role ?? '').toUpperCase().replaceAll('-', '');
  const byRole: Record<string, { technique?: string; alignment: string }> = {
    '0T': { technique: '0', alignment: 'head_up' }, '1T': { technique: '1', alignment: 'inside_shade' },
    '2I': { technique: '2i', alignment: 'inside_eye' }, '2T': { technique: '2', alignment: 'head_up' },
    '3T': { technique: '3', alignment: 'outside_eye' }, '4I': { technique: '4i', alignment: 'inside_eye' },
    '4T': { technique: '4', alignment: 'head_up' }, '5T': { technique: '5', alignment: 'outside_eye' },
    '7T': { technique: '7', alignment: 'inside_eye' }, '9T': { technique: '9', alignment: 'wide' },
    EDGE: { technique: '9', alignment: 'wide' }, APEX: { alignment: 'wide' },
  };
  const match = byRole[role];
  return match ? { defensive_technique: match.technique, defensive_alignment: match.alignment, alignment_key: slot.role } : {};
}

export interface DefensiveAlignmentIssue {
  code: 'DUPLICATE_ALIGNMENT_SLOT' | 'TECHNIQUE_MISSING';
  playerIds: string[];
  message: string;
  severity: 'warning' | 'error';
}

/** Explain front alignment defects before they become a confusing field picture. */
export function defensiveAlignmentIssues(design: Pick<PlayDesign, 'unit' | 'players'>): DefensiveAlignmentIssue[] {
  if (design.unit !== 'defense') return [];
  const players = design.players ?? [];
  const issues: DefensiveAlignmentIssue[] = [];
  const bySlot = new Map<string, PlayPlayer[]>();
  for (const player of players) {
    if (!player.alignment_key) continue;
    const group = bySlot.get(player.alignment_key) ?? [];
    group.push(player);
    bySlot.set(player.alignment_key, group);
  }
  for (const [slot, group] of bySlot) {
    if (group.length > 1) issues.push({ code: 'DUPLICATE_ALIGNMENT_SLOT', playerIds: group.map((player) => player.id), message: `Alignment slot ${slot} is assigned to ${group.map((player) => player.position ?? player.id).join(' and ')}.`, severity: 'error' });
  }
  for (const player of players) {
    const position = String(player.position ?? player.role ?? '').toUpperCase();
    const frontPlayer = /^(DE|DT|NT|DL|EDGE|OLB|ILB|LB|MIKE|WILL|SAM|BUCK|JACK)$/.test(position);
    if (frontPlayer && player.alignment_key && (!player.defensive_technique || !player.defensive_alignment)) {
      issues.push({ code: 'TECHNIQUE_MISSING', playerIds: [player.id], message: `${player.position ?? player.id} has a front slot but no complete technique/alignment relationship.`, severity: 'warning' });
    }
  }
  return issues;
}
