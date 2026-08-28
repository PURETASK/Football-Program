import { describe, expect, it } from 'vitest';

import { clearDefensiveExchangePairPatch, defensiveExchangeLinks, defensiveExchangePairPatch, exchangePatch, reciprocalExchangePatch } from './defensiveExchanges';
import type { PlayDesign } from '../types';

describe('defensive exchange relationships', () => {
  it('creates a canonical current-side exchange patch', () => {
    expect(exchangePatch('RUSH-2', 'penetrate_loop')).toEqual({ exchange_with: 'RUSH-2', target_element_id: 'RUSH-2', exchange_role: 'penetrate_loop', phase: 'exchange' });
  });

  it('creates the reciprocal role for the linked partner', () => {
    expect(reciprocalExchangePatch('RUSH-1', 'penetrate_loop')).toEqual(expect.objectContaining({ exchange_with: 'RUSH-1', target_element_id: 'RUSH-1', exchange_role: 'loop_penetrate', phase: 'exchange' }));
  });

  it('clears an exchange without leaving a stale role', () => {
    expect(exchangePatch('', 'penetrate_loop')).toEqual({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined });
  });

  it('projects reciprocal exchanges into one deduplicated field link', () => {
    const design: PlayDesign = { id: 'EXCHANGE', unit: 'defense', elements: [
      { id: 'RUSH-1', kind: 'rush', player_id: 'DE', exchange_with: 'DROP-1', exchange_role: 'penetrate_loop', points: [{ x: 35, y: 20 }, { x: 42, y: 28 }] },
      { id: 'DROP-1', kind: 'coverage', player_id: 'LB', exchange_with: 'RUSH-1', exchange_role: 'loop_penetrate', points: [{ x: 48, y: 20 }, { x: 46, y: 29 }] },
    ] };
    expect(defensiveExchangeLinks(design)).toEqual([expect.objectContaining({ fromId: 'DROP-1', toId: 'RUSH-1', label: 'Loop → penetrate', from: { x: 46, y: 29 }, to: { x: 42, y: 28 } })]);
  });

  it('creates both sides of a selected exchange pair with reciprocal roles', () => {
    expect(defensiveExchangePairPatch('RUSH-1', 'DROP-1', 'rush_replace')).toEqual([
      ['RUSH-1', expect.objectContaining({ exchange_with: 'DROP-1', exchange_role: 'rush_replace', phase: 'exchange' })],
      ['DROP-1', expect.objectContaining({ exchange_with: 'RUSH-1', exchange_role: 'drop_replace', phase: 'exchange' })],
    ]);
  });

  it('persists vacated and replacement responsibility context on the appropriate sides', () => {
    expect(defensiveExchangePairPatch('RUSH-1', 'DROP-1', 'rush_replace', { vacated_zone: 'left_b', replacement_zone: 'flat_left' })).toEqual([
      ['RUSH-1', expect.objectContaining({ responsibility: 'Vacate left_b' })],
      ['DROP-1', expect.objectContaining({ rotation_to_zone: 'flat_left', zone: 'flat_left', responsibility: 'Replace flat_left' })],
    ]);
  });

  it('clears both reciprocal links without leaving exchange metadata behind', () => {
    expect(clearDefensiveExchangePairPatch('RUSH-1', 'DROP-1')).toEqual([
      ['RUSH-1', expect.objectContaining({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined })],
      ['DROP-1', expect.objectContaining({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined })],
    ]);
  });
});
