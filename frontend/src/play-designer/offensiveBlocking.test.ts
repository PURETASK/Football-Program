import { describe, expect, it } from 'vitest';
import { offensiveBlockingPatch } from './offensiveBlocking';

describe('offensive blocking primitives', () => {
  it('stores a screen release in the release phase', () => {
    expect(offensiveBlockingPatch({ blocking_primitive: 'screen_release', release_after_ms: 450 })).toEqual({ blocking_primitive: 'screen_release', release_after_ms: 450, phase: 'release' });
  });
  it('stores a combo primitive in the block phase', () => {
    expect(offensiveBlockingPatch({ blocking_primitive: 'combo', block_partner_element_id: 'OL-2' })).toEqual({ blocking_primitive: 'combo', block_partner_element_id: 'OL-2', phase: 'block' });
  });
});
