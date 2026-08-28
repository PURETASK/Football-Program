import { describe, expect, it } from 'vitest';

import { DEFENSIVE_PRESETS, defensivePresetPatch } from './defensivePresets';

describe('defensive responsibility presets', () => {
  it('covers the four defensive authoring families', () => {
    expect(new Set(DEFENSIVE_PRESETS.map((preset) => preset.category))).toEqual(new Set(['fit', 'coverage', 'pressure', 'rotation']));
  });

  it('returns a structured, coach-readable TEX stunt patch', () => {
    expect(defensivePresetPatch('tex_stunt')).toEqual(expect.objectContaining({ type: 'TEX', stunt: 'TEX', phase: 'rush', arrow_style: 'stunt', objective: expect.any(String) }));
  });

  it('returns a fresh empty patch for an unknown preset', () => {
    expect(defensivePresetPatch('not-a-real-preset')).toEqual({});
  });
});
