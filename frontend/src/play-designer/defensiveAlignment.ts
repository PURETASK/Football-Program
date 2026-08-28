import type { PlayAlignmentSlot, PlayPlayer } from '../types';

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
