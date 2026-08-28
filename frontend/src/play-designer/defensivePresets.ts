import type { PlayElement } from '../types';

export interface DefensivePreset {
  value: string;
  label: string;
  category: 'fit' | 'coverage' | 'pressure' | 'rotation';
  description: string;
  patch: Partial<PlayElement>;
}

/**
 * Coach-facing defensive responsibility starters. These are authoring aids,
 * not legality decisions: the server validator still owns rule enforcement.
 * Keeping the vocabulary here makes the assignment graph readable and gives
 * the canvas enough semantic data to render, validate, and teach a call.
 */
export const DEFENSIVE_PRESETS: DefensivePreset[] = [
  {
    value: 'spill_fit',
    label: 'Spill fit',
    category: 'fit',
    description: 'Attack the declared surface and spill the ball to pursuit.',
    patch: { type: 'spill', fit_gap: 'B-gap / spill', fit_rule: 'spill', objective: 'Spill the ball to pursuit', responsibility: 'Spill force defender', phase: 'fit', arrow_style: 'fit', leverage: 'outside' },
  },
  {
    value: 'box_fit',
    label: 'Box fit',
    category: 'fit',
    description: 'Slow the entry, keep leverage, and box the ball inside.',
    patch: { type: 'box', fit_gap: 'Inside box', fit_rule: 'box', objective: 'Keep the ball inside and fit clean', responsibility: 'Box / spill support', phase: 'fit', arrow_style: 'fit', leverage: 'inside' },
  },
  {
    value: 'force_edge',
    label: 'Force edge',
    category: 'fit',
    description: 'Set the edge and force the ball back to the pursuit.',
    patch: { type: 'force', fit_gap: 'C-gap / force', fit_rule: 'force', objective: 'Force the ball back inside', responsibility: 'Force / contain', phase: 'fit', arrow_style: 'fit', leverage: 'outside' },
  },
  {
    value: 'cutback_fit',
    label: 'Cutback / weak fit',
    category: 'fit',
    description: 'Own the cutback lane and close behind the front.',
    patch: { type: 'cutback', fit_gap: 'Cutback / backside A', fit_rule: 'cutback', objective: 'Eliminate the cutback', responsibility: 'Backside cutback fit', phase: 'fit', arrow_style: 'fit', leverage: 'inside' },
  },
  {
    value: 'deep_third',
    label: 'Cover 3 deep third',
    category: 'coverage',
    description: 'Carry vertical threats and midpoint the assigned deep third.',
    patch: { type: 'deep_third', coverage: 'cover_3', zone: 'deep_third', objective: 'Protect the deep third', responsibility: 'Deep third player', phase: 'coverage', arrow_style: 'coverage', leverage: 'top_down' },
  },
  {
    value: 'quarter_match',
    label: 'Quarter match',
    category: 'coverage',
    description: 'Read the release and match vertical threats in the quarter.',
    patch: { type: 'quarter_match', coverage: 'quarters', zone: 'quarter_match', objective: 'Match vertical threats in the quarter', responsibility: 'Quarter match player', phase: 'coverage', arrow_style: 'coverage', leverage: 'top_down' },
  },
  {
    value: 'hook_curl',
    label: 'Hook / curl drop',
    category: 'coverage',
    description: 'Expand under the first threat and close the passing window.',
    patch: { type: 'hook_curl', coverage: 'zone', zone: 'hook_curl', objective: 'Close the hook-curl window', responsibility: 'Hook / curl dropper', phase: 'coverage', arrow_style: 'coverage', leverage: 'inside' },
  },
  {
    value: 'robber',
    label: 'Robber rotation',
    category: 'coverage',
    description: 'Rotate into the low-hole window and rob the quarterback’s read.',
    patch: { type: 'robber', coverage: 'robber', zone: 'robber', rotation: 'low_hole', objective: 'Rob the inside crossing window', responsibility: 'Low-hole robber', phase: 'rotation', arrow_style: 'rotation', leverage: 'inside' },
  },
  {
    value: 'man_trail',
    label: 'Man trail',
    category: 'coverage',
    description: 'Play with inside leverage and trail the assigned man.',
    patch: { type: 'man_trail', coverage: 'man', zone: 'man', objective: 'Stay on the assigned man', responsibility: 'Man-to-man trail', phase: 'coverage', arrow_style: 'coverage', leverage: 'trail' },
  },
  {
    value: 'bracket',
    label: 'Bracket / double',
    category: 'coverage',
    description: 'Declare the inside or outside half of a two-player bracket.',
    patch: { type: 'bracket', coverage: 'bracket', zone: 'bracket', objective: 'Deny the featured target', responsibility: 'Bracket leverage player', phase: 'coverage', arrow_style: 'coverage', leverage: 'inside' },
  },
  {
    value: 'edge_rush',
    label: 'Edge rush / contain',
    category: 'pressure',
    description: 'Rush the edge without losing quarterback or boot contain.',
    patch: { type: 'edge_rush', rush_lane: 'C-gap / edge', objective: 'Collapse the edge and keep contain', responsibility: 'Edge rusher / contain', phase: 'rush', arrow_style: 'rush', technique: 'Speed to power', leverage: 'outside' },
  },
  {
    value: 'a_gap_blitz',
    label: 'A-gap pressure',
    category: 'pressure',
    description: 'Insert through the declared A gap on the pressure path.',
    patch: { type: 'a_gap_blitz', rush_lane: 'A-gap', blitz_path: 'A-gap insert', objective: 'Stress the interior protection', responsibility: 'A-gap blitzer', phase: 'blitz', arrow_style: 'rush', technique: 'Cross the center face', leverage: 'inside' },
  },
  {
    value: 'tex_stunt',
    label: 'TEX stunt',
    category: 'pressure',
    description: 'Tackle penetrates; end loops inside to exchange the rush lane.',
    patch: { type: 'TEX', rush_lane: 'Interior exchange', stunt: 'TEX', objective: 'Force a protection exchange', responsibility: 'Tackle penetrator / end looper', phase: 'rush', arrow_style: 'stunt', technique: 'Penetrate then loop', leverage: 'inside' },
  },
  {
    value: 'et_stunt',
    label: 'ET stunt',
    category: 'pressure',
    description: 'End penetrates; tackle loops outside into the vacated lane.',
    patch: { type: 'ET', rush_lane: 'Edge exchange', stunt: 'ET', objective: 'Create a two-man rush surface', responsibility: 'End penetrator / tackle looper', phase: 'rush', arrow_style: 'stunt', technique: 'Penetrate then loop', leverage: 'outside' },
  },
  {
    value: 'sky_rotation',
    label: 'Sky rotation',
    category: 'rotation',
    description: 'Rotate the safety down into the flat and replace the shell.',
    patch: { type: 'sky', coverage: 'cover_3', zone: 'flat', rotation: 'sky', objective: 'Replace the rolled-down safety', responsibility: 'Sky rotation / flat player', phase: 'rotation', arrow_style: 'rotation', leverage: 'outside' },
  },
  {
    value: 'spin_rotation',
    label: 'Spin rotation',
    category: 'rotation',
    description: 'Spin the post safety and declare the replacing deep-half responsibility.',
    patch: { type: 'spin', coverage: 'cover_3', zone: 'deep_half', rotation: 'spin', objective: 'Replace the rotating post safety', responsibility: 'Spin rotation player', phase: 'rotation', arrow_style: 'rotation', leverage: 'top_down' },
  },
];

export function defensivePresetPatch(value: string): Partial<PlayElement> {
  const preset = DEFENSIVE_PRESETS.find((item) => item.value === value);
  return preset ? { ...preset.patch } : {};
}

