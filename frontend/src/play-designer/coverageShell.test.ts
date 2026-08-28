import { describe, expect, it } from 'vitest';
import { coverageShellBoxes } from './coverageShell';

describe('coverage shell geometry', () => {
  it('maps declared zones to spatial boxes and removes duplicates', () => {
    expect(coverageShellBoxes(['deep_left', 'deep_left', 'flat_right'])).toEqual([
      expect.objectContaining({ id: 'deep_left', label: 'Deep left' }),
      expect.objectContaining({ id: 'flat_right', x: 74 }),
    ]);
  });

  it('ignores unknown zones so new server terms do not break rendering', () => {
    expect(coverageShellBoxes(['future_zone', 'robber'])).toEqual([expect.objectContaining({ id: 'robber' })]);
  });
});
