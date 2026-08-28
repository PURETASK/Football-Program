import { describe, expect, it } from 'vitest';

import type { PlayDesign } from '../types';
import { defensiveGapLinks, defensiveGapOwners, gapOwnerPatch } from './defensiveFront';

describe('defensive front ownership', () => {
  it('normalizes a gap ownership selection into canonical assignment fields', () => {
    expect(gapOwnerPatch('left_b')).toEqual({ gap_owner: 'left_b', gap_owner_label: 'Left B gap', gap: 'left_b', fit_gap: 'left_b' });
  });

  it('summarizes owners and detects conflicting duplicate responsibilities', () => {
    const design: PlayDesign = { id: 'FRONT', unit: 'defense', elements: [
      { id: 'A', kind: 'fit', player_id: 'MIKE', gap_owner: 'left_b', responsibility: 'spill' },
      { id: 'B', kind: 'fit', player_id: 'WILL', gap_owner: 'left_b', responsibility: 'box' },
    ] };
    expect(defensiveGapOwners(design).get('left_b')).toEqual({ elementId: 'A', owner: 'MIKE + WILL', conflict: true });
  });

  it('projects every canonical gap into an owned, conflict, or unassigned field link', () => {
    const design: PlayDesign = { id: 'LINKS', unit: 'defense', elements: [{ id: 'FIT', kind: 'fit', player_id: 'MIKE', gap_owner: 'left_a', points: [{ x: 50, y: 20 }, { x: 36, y: 30 }] }] };
    const links = defensiveGapLinks(design);
    expect(links).toHaveLength(12);
    expect(links.find((link) => link.gap === 'left_a')).toEqual(expect.objectContaining({ owner: 'MIKE', elementId: 'FIT', anchor: { x: 36, y: 30 } }));
    expect(links.find((link) => link.gap === 'right_a')).toEqual(expect.objectContaining({ conflict: false, owner: undefined }));
  });
});
