import type { PlayPlayer } from '../types';

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
