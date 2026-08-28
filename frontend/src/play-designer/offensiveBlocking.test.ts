import { describe, expect, it } from 'vitest';
import { blockingConstructionPatch, offensiveBlockingPatch } from './offensiveBlocking';

describe('offensive blocking primitives', () => {
  it('stores a screen release in the release phase', () => {
    expect(offensiveBlockingPatch({ blocking_primitive: 'screen_release', release_after_ms: 450 })).toEqual({ blocking_primitive: 'screen_release', release_after_ms: 450, phase: 'release' });
  });
  it('stores a combo primitive in the block phase', () => {
    expect(offensiveBlockingPatch({ blocking_primitive: 'combo', block_partner_element_id: 'OL-2' })).toEqual({ blocking_primitive: 'combo', block_partner_element_id: 'OL-2', phase: 'block' });
  });

  it('materializes a target-aware pull path without replacing a coach-drawn path', () => {
    const design = {
      id: 'D1', unit: 'offense' as const,
      players: [{ id: 'OL-1', start: { x: 30, y: 30 } }],
      elements: [{ id: 'DEF-1', kind: 'rush', player_id: 'DL-1', points: [{ x: 50, y: 24 }, { x: 50, y: 30 }] }],
    };
    const starter = blockingConstructionPatch({ id: 'OL-BLOCK', kind: 'block', player_id: 'OL-1' }, design, { blocking_primitive: 'pull', block_target_element_id: 'DEF-1' });
    expect(starter).toMatchObject({ phase: 'block', blocking_path_role: 'pull-to-lead', blocking_geometry: 'target-aware' });
    expect(starter.path).toEqual([{ x: 30, y: 30 }, { x: 45, y: 27 }, { x: 50, y: 24 }]);
    const manual = blockingConstructionPatch({ id: 'OL-BLOCK', kind: 'block', points: [{ x: 30, y: 30 }, { x: 35, y: 25 }] }, design, { blocking_primitive: 'pull', block_target_element_id: 'DEF-1' });
    expect(manual).not.toHaveProperty('points');
    expect(manual).not.toHaveProperty('path');
  });
});
