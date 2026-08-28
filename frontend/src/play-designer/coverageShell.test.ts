import { describe, expect, it } from 'vitest';
import { coverageMovementPatch, coverageShellAnchor, coverageShellBoxes, coverageShellLinks, coverageShellOwners } from './coverageShell';

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

  it('materializes a shell-targeted drop path when the assignment has no path', () => {
    const design = { id: 'SHELL', unit: 'defense' as const, players: [{ id: 'CB-L', start: { x: 15, y: 30 } }] };
    const patch = coverageMovementPatch({ id: 'DROP', kind: 'coverage', player_id: 'CB-L' }, design, 'flat_left');
    expect(coverageShellAnchor('flat_left')).toEqual({ x: 13.5, y: 21.5 });
    expect(patch).toMatchObject({ zone: 'flat_left', phase: 'coverage', movement_geometry: 'shell-targeted' });
    expect(patch.path).toEqual([{ x: 15, y: 30 }, { x: 14.25, y: 25.75 }, { x: 13.5, y: 21.5 }]);
  });

  it('does not overwrite an existing coach-drawn coverage path', () => {
    const design = { id: 'SHELL', unit: 'defense' as const };
    const element = { id: 'DROP', kind: 'coverage', points: [{ x: 15, y: 30 }, { x: 20, y: 20 }] };
    const patch = coverageMovementPatch(element, design, 'flat_left');
    expect(patch).not.toHaveProperty('points');
    expect(patch.movement_geometry).toBe('shell-targeted');
  });

  it('collects all visual shell owners for conflict-aware rendering', () => {
    const owners = coverageShellOwners({ elements: [
      { id: 'DROP-1', kind: 'coverage', player_id: 'FS', zone: 'deep_middle' },
      { id: 'DROP-2', kind: 'rotation', player_id: 'MIKE', rotation_to_zone: 'deep_middle' },
    ] });
    expect(owners.get('deep_middle')).toEqual(['FS', 'MIKE']);
  });

  it('marks each movement vector when a shell zone has multiple owners', () => {
    const links = coverageShellLinks({ id: 'CONFLICT-SHELL', unit: 'defense', elements: [
      { id: 'DROP-1', kind: 'coverage', player_id: 'FS', zone: 'deep_middle', points: [{ x: 50, y: 30 }, { x: 50, y: 8 }] },
      { id: 'ROTATE-1', kind: 'rotation', player_id: 'MIKE', rotation_to_zone: 'deep_middle', points: [{ x: 40, y: 30 }, { x: 50, y: 8 }] },
    ] });
    expect(links).toHaveLength(2);
    expect(links.every((link) => link.conflict)).toBe(true);
  });
});
